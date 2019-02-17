

import time, os, logging
import DLProcessor
from packer import Packer

logger = logging.getLogger('nbdler')


class TimeStatus(Packer, object):
    def __init__(self):
        self.go_startTime = None
        self.go_pauseTime = None
        self.go_lastTime = 0
        self.go_end = False

        self.pauseflag = False
        self.endflag = False

        self.done_startTime = None
        self.done_pauseTime = None
        self.done_lastTime = 0
        self.done_end = False

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'go_end' or key == 'done_end':
            self.endflag = self.go_end and self.done_end


    def startGo(self):
        self.pauseflag = False
        if not self.go_startTime and not self.go_end:
            self.go_startTime = time.clock()
            self.go_pauseTime = None

    def endGo(self):
        if self.go_startTime:
            self.pause()
        self.go_end = True

    def pause(self):
        self.pauseflag = True
        if self.go_startTime:
            self.go_pauseTime = time.clock()
            self.go_lastTime += self.go_pauseTime - self.go_startTime
            self.go_startTime = None

        if self.done_startTime:
            self.done_pauseTime = time.clock()
            self.done_lastTime += self.done_pauseTime - self.done_startTime
            self.done_startTime = None

    def startDone(self):
        if not self.done_startTime and not self.done_end:
            self.done_pauseTime = None
            self.done_startTime = time.clock()

    def endDone(self):
        if self.done_startTime:
            self.done_pauseTime = time.clock()
            self.done_lastTime += self.done_pauseTime - self.done_startTime

            self.done_startTime = None
        self.done_end = True

    def clear(self):
        self.go_startTime = None
        self.go_pauseTime = None
        self.go_lastTime = 0
        self.go_end = False

        self.done_startTime = None
        self.done_pauseTime = None
        self.done_lastTime = 0
        self.done_end = False

    def getGoDuration(self):
        return self.go_lastTime + (time.clock() - self.go_startTime) if self.go_startTime else self.go_lastTime

    def getDoneDuration(self):
        return self.done_lastTime + (time.clock() - self.done_startTime) if self.done_startTime else self.done_lastTime

    def __packet_params__(self):
        return ['go_lastTime', 'done_lastTime']




class Progress(Packer, object):
    def __init__(self, GlobalProgress, Urlid, begin, end):

        self.globalprog = GlobalProgress

        self.begin = begin
        self.end = end
        self.length = end - begin

        self.go_inc = 0
        self.done_inc = 0

        self.status = TimeStatus()

        self.processor = DLProcessor.Processor(self, Urlid)
        self.urlid = Urlid


    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)

        if key == 'urlid':
            self.processor.urlid = self.urlid
        elif key == 'begin' or key == 'end':
            self.length = getattr(self, 'end', 0) - getattr(self, 'begin', 0)
        elif key == 'go_inc':
            if getattr(self, 'status', None):
                if self.go_inc > self.length:
                    raise Exception('ProgressGoExceed')
                elif self.go_inc == self.length:
                        self.endGo()
                else:
                    self.status.go_end = False
        elif key == 'done_inc':
            if getattr(self, 'status', None):
                if self.done_inc > self.length:
                    raise Exception('ProgressDoneExceed')
                elif self.done_inc == self.length:
                    self.endDone()
                else:
                    self.status.done_end = False
        elif key == 'length':
            if self.length:

                if getattr(self, 'go_inc', 0) == self.length:
                    self.endGo()
                elif getattr(self, 'done_inc', 0) == self.length:
                    self.endDone()

    def isGoEnd(self):
        return self.status.go_end

    def isEnd(self):
        return self.status.endflag

    def isPause(self):
        return self.status.pauseflag

    def isReady(self):
        return not self.status.go_end and not self.status.pauseflag


    def getAvgSpeed(self):
        duration = self.status.getGoDuration()
        return self.go_inc * 1.0 / duration if duration > 0 else 0

    def setNewRange(self, Range):
        self.begin = Range[0]
        self.end = Range[1]

    def getLeft(self):
        return self.length - self.go_inc


    def run(self):
        self.status.startGo()
        self.processor.run()

    def go(self, bytelen):
        self.go_inc += bytelen

        pos = int((self.begin + self.go_inc - bytelen) * 1.0 / self.globalprog.handler.file.BLOCK_SIZE)
        fil_len = int(math.ceil(bytelen * 1.0 / self.globalprog.handler.file.BLOCK_SIZE))
        for i in range(fil_len):
            self.globalprog.block_map[pos + i] = self.urlid


    def done(self, bytelen):
        self.done_inc += bytelen


    def endDone(self):
        self.status.endDone()

    def endGo(self):
        self.status.endGo()

    def __packet_params__(self):
        return ['status', 'begin', 'end', 'done_inc', 'go_inc', 'urlid']

    def clear(self):
        self.go_inc = 0
        self.done_inc = 0
        self.status = TimeStatus()
        self.processor.buff = ''

    def unpack(self, packet):
        Packer.unpack(self, packet)

        self.go_inc = self.done_inc

class Piece(object):
    def __init__(self):
        self.last_left = None
        self.last_clock = None

        self.start_clock = None
        self.last_time = 0

    def start(self):
        if not self.last_clock:
            self.start_clock = time.clock()

    def pause(self):
        if self.last_clock:
            self.last_time += time.clock() - self.start_clock
            self.start_clock = None
            self.last_clock = None


MANUAL = 0
AUTO = 1

import threading, math, zlib
import DLInspector, DLAllotter




class GlobalProgress(Packer, object):
    def __init__(self, Handler, mode=AUTO):

        self.progresses = {}

        self.handler = Handler

        self.block_map = None

        self.piece = Piece()
        self.status = TimeStatus()

        self.allotter = DLAllotter.Allotter(Handler, self)
        self.inspector = DLInspector.Inspector(Handler, self, self.allotter)

        self.__packet_frame__ = {}

        self.__buff_lock__ = threading.Lock()
        self.__buff_counter__ = 0
        self.__progresses_lock__ = threading.Lock()
        self.__release_thread__ = None
        self.__insspeed_lock__ = threading.Lock()

        self.pause_req = False

        self.__mode__ = mode

    def insert(self, Urlid, begin, end):
        with self.__progresses_lock__:
            if not self.block_map:
                self.makeMap()

            for i in self.progresses.values():
                if begin > i.begin and begin < i.end:
                    raise Exception('ProgressOverlap')

            prog = Progress(self, Urlid, begin, end)
            block_index = int(prog.begin * 1.0 / self.handler.file.BLOCK_SIZE)
            self.block_map[block_index] = Urlid
            self.progresses['%d-%d' % (begin, end)] = prog

        return prog

    def run(self):
        if not self.block_map:
            self.makeMap()
        for i, j in self.progresses.items():
            j.run()

        self.piece.start()
        self.status.startGo()
        if self.__mode__ == AUTO:
            self.inspector.runAllotter()
        # if self.handler.url.max_speed != -1:
        #     self.inspector.runLimiter()
        self.inspector.runSelfCheck()


    def checkAllGoEnd(self):

        for i in self.progresses.values():
            if not i.status.go_end:
                break
        else:
            self.status.endGo()
            self.close()

    def makePause(self):
        for i, j in self.progresses.items():
            with j.processor.__opa_lock__:
                if not j.status.go_end and not j.status.pauseflag:
                    j.processor.pause()

    def isAllPause(self):
        self.makePause()
        for i in self.progresses.values():
            if not i.isPause() and not i.isGoEnd():
                break
        else:
            if not self.allotter.__allotter_lock__.locked():
                return True

        return False

    def pause(self):

        self.pause_req = True

        while True:
            if self.isAllPause():
                break
            if self.isEnd():
                break
            time.sleep(0.1)

        self.piece.pause()
        self.status.pause()

        self.releaseBuffer()

        self.save()

        self.pause_req = False


    def getMap(self):
        return self.block_map

    def setMap(self, map):
        self.block_map = map

    def getConnections(self):
        connections = []
        with self.__progresses_lock__:
            for i in self.progresses.values():
                if not i.status.go_end:
                    connections.append(i)

        return connections

    def getOnlines(self):
        onlines = []
        with self.__progresses_lock__:
            for i in self.progresses.values():
                if i.processor.isRunning():
                    onlines.append(i)

        return onlines

    def fix(self, segs):
        for i in segs:
            self.progresses[i].clear()

        self.run()

    def isEnd(self):

        return self.status.endflag and not self.__buff_lock__.locked()

    def isGoEnd(self):
        return self.status.go_end

    def getLeft(self):
        gobyte = 0
        with self.__progresses_lock__:
            for i in self.progresses.values():
                gobyte += i.go_inc

        return self.handler.file.size - gobyte

    def getAvgSpeed(self):
        if self.status.go_startTime is not None and not self.status.endflag:
            totaltime = time.clock() - self.status.go_startTime
        else:
            totaltime = 0

        totaltime += self.status.go_lastTime

        return (self.handler.file.size - self.getLeft()) * 1.0 / totaltime


    def getInsSpeed(self, update=True):
        with self.__insspeed_lock__:

            curleft = self.getLeft()
            curclock = time.clock()

            if self.piece.last_left is None:
                self.piece.last_left = curleft
            if self.piece.last_clock is None:
                if self.piece.start_clock:
                    self.piece.last_clock = self.piece.start_clock
                else:
                    self.piece.last_clock = curclock

            incbyte = self.piece.last_left - curleft
            incclock = curclock - self.piece.last_clock

            # if incbyte < 0:
            #     pass

            if update:
                self.piece.last_left = curleft
                self.piece.last_clock = curclock

        return incbyte * 1.0 / incclock if incclock else 0

    def close(self):
        self.releaseBuffer()
        self.status.endDone()

        self.status.endflag = True

    def makeMap(self):
        self.block_map = [None for i in range(int(
            math.ceil(self.handler.file.size*1.0 / self.handler.file.BLOCK_SIZE)))]


    def releaseBuffer(self):
        # if self.__buff_lock__.locked():
        #     return
        with self.__buff_lock__:
            buffqueue = []

            for i in self.progresses.values():
                if i.processor.buff:
                    buffqueue.append(i)

            if not buffqueue:
                return
            msg = 'ReleaseBuffer: +++++++++++'
            extra = {'progress': '%010s-%010s' % ('..........', '..........'), 'urlid': '.'}
            logger.info(msg, extra=extra)
            msg = 'ReleaseBuffer: BUFF_SIZE = %d' % self.__buff_counter__
            extra = {'progress': '..........-..........', 'urlid': '.'}
            logger.info(msg, extra=extra)

            f = self.handler.file.fp if self.__mode__ == MANUAL else \
                open(os.path.join(self.handler.file.path, self.handler.file.name), 'rb+')
            with f:
                for progress in buffqueue:
                    with progress.processor.__buff__lock__:
                        f.seek(progress.begin + progress.done_inc)
                        f.write(progress.processor.buff)
                        progress.done(len(progress.processor.buff))
                        progress.processor.buff = b''
                f.flush()
            # f.close()

            self.save()
            self.__buff_counter__ = 0
            self.__release_thread__ = None
            msg = 'ReleaseBuffer: -----------'
            extra = {'progress': '%010s-%010s' % ('..........', '..........'), 'urlid': '.'}
            logger.info(msg, extra=extra)


    def checkBuffer(self, bytelen):
        self.__buff_counter__ += bytelen

        if self.__buff_counter__ >= self.handler.file.buffer_size:
            if not self.__release_thread__:
                self.__release_thread__ = threading.Thread(target=self.releaseBuffer, name='ReleaseBuffer')
                self.__release_thread__.start()

    def save(self):
        if not self.__packet_frame__:
            self.__packet_frame__ = self.handler.pack()
        self.__packet_frame__['__auto_global__'] = self.pack()

        packet = zlib.compress(str.encode(str(self.__packet_frame__)), zlib.Z_BEST_COMPRESSION)

        with open(os.path.join(self.handler.file.path, self.handler.file.name + '.nbdler'), 'wb') as f:
            f.write(packet)
            f.flush()
        pass

    def askWait(self, msec):
        for i in self.progresses.values():
            if not i.status.go_end:
                i.processor.opareq.wait = msec

    def askCut(self, Range):
        if Range:
            progress = None
            odd = [None, None]
            for i in self.progresses.values():
                if i.end == Range[1]:
                    progress = i
                    break
                elif i.begin == Range[1]:
                    odd[1] = i
                elif i.end == Range[0]:
                    odd[0] = i

            if not progress and odd[0] and odd[1]:
                msg = 'OddRanges: %010d-%010d' % (Range[0], Range[1])
                extra = {'progress': '%010s-%010s' % ('.'*10, '.'*10), 'urlid': '.'}
                logger.warning(msg, extra=extra)

                return Range

            return progress.processor.cutRequest(Range)
        else:
            return []

    def cut(self, Progress, Range):
        with self.__progresses_lock__:
            self.progresses['%d-%d' % (Progress.begin, Range[0])] = Progress
            del self.progresses['%d-%d' % (Progress.begin, Progress.end)]
            Progress.setNewRange([Progress.begin, Range[0]])

    def __packet_params__(self):
        return ['status', 'progresses']

    def pack(self):
        with self.__progresses_lock__:
            return Packer.pack(self)


    def unpack(self, packet):
        Packer.unpack(self, packet)

        for i, j in self.progresses.items():
            prog = Progress(self, -1, -1, -1)
            prog.unpack(j)
            self.progresses[i] = prog

        self.makeMap()

        for progress in self.progresses.values():
            pos = int(progress.begin * 1.0 / self.handler.file.BLOCK_SIZE)
            fil_len = int(math.ceil(progress.go_inc * 1.0 / self.handler.file.BLOCK_SIZE))
            self.block_map[pos] = progress.urlid
            for i in range(fil_len):
                self.block_map[pos + i] = progress.urlid

        self.status.endflag = self.status.go_end = self.status.done_end = self.isEnd()

    def __del__(self):
        self.releaseBuffer()
        if self.__mode__ == AUTO:
            if not self.isEnd():
                self.save()




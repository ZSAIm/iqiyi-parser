

import time, os
from . import DLProcessor
from .packer import Packer
import gc
import traceback
from . import DLCommon as cv


class TimeStatus(Packer, object):
    def __init__(self):
        self.go_startTime = None
        self.go_endtime = None

        self.go_lastTime = 0
        self.go_end = False

        self.pauseflag = False
        self.endflag = False

        self.done_startTime = None
        self.done_end = False

        self.pause_req = False


    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'go_end' or key == 'done_end':
            self.endflag = self.go_end and self.done_end


    def startGo(self):
        self.go_startTime = time.time()
        self.pauseflag = False


    def endGo(self):
        self.go_endtime = time.time()
        self.go_end = True

    def isGoEnd(self):
        return self.go_end

    def isEnd(self):
        return self.endflag

    def isDoneEnd(self):
        return self.done_end

    def isStarted(self):
        return self.go_startTime and not self.pauseflag

    def startPause(self):
        self.pause_req = True

    def endPause(self):
        self.pauseflag = True
        self.pause_req = False

        self.go_lastTime += time.time() - self.go_startTime if self.go_startTime else 0

    def pausing(self):
        return self.pause_req

    def isPaused(self):
        return self.pauseflag


    def endDone(self):

        self.done_end = True

    def clear(self):
        self.go_startTime = None
        self.go_end = False

        self.done_startTime = None
        self.done_end = False

    def getGoDur(self):
        return (time.time() - self.go_startTime) if self.go_startTime else 0

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
                # if self.go_inc > self.length:
                #     raise Exception('ProgressGoExceed')
                if self.go_inc > self.length:
                    self.go_inc = self.length
                if self.go_inc == self.length:
                    self.endGo()
                else:
                    self.status.go_end = False
        elif key == 'done_inc':
            if getattr(self, 'status', None):
                if self.done_inc > self.length:
                    self.done_inc = self.length
                    # raise Exception('ProgressDoneExceed')
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
        duration = self.status.getGoDur()
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

    def __repr__(self):
        return 'EndFlag=%s, PauseFlag=%s, Length=%s, Go_inc=%s, Range=(%s-%s)' % (
            self.status.endflag, self.status.pauseflag, self.length, self.go_inc, self.begin, self.end)



class Piece(object):
    def __init__(self):
        self.last_left = None
        self.last_clock = None

        self.start_clock = None
        self.last_time = 0

    def start(self):
        if not self.last_clock:
            self.start_clock = time.time()

    def pause(self):
        if self.last_clock:
            self.last_time += time.time() - self.start_clock if self.start_clock else 0
            self.start_clock = None
            self.last_clock = None


MANUAL = 0
AUTO = 1

import threading, math, zlib
from . import DLInspector, DLAllotter

from .DLInfos import FileStorage


class GlobalProgress(Packer, object):
    def __init__(self, Handler, mode=AUTO):

        self.progresses = {}

        self.handler = Handler

        self.block_map = None

        self.piece = Piece()
        self.status = TimeStatus()

        self.fs = FileStorage()

        self.allotter = DLAllotter.Allotter(Handler, self)
        self.inspector = DLInspector.Inspector(Handler, self, self.allotter)

        self.__packet_frame__ = {}

        self._buff_counter = 0

        self._release_signal = threading.Event()

        self._prog_lock__ = threading.Lock()
        # self.__release_thread__ = None

        self.__mode__ = mode

        self._url_excepts = []

        self._threads = self.handler.threads
        # self.pool


    def Thread(self, *args, **kwargs):
        return self._threads.Thread(*args, **kwargs)


    def insert(self, Urlid, begin, end):
        with self._prog_lock__:
            if not self.block_map:
                self.makeMap()

            for i in list(self.progresses.values()):
                if begin > i.begin and begin < i.end:
                    raise Exception('ProgressOverlap')

            prog = Progress(self, Urlid, begin, end)
            block_index = int(prog.begin * 1.0 / self.handler.file.BLOCK_SIZE)
            self.block_map[block_index] = Urlid
            self.progresses['%d-%d' % (begin, end)] = prog

        return prog

    def run(self):
        """export: run()"""
        if not self.block_map:
            self.makeMap()

        self.piece.start()
        self.status.startGo()
        for i, j in self.progresses.items():
            j.run()

        if self.__mode__ == AUTO:
            self.inspector.runAllotter()
        # if self.handler.url.max_speed != -1:
        #     self.inspector.runLimiter()
        self.inspector.runInspector()
        self._run_releaser()

    def _run_releaser(self):
        rel = self._threads.get(cv.RELEASE_BUFF)
        if not rel or rel.isStoped():
            self.Thread(target=self.releaseBuffer, name=cv.RELEASE_BUFF).start()


    def ckeckAllGoEnd(self):
        """export: checkAllGoEnd()"""
        # with self.__buff_lock__:
        if self._prog_lock__:
            if not self._is_end():
                if self._is_go_end():
                    if self.__mode__ == AUTO:
                        miss = self.checkCompleteness()
                        if miss:

                            for i in miss:
                                urlid = self.allotter.assignUrlid()
                                if urlid != -1:
                                    prog = self.insert(urlid, *i)
                                    prog.run()
                            return False
                    self.status.endGo()
                    self.close()
                    return True
            else:
                return True


    def trap(self):
        """export: trap()"""
        while not self._threads.isAllDead():
            if self._url_excepts:
                exc = self._url_excepts.pop()
                raise exc

            time.sleep(0.01)

        if self._url_excepts:
            exc = self._url_excepts.pop()
            raise exc

    def join(self):
        """export: join()"""
        while not self._threads.isAllDead():
            time.sleep(0.01)

    def raiseUrlError(self, url_except):
        self._url_excepts.append(url_except)


    def _is_go_end(self):
        if not self.progresses:
            return False
        for i in self.progresses.values():
            if not i.status.go_end:
                return False
        else:

            return True

    def isGoEnd(self):
        """export: isGoEnd()"""
        with self._prog_lock__:
            return self._is_go_end()


    def _is_critical(self):
        if self._is_go_end():
            return False
        critical = False
        for i in list(self.progresses.values()):
            if not i.isEnd() and i.processor.critical:
                critical = True
                # return False
        # else:
            # if self._threads.getAll(cv.ADDNODE):

                # return False
            # if self._threads.getAll(cv.LAUNCHER):
            #     return False
            # return True
        return critical

    def isCritical(self):
        """export: isCritical()"""
        with self._prog_lock__:
            return self._is_critical()


    def pause(self):
        """export: pause()"""

        if self.status.isEnd():
            return
        self.status.startPause()

        for i in self._threads.getAll(cv.ADDNODE):
            i.join()

        for i in self._threads.getAll(cv.LAUNCHER):
            i.join()

        for i in self._threads.getAll(cv.INSPECTOR):
            i.join()

        for i in self._threads.getAll(cv.ALLOTTER):
            i.join()

        for i, j in self.progresses.items():
            with j.processor.__opa_lock__:
                if not j.status.isGoEnd() and not j.status.pauseflag:
                    if j.processor.isRunning():
                        j.processor.pause()

        for i in self._threads.getAll(cv.PROCESSOR):
            i.join()

        self.piece.pause()
        if self.handler.file.size != -1:
            self.save()
        self.status.endPause()
        # self.pause_req = False

    shutdown = pause


    def getMap(self):
        return self.block_map

    def setMap(self, map):
        self.block_map = map


    def getConnections(self):
        """export: getConnections()"""
        connections = []
        # with self.__progresses_lock__:
        for i in list(self.progresses.values()):
            if not i.status.isGoEnd():
                connections.append(i)

        return connections

    def getOnlines(self):
        """export: getOnline()"""
        onlines = []
        # with self.__progresses_lock__:
        for i in list(self.progresses.values()):
            if i.processor.isRunning():
                onlines.append(i)

        return onlines

    # def fix(self, segs):
    #     for i in segs:
    #         self.progresses[i].clear()
    #
    #     self.run()


    def _is_end(self):
        """export: isEnd()"""
        return self.status.isEnd()

    isEnd = _is_end

    def getLeft(self):
        gobyte = 0
        # with self.__progresses_lock__:
        for i in list(self.progresses.values()):
            gobyte += i.go_inc

        return self.handler.file.size - gobyte if self.handler.file.size != -1 else 0

    def getAvgSpeed(self):
        if self.status.isGoEnd():
            totaltime = self.status.go_endtime - self.status.go_startTime
        elif not self.status.go_startTime:
            totaltime = 0
        else:
            totaltime = time.time() - self.status.go_startTime

        totaltime += self.status.go_lastTime

        return (self.handler.file.size - self.getLeft()) * 1.0 / totaltime if totaltime else 0


    def getInsSpeed(self):


        curleft = self.getLeft()
        curclock = time.time()

        if self.piece.last_left is None:
            self.piece.last_left = curleft
        if self.piece.last_clock is None:
            if self.piece.start_clock:
                self.piece.last_clock = self.piece.start_clock
            else:
                self.piece.last_clock = curclock

        incbyte = self.piece.last_left - curleft
        incclock = curclock - self.piece.last_clock


        if incclock >= 1:
            self.piece.last_left = curleft + incbyte / 2.0
            self.piece.last_clock = curclock - incclock / 2.0

        if self.isEnd() and curleft == 0:
            if incbyte > 0 and incclock > 0:
                return incbyte * 1.0 / incclock
            else:
                return 0


        if incclock > 0 and incbyte > 0:
            ins_speed = incbyte * 1.0 / incclock
        else:
            ins_speed = 0

        return ins_speed

    def close(self):
        self._release_signal.set()
        self.status.endDone()

    def makeMap(self):
        self.block_map = [None for i in range(int(
            math.ceil(self.handler.file.size*1.0 / self.handler.file.BLOCK_SIZE)))]


    def checkCompleteness(self):
        with self._prog_lock__:
            _ranges = [i.split('-') for i in self.progresses.keys()]
            _ranges = sorted(_ranges, key=lambda x: int(x[0]))

            miss = []
            for i in range(len(_ranges)-1):
                if _ranges[i][1] != _ranges[i+1][0]:
                    miss.append((int(_ranges[i][1]), int(_ranges[i+1][0])))

            if int(_ranges[-1][1]) != self.handler.file.size:
                miss.append((int(_ranges[-1][1]), self.handler.file.size))

            return miss



    def releaseBuffer(self):

        try:
            f = self.fs if self.__mode__ == MANUAL else \
                open(os.path.join(self.handler.file.path, self.handler.file.name), 'rb+')
        except Exception as e:
            traceback.print_exc()
            threading.Thread(target=self.shutdown).start()
            return

        with f:
            while True:
                if self.status.isEnd() or self.status.isPaused():
                    break
                if self.isCritical():
                    self.join()
                    break
                self._release_signal.wait(1)
                self._release_signal.clear()
                self._release(f)

            self._release(f)

    def _release(self, f):
        buffqueue = []
        for i in self.progresses.values():
            if i.processor.buff:
                buffqueue.append(i.processor)
        buffqueue = sorted(buffqueue, key=lambda x: x.progress.begin)
        if buffqueue:

            for processor in buffqueue:
                processor.releaseBuffer(f)
            f.flush()
            gc.collect()
        self.save()


    def checkBuffer(self, bytelen):
        self._buff_counter += bytelen
        if self._buff_counter >= self.handler.file.buffer_size:
            self._buff_counter = 0
            self._release_signal.set()


    def save(self):
        if not self.__packet_frame__:
            self.__packet_frame__ = self.handler.pack()
        self.__packet_frame__['__globalprog__'] = self.pack()

        packet = zlib.compress(str.encode(str(self.__packet_frame__)), zlib.Z_BEST_COMPRESSION)

        with open(os.path.join(self.handler.file.path, self.handler.file.name + '.nbdler'), 'wb') as f:
            f.write(packet)
            f.flush()


    def askWait(self, msec):
        for i in self.progresses.values():
            if not i.status.go_end:
                i.processor.opareq.wait = msec

    def askCut(self, Range):
        if Range:
            progress = None
            gap = False
            cur_progresses = list(self.progresses.values())
            for i in cur_progresses:
                if i.end == Range[1]:
                    progress = i
                    break
            else:
                for i in cur_progresses:
                    if i.begin == Range[1]:
                        gap = True
                        break
                    elif i.end == Range[0]:
                        gap = True
                        break

                if gap:
                    return Range

                if not progress:
                    return []

            return progress.processor.cutRequest(Range)
        else:
            return []

    def cut(self, Progress, Range):
        with self._prog_lock__:
            self.progresses['%d-%d' % (Progress.begin, Range[0])] = Progress
            del self.progresses['%d-%d' % (Progress.begin, Progress.end)]
            Progress.setNewRange([Progress.begin, Range[0]])

    def __packet_params__(self):
        return ['status', 'progresses']

    def pack(self):
        with self._prog_lock__:
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


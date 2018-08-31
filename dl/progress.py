# -*- coding: UTF-8 -*-
import time, sys, math, threading
from WaitLock import WaitLock
from io import StringIO

def load_attr(obj, data, ignores=[]):
    for i, j in data.items():
        if i not in ignores:
            setattr(obj, i, j)

class Status:
    def __init__(self):
        self.startTime_go = time.clock()
        self.endTime_go = None
        self.endTime_done = None

        self.endFlag_go = False
        self.endFlag_done = False
        self.pauseFlag = False

        self.retry_count = 0
        self.empty_count = 0

class Piece:
    def __init__(self):
        self.go_inc = 0
        self.lastLeft = None
        self.lastTime_go = time.clock()



class Progress:



    def __init__(self, url_index, url, range, GlobalProg):

        self.url_index = url_index
        self.GlobalProg = GlobalProg
        self.BLOCK_SIZE = GlobalProg.file.BLOCK_SIZE

        self.buffer_piece = {}

        self.url = url
        self.thread = None

        self.begin = range[0]
        self.end = range[1]
        self.length = range[1] - range[0]

        # INCREMENT
        self.go_inc = 0
        self.done_inc = 0
        self.increment = 0

        self.status = Status()
        self.piece = Piece()

        self.wait = WaitLock(timeout=2)
        self.lock = threading.Lock()



    def done(self, byte_length):
        self.done_inc += byte_length

        if self.done_inc == self.length:
            # print self.length
            self.status.endFlag_done = True

            for i in self.GlobalProg.queue.values():
                if i.status.endFlag_done is False:
                    break
            else:
                # print 'end'
                self.GlobalProg.status.endFlag_done = True
                self.GlobalProg.status.endTime_done = time.clock()

        if self.GlobalProg.status.pauseFlag is True:
            self.status.pauseFlag = True

    def merge_buffer_piece(self):

        if len(self.buffer_piece) is 0:
            return None
        else:
            ret_buf = ''
            stream = StringIO()

            _part_up = sorted(self.buffer_piece.items(), key=lambda x: x[0])

            for i in _part_up:
                ret_buf += i[1]
                if len(i[1]) != 1024:
                    print len(ret_buf), len(i[1])
            return ret_buf

    def go(self, byte_length):
        self.go_inc += byte_length

        if self.GlobalProg.save is True:
            pos = int((self.begin + self.go_inc - byte_length) * 1.0 / self.BLOCK_SIZE)
            _fil_len = int(math.ceil(byte_length * 1.0 / self.BLOCK_SIZE))
            for i in range(_fil_len):
                self.GlobalProg.map[pos + i] = self.url_index

        if self.go_inc == self.length:
            self.wait.release()
            self.status.endFlag_go = True
            self.status.endTime_go = time.clock()

            for i in self.GlobalProg.queue.values():
                if i.status.endFlag_go is False:
                    break
            else:
                self.GlobalProg.status.endFlag_go = True
                self.GlobalProg.status.endTime_go = time.clock()

    def clip_range_req(self, take_range):
        with self.wait as res:
            if res is False:
                return [None, None]

            if self.status.endFlag_go is True or take_range[0] < self.begin or take_range[1] > self.end:
                return [None, None]

            while self.begin + self.go_inc >= take_range[0]:
                take_range[0] += self.BLOCK_SIZE
            if take_range[0] >= take_range[1]:
                return [None, None]
            new_range = [self.begin, take_range[0]]

            self.GlobalProg.clip_range([self.begin, self.end], new_range)
            self.set_range(new_range)

            put_range = take_range
            return put_range

    def set_range(self, _range):
        self.begin = _range[0]
        self.end = _range[1]
        self.length = _range[1] - _range[0]

    def getLeft(self):
        return self.length - self.go_inc


    def getinsSpeed(self):

        if self.status.endFlag_go is True:

            ret = self.piece.go_inc / (self.status.endTime_go - self.status.startTime_go)
            # only the first can get the last instant speed. or it will get 0
            self.piece.go_inc = 0
        else:
            t = time.clock()
            ret = self.piece.go_inc / (t - self.piece.lastTime_go)
            self.piece.lastTime_go = t

        self.piece.go_inc = 0

        return ret

    def getavgSpeed(self):
        if self.status.endFlag_go is False:
            return self.go_inc / (time.clock() - self.status.startTime_go)
        else:
            return self.go_inc / (self.status.endTime_go - self.status.startTime_go)


    def isGoEnd(self):
        return self.status.endFlag_go and self.getLeft() == 0

    def isDoneEnd(self):
        return self.status.endFlag_done

    def isAlive(self):
        if self.thread is not None:
            return self.thread.isAlive()
        else:
            return False

    def re_init(self):
        self.go_inc = 0
        self.increment = 0
        self.done_inc = 0

        self.status = Status()
        self.piece = Piece()

        self.GlobalProg.status.endFlag_go = False
        self.GlobalProg.status.endFlag_done = False

        if self.GlobalProg.save is True:

            pos = int(self.end * 1.0 / self.BLOCK_SIZE)
            _fil_len = int(self.length * 1.0 / self.BLOCK_SIZE) - 1
            for i in range(_fil_len):
                self.GlobalProg.map[pos - i - 1] = None

    def dump(self):
        _dump_dict = dict(
            url_index=self.url_index,
            range=[self.begin, self.end],
            buffer_piece=self.buffer_piece,
            go_inc=self.go_inc,
            done_inc=self.done_inc,
            increment=self.increment,
            status={
                'endFlag_go': self.status.endFlag_go,
                'endFlag_done': self.status.endFlag_done,
                'pauseFlag': self.status.pauseFlag,
                'startTime': self.status.startTime_go,
                'endTime': self.status.endTime_go,
            }

        )

        return _dump_dict

    @staticmethod
    def load(_data):
        prog = Progress(_data['url_index'], None, _data['range'], None)

        load_attr(prog, _data, ['status'])
        load_attr(prog.status, _data)

        return prog

    def activate(self, GlobalProg):
        self.GlobalProg = GlobalProg
        # self.lock = threading.Lock()
        self.url = GlobalProg.urls[self.url_index]

        if self.status.endTime_go is False:
            self.status.startTime_go = time.clock()

        pos = int((self.begin) * 1.0 / self.BLOCK_SIZE)
        _fil_len = int(math.ceil(self.go_inc * 1.0 / self.BLOCK_SIZE))
        for i in range(_fil_len):
            self.GlobalProg.map[pos + i] = self.url_index

class GlobalProgress:

    def __init__(self, DLMobj, urls, file, save=True):

        self.DLMobj = DLMobj
        self.save = save
        self.urls = urls
        self.file = file
        if self.save is True:
            self.map = self.make_map(self.file.size)
        else:
            self.map = None

        self.piece = Piece()
        self.status = Status()

        self.piece.lastLeft = self.file.size
        self.lastSpeed = None

        self.queue = {}
        self.monitor = None
        self.retry_wait = threading.Lock()
        # global BLOCK_SIZE
        # BLOCK_SIZE = self.file.BLOCK_SIZE

    def make_map(self, size):
        return [None for i in range(int(math.ceil(size*1.0 / self.file.BLOCK_SIZE)))]

    def launch_monitor(self):
        self.monitor = threading.Thread(target=self.__monitor_thread)
        self.monitor.start()

    def __monitor_thread(self):
        while True:
            if self.status.pauseFlag is True or self.status.endFlag_go is True:
                break

            for i in self.queue.values():
                if i.isGoEnd() is False:
                    if i.thread is None or i.thread.isAlive() is False:
                        if self.retry_wait.locked() is False:
                            self.DLMobj.launch(i)

            time.sleep(3)

    def enqueue(self, url, _range):
        self.status.endFlag_go = False
        self.status.endFlag_done = False
        _prog = Progress(self.urls.index(url), url, _range, self)
        self.queue['%d-%d' % (_range[0], _range[1])] = _prog
        if self.monitor is None or self.monitor.isAlive() is False:
            self.launch_monitor()
        return _prog

    def getinsSpeed(self):
        if self.piece.lastLeft is None or self.piece.lastTime_go is None:
            # print self.queue.keys()
            if len(self.queue) > 0:
                self.piece.lastLeft = self.getLeft()
                self.piece.lastTime_go = time.clock()
            return 0
        else:
            now_left = self.getLeft()
            # print now_left, self.lastLeft
            if self.status.endFlag_go is False:
                ret = (self.piece.lastLeft - now_left) / (time.clock() - self.piece.lastTime_go)

            else:
                ret = (self.piece.lastLeft - now_left) / (self.status.endTime_go - self.status.startTime_go)

            self.piece.lastLeft = now_left
            self.piece.lastTime_go = time.clock()

            if ret < 0:
                return self.getavgSpeed()

            return ret

    def getavgSpeed(self):
        """global average speed"""

        if self.status.endFlag_go is False:
            if self.lastSpeed is None:
                return (self.file.size - self.getLeft()) / (time.clock() - self.status.startTime_go)
            else:
                return (self.lastSpeed + (self.file.size - self.getLeft()) / (time.clock() - self.status.startTime_go)) / 2
        else:
            if self.lastSpeed is None:
                return (self.file.size - self.getLeft()) / (self.status.endTime_go - self.status.startTime_go)
            else:
                return (self.lastSpeed + (self.file.size - self.getLeft()) / (self.status.endTime_go - self.status.startTime_go)) / 2

    def getLeft(self):
        """get global left of the downloading."""
        sum = 0
        for i in self.queue.values():
            # sum += i.getLeft()
            sum += i.length - i.go_inc
        return sum

    def getCompl_perc(self):
        return 1.0 - self.getLeft() *1.0 / self.file.size

    def getOnlineQuantity(self):
        _count = 0
        for i in self.queue.values():
            if i.thread is not None and i.thread.isAlive() is True:
                _count += 1

        return _count

    def getRuningQuantity(self):
        _count = 0
        for i in self.queue.values():
            if i.isGoEnd() is False:
                _count += 1
        return _count

    def isDone(self):
        return self.status.endFlag_go

    def getQueueServerMes(self):
        _dict = {}
        # _server = None

        for i in self.queue.values():
            if _dict.has_key(i.url) is True:
                _dict[i.url]['COUNT'] += 1
                _dict[i.url]['SPEED'] += i.getavgSpeed()
            else:
                _dict[i.url] = {'SPEED': i.getavgSpeed(), 'COUNT': 1}

        return _dict

    def get_parent_prog(self, next_range):
        if len(self.queue) is 0:
            return None
        for i in self.queue.values():
            if next_range[0] >= i.begin and next_range[1] <= i.end:
                return i

        return None

    def clip_range(self, old_range, new_range):
        prog = self.queue['%d-%d' % (old_range[0], old_range[1])]
        # print prog
        del self.queue['%d-%d' % (old_range[0], old_range[1])]
        self.queue['%d-%d' % (new_range[0], new_range[1])] = prog

    def pause(self):

        self.status.pauseFlag = True
        while True:
            for i in self.queue.values():
                if i.status.pauseFlag is False and \
                        i.status.endFlag_done is False and \
                        i.thread is not None and \
                        i.thread.isAlive() is True:
                    break
            else:
                break
            time.sleep(0.2)

    def _continue(self):
        self.status.pauseFlag = False

        for i in self.queue.values():
            i.status.pauseFlag = False
            if i.isGoEnd() is False:
                self.DLMobj.launch(i)


    def dump(self):

        _copy_queue = {}
        for i, j in self.queue.items():
            _copy_queue[i] = j.dump()

        _dump_dict = dict(
            queue=_copy_queue,
            status=dict(
                endFlag_done=self.status.endFlag_done,
                endFlag_go=self.status.endFlag_go,
                pauseFlag=self.status.pauseFlag
            )
            # startTime=self.startTime,
            # endTime=self.endTime,
            # lastLeft=self.lastLeft,
            # lastSpeed=self.lastSpeed
        )

        return _dump_dict

    def activate(self, _data):
        for i, j in _data['queue'].items():
            self.queue[i] = Progress.load(j)
            self.queue[i].activate(self)

        load_attr(self, _data, ['queue', 'status'])
        load_attr(self.status, _data['status'])


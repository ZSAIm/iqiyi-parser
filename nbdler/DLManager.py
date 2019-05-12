

from .packer import Packer
import time, threading
from .DLError import DLUrlError
import queue

class Manager(Packer, object):
    def __init__(self):
        self.tasks = {}

        self.id_map = []
        self.name_id = {}

        self.max_task = 2

        self.queue = TaskQueue()

        self._insp_thr = None
        self.shutdown_flag = False
        self.all_pause_flag = True
        self.__queue_lock__ = threading.RLock()
        self._done_buff = []

        self._trap_thrs = {}
        self.except_queue = queue.Queue()
        # self._except = None

    def __insp__(self):

        while True:

            self.checkRunQueue()
            if self.shutdown_flag or self.all_pause_flag:
                self.checkRunQueue()
                break
            self.run()

            if not self.queue.undone and self.isEnd():
                self.checkRunQueue()
                break
            time.sleep(0.01)

    def checkRunQueue(self):
        with self.__queue_lock__:
            for i in list(self.queue.run):
                if self.tasks[i].isEnd():
                    self.tasks[i].close()
                    self.queue.run.remove(i)
                    self.queue.done.append(i)
                    self._done_buff.append(i)
                elif self.tasks[i].isCritical():
                    self.queue.run.remove(i)
                    self.queue.critical.append(i)

    def getExceptions(self):
        return list(self.except_queue.queue)


    def getHandler(self, name=None, id=None):
        if name is None and id is None:
            return None
        if id is not None:
            return self.tasks[id]

        if name is not None:
            return self.tasks[self.getIdFromName(name)]

    def getAllTask(self):
        return self.tasks

    def getRunQueue(self):
        return self.queue.run

    def getPauseQueue(self):
        return self.queue.pause

    def getDoneQueue(self):
        return self.queue.done

    def getUndoneQueue(self):
        return self.queue.undone

    def getCriticalQueue(self):
        return self.queue.critical

    def getIdFromName(self, name):
        return self.name_id[name]


    def getNameFromId(self, id):
        for i, j in self.name_id.items():
            if id == j:
                return i

    def addHandler(self, Handler, name=None):
        with self.__queue_lock__:
            id = self.newId()

            name = id if not name else name

            self.tasks[id] = Handler
            self.name_id[name] = id

            self.id_map[id] = True
            self.queue.undone.append(id)

        return id

    def newId(self):
        for i, j in enumerate(self.id_map):
            if not j:
                return i
        else:
            self.id_map.append(False)
            return len(self.id_map) - 1

    def remove(self, id):
        with self.__queue_lock__:
            del self.tasks[id]
            self.id_map[id] = False
            del self.name_id[self.getIdFromName(id)]

    def run(self, id=None):
        with self.__queue_lock__:
            self.all_pause_flag = False
            if not self._insp_thr or not self._insp_thr.isAlive():

                self._insp_thr = threading.Thread(target=self.__insp__, name='Nbdler-Manager')
                self._insp_thr.start()
            if id is not None:
                if len(self.queue.run) < self.max_task:
                    self.tasks[id].run()
                    self.queue.run.append(id)
            else:

                for i in list(self.queue.undone):
                    if len(self.queue.run) < self.max_task:
                        # if not self.tasks[i].isEnd():
                        self.tasks[i].run()
                        self.queue.run.append(i)
                        if i in self.queue.pause:
                            self.queue.pause.remove(i)
                        self.queue.undone.remove(i)
                    else:
                        break

    def pause(self, id=None):
        self._done_buff = []
        if id is not None:
            self.tasks[id].pause()
            with self.__queue_lock__:
                if id in self.queue.run:
                    self.queue.run.remove(id)
                if id not in self.queue.pause:
                    self.queue.pause.append(id)
        else:
            self.all_pause_flag = True
            self._insp_thr.join()

            for i in list(self.getRunQueue()):
                threading.Thread(target=self._pause, name='Nbdler-Pause-%d' % i, args=(i,)).start()
                # threading.Thread(target=self.tasks[i].pause, name='manager-pause-%d' % i).start()

    def isShutdown(self):
        return self.shutdown_flag



    def _pause(self, id):
        self.tasks[id].pause()
        with self.__queue_lock__:
            if id in self.queue.run:
                self.queue.run.remove(id)
            if id not in self.queue.pause:
                self.queue.pause.append(id)
        self.checkRunQueue()

    def shutdown(self):
        self._done_buff = []
        self.shutdown_flag = True
        if self._insp_thr:
            self._insp_thr.join()

            for i in self.tasks.values():
                threading.Thread(target=i.shutdown).start()


    def close(self):
        pass

    def join(self):
        if not self._insp_thr:
            raise RuntimeError('cannot join thread before it is started')
        for i, j in list(self.tasks.items()):
            self.tasks[i].join()

        self._insp_thr.join()

    def trap(self):
        if not self._insp_thr:

            raise RuntimeError('cannot join thread before it is started')
        for i in list(self.tasks.values()):
            if not i.isEnd():
                if i not in self._trap_thrs:
                    thr = threading.Thread(target=self._trap, args=(i,))
                    self._trap_thrs[i] = thr
                    thr.start()

        while self._trap_thrs or not self.except_queue.empty():

            if not self.except_queue.empty():
                _except = self.except_queue.get(timeout=1)
                raise _except
            time.sleep(0.01)
        self._insp_thr.join()

    def _trap(self, task):

        try:
            task.trap()
        except DLUrlError as e:
            self.except_queue.put(e)

        del self._trap_thrs[task]

    def getAvgSpeed(self, id=None):
        with self.__queue_lock__:
            if id is not None:
                return self.tasks[id].getAvgSpeed()

            speed = 0
            for i in self.queue.run:
                if not self.tasks[i].isEnd():
                    speed += self.tasks[i].getAvgSpeed()

        return speed

    def getInsSpeed(self, id=None):
        with self.__queue_lock__:
            if id is not None:
                return self.tasks[id].getInsSpeed()

            speed = 0
            for i in self.queue.run:
                speed += self.tasks[i].getInsSpeed()

            for i in list(self._done_buff):
                tmp = self.tasks[i].getInsSpeed()
                speed += tmp
                if tmp < 100:
                    self._done_buff.remove(i)
            # self._done_buff = []
        return speed

    def getIncByte(self, id=None):
        with self.__queue_lock__:
            if id is not None:
                return self.tasks[id].getIncByte()

            inc = 0
            for i in self.queue.done:
                inc += self.tasks[i].getFileSize()
            for i in self.queue.run:
                dl = self.tasks[i]
                inc += dl.getFileSize() - dl.getLeft()

        return inc

    def getFileSize(self, id=None):
        if id is not None:
            return self.tasks[id].getFileSize()

        return self.getTotalSize()

    def getTotalSize(self):
        size = 0
        for i, j in self.tasks.items():
            size += j.getFileSize()

        return size

    def getLeft(self, id=None):
        with self.__queue_lock__:
            if id is not None:
                return self.tasks[id].getLeft()

            left = 0
            for i in self.queue.run:
                if not self.tasks[i].isEnd():
                    left += self.tasks[i].getLeft()
            for i in self.queue.undone:
                left += self.tasks[i].getLeft()
        return left


    def isEnd(self, id=None):
        with self.__queue_lock__:
            if id is not None:
                return self.tasks[id].isEnd()

            for i in self.queue.run:
                if not self.tasks[i].isEnd():
                    break
            else:
                if self._trap_thrs:
                    return False
                if not self.queue.undone:
                    if threading.current_thread() == self._insp_thr or not self._insp_thr or not self._insp_thr.isAlive():
                        return True
                    return False

                else:
                    return False
        return False

    def config(self, **kwargs):
        for i, j in self.__config_params__():
            if i in kwargs:
                setattr(self, j, kwargs[i])

    def __config_params__(self):
        return [('max_task', 'max_task')]


    def __packet_params__(self):
        return ['tasks', 'max_task']


    def unpack(self, packet):
        Packer.unpack(self, packet)


class TaskQueue(object):
    def __init__(self):
        self.run = []
        self.pause = []
        self.undone = []
        self.done = []
        self.ready = []
        self.critical = []


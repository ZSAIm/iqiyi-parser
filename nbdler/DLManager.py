

from .packer import Packer
import time, threading

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
            with self.__queue_lock__:
                for i in list(self.getRunQueue()):
                    threading.Thread(target=self.tasks[i].pause).start()
                    if i in self.queue.run:
                        self.queue.run.remove(i)
                    if i not in self.queue.pause:
                        self.queue.pause.append(i)

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
            if not self.isEnd():
                self.run()
            else:
                return
            # raise RuntimeError('cannot join thread before it is started')

        self._insp_thr.join()
        for i in self.tasks.values():
            i.join()

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
                return True if not self.queue.undone else False
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



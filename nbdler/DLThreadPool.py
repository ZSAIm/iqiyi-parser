
# import logging
import threading
import time

class ThreadPool:
    def __init__(self, Handler):
        self._handler = Handler
        self._threads = []
        self._insp_thr_ = None
        self._app_lock = threading.Lock()

    def Thread(self, *args, **kwargs):
        with self._app_lock:
            thr = threading.Thread(*args, daemon=self._handler._daemon, **kwargs)
            self._threads.append(thr)
            if not self._insp_thr_ or (self._insp_thr_._started.is_set() and not self._insp_thr_.isAlive()):
                self._insp_thr_ = threading.Thread(target=self.__insp__, name='Nbdler-ThreadPool', daemon=self._handler._daemon)
                self._insp_thr_.start()
        return thr

    def __insp__(self):
        while True:
            with self._app_lock:
                for i in list(self._threads):
                    if i._started.is_set() and not i.isAlive():
                        self._threads.remove(i)
                if not self._threads:
                    break
            time.sleep(0.1)

    def isAllDead(self):
        if len(self._threads) == 0:
            return True
        elif len(self._threads) == 1:
            if self._threads[0] is threading.currentThread():
                return True
            else:
                return False
        else:
            return False

    def getThreadsFromName(self, name):
        threads = []
        for i in list(self._threads):
            if i.getName() == name:
                threads.append(i)

        return threads




import time
from . import DLCommon as cv
import threading
# logger = logging.getLogger('nbdler')


class Inspector(object):
    def __init__(self, Handler, GlobalProgress, Allotter):
        self.globalprog = GlobalProgress
        self.handler = Handler
        self.allotter = Allotter

        self._insp_thr = None
        self._allot_thr = None
        self.__limiter_thread__ = None

    def install(self, Allotter):
        self.allotter = Allotter

    def Thread(self, *args, **kwargs):
        return self.handler.threads.Thread(*args, **kwargs)

    def runAllotter(self):
        if not self._allot_thr or self._allot_thr.isStoped():
            self._allot_thr = self.Thread(target=self._allotter, name=cv.ALLOTTER)
            self._allot_thr.start()

    def runInspector(self):
        if not self._insp_thr or self._insp_thr.isStoped():
            self._insp_thr = self.Thread(target=self._inspector, name=cv.INSPECTOR)
            self._insp_thr.start()


    def _inspector(self):
        while True:
            if self._is_ready():
                for i in list(self.globalprog.progresses.values()):
                    if not i.isGoEnd() and not i.processor.isRunning():
                        i.processor.run()
            else:
                break

            time.sleep(0.5)


    def _allotter(self):
        while True:
            if self._is_ready():
                valid_num = self.handler.url.max_conn - len(self.globalprog.getConnections())
                for i in range(valid_num):
                    if not self._is_ready():
                        break
                    ask_urlid, ask_range = self.allotter.assign()
                    if ask_urlid != -1 and ask_range:
                        ask_range = self.globalprog.askCut(ask_range)
                        if ask_range:
                            progress = self.globalprog.insert(ask_urlid, *ask_range)
                            progress.run()
            else:
                break
            time.sleep(1)

        # while True:
        #     if self.globalprog.status.endflag or self.globalprog.pause_req or self.globalprog.status.pauseflag or self.globalprog.isCritical():
        #         break
        #     with self.allotter.__allotter_lock__:
        #         for i in range(self.handler.url.max_conn - len(self.globalprog.getConnections())):
        #
        #             if self.globalprog.status.endflag or self.globalprog.pause_req or self.globalprog.status.pauseflag:
        #                 break
        #
        #             ask_urlid, ask_range = self.allotter.assign()
        #             if ask_urlid != -1 and ask_range:
        #                 ask_range = self.globalprog.askCut(ask_range)
        #                 if ask_range:
        #                     # print('ask_range: ', ask_range)
        #                     progress = self.globalprog.insert(ask_urlid, *ask_range)
        #                     progress.run()
        #     time.sleep(1.5)

    def _is_ready(self):
        return not self.globalprog.isGoEnd() and not self.globalprog.status.pausing() and \
               not self.globalprog.isCritical() and not self.globalprog.status.isPaused()


    # def __limiter__(self):
    #     while True:
    #         if self.globalprog.status.endflag or self.globalprog.pause_req or self.globalprog.status.pauseflag:
    #             break
    #         cur_speed = self.globalprog.getAvgSpeed()
    #         if cur_speed >= self.handler.url.max_speed:
    #             sec = (cur_speed - self.handler.url.max_speed) / cur_speed * 50
    #             self.__last_wait__ = sec
    #             self.globalprog.askWait(sec)
    #             print 1, sec
    #         else:
    #             sec = self.__last_wait__ * cur_speed / self.handler.url.max_speed
    #             self.__last_wait__ = sec
    #             self.globalprog.askWait(sec)
    #             # time.sleep(0.0001)
    #             # continue
    #             print 2, sec, cur_speed
    #         msg = 'LimiterWait: %s' % sec
    #         extra = {'progress': '%010s-%010s' % ('?', '?'), 'urlid': '?'}
    #         logger.debug(msg, extra=extra)
    #
    #         time.sleep(0.1)


    def run(self):
        self.runInspector()
        self.runAllotter()
        # self.runLimiter()
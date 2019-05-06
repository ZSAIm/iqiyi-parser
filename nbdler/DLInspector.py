
import time

# logger = logging.getLogger('nbdler')


class Inspector(object):
    def __init__(self, Handler, GlobalProgress, Allotter):
        self.globalprog = GlobalProgress
        self.handler = Handler
        self.allotter = Allotter

        self._selfcheck_thr = None
        self._allo_thr = None
        self.__limiter_thread__ = None

        # self.__last_wait__ = 0

    def install(self, Allotter):
        self.allotter = Allotter

    def _Thread(self, *args, **kwargs):
        return self.handler.thrpool.Thread(*args, **kwargs)

    def runAllotter(self):
        if not self._allo_thr or (self._allo_thr._started.is_set() and not self._allo_thr.isAlive()):
            self._allo_thr = self._Thread(target=self.__allotter__, name='Nbdler-Allotter')
            self._allo_thr.start()

    def runSelfCheck(self):
        if not self._selfcheck_thr or not self._selfcheck_thr.isAlive():
            self._selfcheck_thr = self._Thread(target=self.__selfcheck__, name='Nbdler-SelfCheck')
            self._selfcheck_thr.start()

    # def runLimiter(self):
    #     if self.handler.url.max_speed != -1:
    #         if not self.__limiter_thread__ or not self.__limiter_thread__.isAlive():
    #             self.__limiter_thread__ = threading.Thread(target=self.__limiter__)
    #             self.__limiter_thread__.start()

    def __selfcheck__(self):
        while True:
            if self.globalprog.status.endflag or self.globalprog.status.pauseflag:
                break

            # progresses = self.globalprog.progresses.copy()
            for i in list(self.globalprog.progresses.values()):
                if not i.processor.isGoEnd() and not i.processor.isRunning():
                    if self.globalprog.pause_req:
                        return

                    i.processor.run()

            if self.globalprog.pause_req:
                return
            time.sleep(1)

    def __allotter__(self):
        while True:
            if self.globalprog.status.endflag or self.globalprog.pause_req or self.globalprog.status.pauseflag:
                break
            with self.allotter.__allotter_lock__:
                for i in range(self.handler.url.max_conn - len(self.globalprog.getConnections())):

                    if self.globalprog.status.endflag or self.globalprog.pause_req or self.globalprog.status.pauseflag:
                        break

                    ask_urlid, ask_range = self.allotter.assign()
                    if ask_urlid != -1 and ask_range:
                        ask_range = self.globalprog.askCut(ask_range)
                        if ask_range:
                            # print('ask_range: ', ask_range)
                            progress = self.globalprog.insert(ask_urlid, *ask_range)
                            progress.run()
            time.sleep(1.5)

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
        self.runSelfCheck()
        self.runAllotter()
        # self.runLimiter()
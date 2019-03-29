



import logging, math
import time, threading

# logger = logging.getLogger('nbdler')


class Inspector(object):
    def __init__(self, Handler, GlobalProgress, Allotter):
        self.globalprog = GlobalProgress
        self.handler = Handler
        self.allotter = Allotter

        self.__selfcheck_thread__ = None
        self.__allotter_thread__ = None
        self.__limiter_thread__ = None

        # self.__last_wait__ = 0

    def install(self, Allotter):
        self.allotter = Allotter

    def runAllotter(self):
        if not self.__allotter_thread__ or not self.__allotter_thread__.isAlive():
            self.__allotter_thread__ = threading.Thread(target=self.__allotter__, name='Allotter')
            self.__allotter_thread__.start()

    def runSelfCheck(self):
        if not self.__selfcheck_thread__ or not self.__selfcheck_thread__.isAlive():
            self.__selfcheck_thread__ = threading.Thread(target=self.__selfcheck__, name='SelfCheck')
            self.__selfcheck_thread__.start()

    # def runLimiter(self):
    #     if self.handler.url.max_speed != -1:
    #         if not self.__limiter_thread__ or not self.__limiter_thread__.isAlive():
    #             self.__limiter_thread__ = threading.Thread(target=self.__limiter__)
    #             self.__limiter_thread__.start()

    def __selfcheck__(self):
        while True:
            if self.globalprog.status.endflag or self.globalprog.status.pauseflag:
                break

            progresses = self.globalprog.progresses.copy()
            for i in progresses.values():
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
                    if ask_urlid != -1:
                        ask_range = self.globalprog.askCut(ask_range)
                        if ask_range:
                            progress = self.globalprog.insert(ask_urlid, *ask_range)
                            # msg = 'Insert: %010d-%010d, [%d]' % (ask_range[0], ask_range[1], ask_urlid)
                            # extra = {'progress': '%010s-%010s' % ('..........', '..........'), 'urlid': '.'}
                            # logger.info(msg, extra=extra)
                            progress.run()
            time.sleep(3)

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
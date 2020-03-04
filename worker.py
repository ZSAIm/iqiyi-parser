# -*- coding: UTF-8 -*-
from eventdriven import ControllerPool, Controller
from urllib.request import ProxyHandler


class Worker:
    order = 999

    def response(self):
        pass

    def getinfo(self):
        pass

    def request(self):
        pass


# 运行中的worker
working = []


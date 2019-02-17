

import socket, ssl
import threading
# import DL.progress
import time
# import sys
from DLInfos import Target
# import math
import logging


logger = logging.getLogger('nbdler')


MAX_BUFFER_SIZE = 1024 * 1024 * 1

socket.setdefaulttimeout(3)

class OpaReq:
    def __init__(self):
        self.cut = []
        self.pause = False
        self.switch = False
        self.wait = 0

    def clear(self):
        self.cut = []
        self.pause = False
        self.switch = False
        self.wait = 0


class ErrorCounter(object):

    _404__THRESHOLD = 5
    _302__THRESHOLD = 20

    RECV_TIMEOUT_THRESHOLD = 5
    SOCKET_ERROR_THRESHOLD = 5

    def __init__(self):
        self._404_ = 0
        self._302_ = 0

        self.recv_error = 0
        self.socket_error = 0

        self.error_occur = False

    def __setattr__(self, key, value):
        # setattr(self, key, value)
        object.__setattr__(self, key, value)
        if key != 'error_occur':
            for i, j in self.check().items():
                if getattr(self, i, 0) > getattr(self, j, 0):
                    self.error_occur = True
            else:
                self.error_occur = False

    def isError(self):
        return self.error_occur

    def clear(self):
        self._404_ = self._302_ = self.recv_error = self.socket_error = 0

    def check(self):
        return {
            '_404_': '_404__THRESHOLD',
            '_302_': '_302__THRESHOLD',
            'recv_error': 'RECV_TIMEOUT_THRESHOLD',
            'socket_error': 'SOCKET_ERROR_THRESHOLD'
            # self._404_: ErrorCounter._404__THRESHOLD,
            # self._302_: ErrorCounter._302__THRESHOLD,
            # self.recv_error: ErrorCounter.RECV_TIMEOUT_THRESHOLD,
            # self.socket_error: ErrorCounter.SOCKET_ERROR_THRESHOLD
        }



class Processor(object):
    def __init__(self, Progress, Urlid):
        self.progress = Progress

        self.url = None
        self.urlid = Urlid

        # self.loadUrl(Urlid)

        self.buff = b''

        self.opareq = OpaReq()
        self.__opa_lock__ = threading.Lock()

        self.target = Target()

        self.__thread__ = None
        self.__run_lock__ = threading.Lock()
        # self.__404_counter__ = 0

        self.error_counter = ErrorCounter()

        self.__buff__lock__ = threading.Lock()

    # def __setattr__(self, key, value):
    #     object.__setattr__(self, key, value)
        # if key == 'urlid':
        #     if self.checkUrl():
        #         self.url = self.getHandler().url.getUrls()[value]
        #         self.target = DLInfos.Target(self.url.url, None, self.url.headers.items())
        #     else:
        #         self.url = None
        #         self.target = None

    def loadUrl(self, Urlid):

        urls = self.getHandler().url.getUrls()

        if Urlid in urls:
            self.url = urls[Urlid]
            # if self.urlid != Urlid:
                # self.url.reload()
            self.target.load(self.url.url)
                # self.target.load(self.url.url) # = DLInfos.Target(self.url.url, None)
        else:
            self.url = None

        self.urlid = Urlid

    def isReady(self):
        return self.progress.isReady()

    def isRunning(self):
        return self.__thread__ and self.__thread__.isAlive()

    def isPause(self):
        return self.progress.isPause()

    def isEnd(self):
        return self.progress.isEnd()




    def getHandler(self):
        return self.progress.globalprog.handler

    def selfCheck(self):

        if not self.url:
            self.loadUrl(self.urlid)

        if not self.url or not self.getHandler().url.hasUrl(self.urlid):
            self.getSwitch()

        if self.isReady():
            if not self.isRunning():
                if self.error_counter.isError():
                    self.getSwitch()

                if self.opareq.cut:
                    self.getCut()

                if self.opareq.pause:
                    self.getPause()
                    return False

                return True
        else:
            self.close()

        return False



    def run(self):
        with self.__run_lock__:
            if self.selfCheck():
                self.__thread__ = threading.Thread(target=self.__getdata__, name='Processor')
                self.__thread__.start()



    def __getdata__(self):
        if self.opareq.cut:
            self.getCut()

        if self.opareq.pause:
            self.getPause()
            return
        # if self.checkOpa():

        sock, buff = self.makeSocket()

        if not sock:
            # msg = 'SocketNotBuilt: ->rerun.'
            # extra = {'progress': '%-10d-%10d' % (self.progress.begin, self.progress.end),
            #          'urlid': self.urlid}
            # logger.warning(msg, extra=extra)

            # self.target = DLInfos.Target(self.url.url, None, self.url.headers.items())
            self.error_counter.socket_error += 1
            time.sleep(2)
            self.run()
            return
        else:

            status, _headers = parse_headers(buff[:(buff.index(b'\r\n\r\n'))])
            self.target.update(headers=_headers)

            if status == 302:
                self.__302__(sock)
                return
            elif status == 404:
                self.__404__(sock)
                return
            elif status != 206:
                self.__404__(sock)
                return

            self.error_counter.clear()

            buff = buff[(buff.index(b'\r\n\r\n') + 4):]

            if self.progress.length < len(buff):
                print(self.progress.end - self.progress.begin, len(buff))
                return

            self.progress.go(len(buff))
            self.__recv_loop__(sock, buff)

            sock.shutdown(socket.SHUT_RDWR)

    def makeSocket(self):
        sock = None
        buff = b''

        try:
            ip = socket.gethostbyname(self.target.host)

            if self.target.protocol == 'https':
                sock = ssl.wrap_socket(socket.socket())
            elif self.target.protocol == 'http':
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            assert sock is not None
            if not sock:
                self.error_counter.socket_error += 1
                return None, b''
            # if self.opareq.pause:
            #     self.getPause()
            #     return None, ''

            # try:
            sock.connect((ip, self.target.port))

            Range = (self.progress.begin + self.progress.go_inc, self.progress.end)

            packet = 'GET %s HTTP/1.1\r\n' % self.target.path + \
                     'Host: %s\r\n' % self.target.host + \
                     'Connection: keep-alive\r\n' + \
                     'Range: bytes=%d-%d\r\n' % Range + \
                     '%s' + \
                     '\r\n'

            pack_format = ''
            for i, j in self.url.headers.items():
                pack_format += i + ': ' + j + '\r\n'

            packet = packet % pack_format
            sock.send(str.encode(str(packet)))
            buff = sock.recv(1024)
        except:
            # sock.shutdown(socket.SHUT_RDWR)
            self.error_counter.socket_error += 1
            sock = None
        else:
            if not buff:
                sock.shutdown(socket.SHUT_RDWR)
                sock = None
            else:
                while b'\r\n\r\n' not in buff:
                    buff += sock.recv(512)
                    if 'HTTP' not in buff:
                        sock.shutdown(socket.SHUT_RDWR)
                        sock = None
                        break

        return sock, buff

    def __302__(self, sock):
        if self.target.headers.get('location', None):
            # with self.url.target_lock:
            self.target.load(self.target.headers.get('location'))
            # self.target.update(url=self.target.headers.get('location'), headers=self.target.headers)
            # self.target = DLInfos.Target(self.target.headers.get('location'), self.target.headers)
        sock.shutdown(socket.SHUT_RDWR)

        # msg = 'HTTP 302: ->continue("%s")' % self.target.headers.get('location', None)
        # extra = {'progress': '%-10d-%10d' % (self.progress.begin, self.progress.end), 'urlid': self.urlid}
        # logger.debug(msg, extra=extra)

        self.run()

    def __404__(self, sock):

        self.error_counter._404_ += 1
        # self.target = DLInfos.Target(self.url.url, self.url.headers.items())
        self.url.reload()

        sock.shutdown(socket.SHUT_RDWR)

        time.sleep(2)

        self.run()



    def __recv_loop__(self, sock, buff):

        while True:
            if self.opareq.cut:
                self.getCut()

            if self.opareq.pause:
                self.buffer(buff)
                self.getPause()
                break

            # if self.opareq.wait:
            #     self.getWait()

            last_len = len(buff)
            rest = self.progress.length - self.progress.go_inc
            try:
                if rest == 0:
                    if len(buff) != 0:
                        self.buffer(buff)
                    break
                elif rest < 4096:
                    buff += sock.recv(rest)
                else:
                    buff += sock.recv(4096)
            except:

                self.error_counter.recv_error += 1
                self.buffer(buff[:last_len])
                return

            if len(buff) == last_len:
                self.error_counter.recv_error += 1
                if len(buff) != 0:
                    self.buffer(buff)
                    buff = b''
                return


            if len(buff) - last_len > rest:
                self.error_counter.recv_error += 1

                return
            self.progress.go(len(buff) - last_len)

            if self.progress.go_inc >= self.progress.length:
                self.buffer(buff[:self.progress.length - self.progress.done_inc - len(self.buff)])
                self.close()
                break
            elif len(buff) >= MAX_BUFFER_SIZE:
                self.buffer(buff)
                buff = b''



    def close(self):
        self.progress.globalprog.checkAllGoEnd()
        self.opareq.clear()
        msg = 'Close: '
        extra = {'progress': '%-10d-%10d' % (self.progress.begin, self.progress.end),
                 'urlid': self.urlid}
        logger.info(msg, extra=extra)

    def pause(self):
        self.opareq.pause = True

    def getPause(self):
        # with self.__opa_lock__:
        self.progress.status.pause()
        self.opareq.pause = False


    def getWait(self):
        time.sleep(self.opareq.wait)

    def getSwitch(self):

        next_urlid = self.getHandler().url.getNextId()
        self.loadUrl(next_urlid)

        self.error_counter.clear()

    def buffer(self, buff):
        with self.__buff__lock__:
            self.buff += buff
            self.progress.globalprog.checkBuffer(len(buff))

    # def isOnline(self):
    #     return self.__thread__ and self.__thread__.isAlive()

    def isGoEnd(self):
        return self.progress.isGoEnd()

    def cutRequest(self, Range):

        last_range = [self.progress.begin, self.progress.end]

        self.opareq.cut = [Range[0], Range[1]]

        msg = 'CutRequest: %010d-%010d' % (Range[0], Range[1])
        extra = {'progress': '%-10d-%10d' % (self.progress.begin, self.progress.end),
                 'urlid': self.urlid}
        logger.info(msg, extra=extra)

        while True:
            if not self.isReady() or not self.opareq.cut:
                break
            time.sleep(0.1)

        return [self.progress.end, last_range[1]] if last_range[1] != self.progress.end else []


    def getCut(self):
        while self.progress.begin + self.progress.go_inc >= self.opareq.cut[0]:
            self.opareq.cut[0] += self.progress.globalprog.handler.file.BLOCK_SIZE

        if self.opareq.cut[0] >= self.opareq.cut[1]:
            retrange = []
        else:
            retrange = self.opareq.cut
        # retrange = [] if self.opareq.cut[0] >= self.opareq.cut[1] else self.opareq.cut

        if retrange:
            self.progress.globalprog.cut(self.progress, retrange)

        msg = 'GetCut: %010d-%010d' % (self.opareq.cut[0], self.opareq.cut[1])
        extra = {'progress': '%-10d-%10d' % (self.progress.begin, self.progress.end),
                 'urlid': self.urlid}
        logger.info(msg, extra=extra)

        self.opareq.cut = []


def parse_headers(http_msg):

    http_msg = bytes.decode(http_msg)
    status_bar = http_msg[:http_msg.index('\r\n') + 2]
    status = int(status_bar.split(' ')[1])

    header = http_msg[http_msg.index('\r\n') + 2:]

    res_headers = []

    for i in header.split('\r\n'):
        if i:
            name = i[:i.index(':')].lower().strip()
            value = i[i.index(':') + 1:].lstrip()
            res_headers.append((name, value))

    return status, res_headers
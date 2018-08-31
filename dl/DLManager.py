
from progress import *
from TaskAssign import TaskAssign
import os
import socket,ssl
import DLInformation

# RETRY_WAIT_TIME = 10
# MAX_BUFFER_SIZE = 5 * 1024 * 1024

class DLManager(object):

    DEFAULT_THREAD_NUM = 5

    def __init__(self, urls, file):

        self.urls = urls
        self.file = file
        self.GlobalProg = GlobalProgress(self, self.urls, self.file)
        self.task = TaskAssign(self, self.GlobalProg, self.urls, self.file)

        self._fix_count = 0
        self.__write_lock = threading.Lock()
        self.auto_assign_thread = None

    def __release_buffer(self, buff, _progress):
        if _progress.GlobalProg.save is True:
            self.__buffer_to_file(buff, _progress, _progress.begin + _progress.increment)
        else:

            _progress.buffer_piece[_progress.begin + _progress.increment] = buff
            _progress.done(len(buff))

        _progress.increment += len(buff)

    def __buffer_to_file(self, buff, _progress, startPos):
        with self.__write_lock:
            with open(os.path.join(self.file.path, self.file.name + '.download'), 'rb+') as f:
                f.seek(startPos)
                f.write(buff)
                _progress.done(len(buff))

    def __build_download(self, url, _range):
        if url is None or None in _range:
            return
        if _range[0] == _range[1]:
            return
        _prog = self.GlobalProg.enqueue(url, _range)
        self.launch(_prog)

    def launch(self, _progress):
        if _progress.url.retry_count >= 3:
            if _progress.url.retry_count >= 10:
                self.pause()
                _progress.url.dead = True
                return
            _progress.url.reload()

        with _progress.url.reload_lock:
            if _progress.url.dead is True:
                self.__switch_url(_progress)
            with _progress.lock:
                if _progress.thread is None or _progress.thread.isAlive() is False:
                    thd = threading.Thread(target=self.__getdata__, args=(_progress, _progress.url))
                    _progress.thread = thd
                    thd.start()

    def __retry__(self, _progress):

        if _progress.GlobalProg.save is True:
            _progress.status.retry_count += 1
            if _progress.status.retry_count >= 5:
                self.__switch_url(_progress)

        self.launch(_progress)

    def __switch_url(self, _progress):

        _progress.url = self.urls[(self.urls.index(_progress.url) + 1) % len(self.urls)]
        if _progress.url.dead is True:
            self.__switch_url(_progress)

    def __getdata__(self, _progress, url=None, MaxBuffSize=1024 * 1024 * 5):

        _progress.wait.acquire()
        if self.GlobalProg.status.pauseFlag is True:
            return
        if url is None:
            url = _progress.url
        _empty_count = 0
        sock = None
        ip = socket.gethostbyname(url.host)
        if url.protocol == 'https':
            sock = ssl.wrap_socket(socket.socket())
        elif url.protocol == 'http':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        assert sock is not None
        sock.settimeout(5)
        try:
            sock.connect((ip, url.port))
            packet = 'GET %s HTTP/1.1\r\n' % url.path + \
                     'Host: {0}\r\n'.format(url.host) + \
                     'Connection: keep-alive\r\n' + \
                     'User-Agent: Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36\r\n' + \
                     'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\n' + \
                     'Accept-Encoding: gzip, deflate, br\r\n' + \
                     'Accept-Language: zh-CN,zh;q=0.9\r\n' + \
                     'Range: bytes=%d-%d' % (_progress.begin + _progress.go_inc, _progress.end) + \
                     '\r\n\r\n'
            sock.send(packet)
            buff = sock.recv(1024)
        except:
            # CONNECT TIME OUT EXCEPTION.
            time.sleep(3)
            url.retry_count += 1
            try:
                sock.shutdown(socket.SHUT_RDWR)
            except:
                # print '[Errno 10057]'
                pass
            self.__retry__(_progress)
            return

        if not buff:
            url.retry_count += 1
            sock.shutdown(socket.SHUT_RDWR)
            time.sleep(3)
            self.__retry__(_progress)
            return

        url.retry_count = 0
        # _progress.status.empty_count = 0

        while '\r\n\r\n' not in buff:
            buff += sock.recv(512)
            if 'HTTP' not in buff:
                sock.shutdown(socket.SHUT_RDWR)
                time.sleep(2)
                self.__retry__(_progress)
                return

        _headers = buff[:(buff.index('\r\n\r\n'))]
        _status, _headers_dict = self.parse_HTTPMessage(_headers)

        if _status == 302:
            url.reload_validate(_headers_dict['location'])
            sock.shutdown(socket.SHUT_RDWR)
            self.__retry__(_progress)
            return
        elif _status == 404:
            sock.shutdown(socket.SHUT_RDWR)
            time.sleep(3)
            self.__retry__(_progress)
            return
        elif _status != 206:
            sock.shutdown(2)
            time.sleep(5)
            self.__retry__(_progress)
            return


        buff = buff[(buff.index('\r\n\r\n') + 4):]


        if _progress.length < len(buff):
            buff = buff[:_progress.length]

        _progress.go(len(buff))

        while True:

            if self.GlobalProg.status.pauseFlag is True:
                if buff:
                    self.__release_buffer(buff, _progress)
                return
            _progress.wait.acquire()
            _last_buff_len = len(buff)
            try:
                rest = _progress.length - _progress.go_inc
                if rest == 0:
                    if len(buff) != 0:
                        self.__release_buffer(buff, _progress)
                    break
                elif rest < 10240:
                    buff += sock.recv(rest)
                else:
                    buff += sock.recv(10240)

                if len(buff) == _last_buff_len:
                    _empty_count += 1
                    if _empty_count >= 5:
                        sock.shutdown(socket.SHUT_RDWR)
                        time.sleep(3)
                        if len(buff) != 0:
                            self.__release_buffer(buff, _progress)
                            buff = ''
                        self.__retry__(_progress)
                        return
                if len(buff) - _last_buff_len > rest:
                    buff = buff[:_last_buff_len + rest]

                _progress.go(len(buff) - _last_buff_len)
            except Exception as x:              # Time Out

                sock.shutdown(socket.SHUT_RDWR)
                buff = buff[:_last_buff_len]
                self.__release_buffer(buff, _progress)
                buff = ''
                if _progress.increment + len(buff) != _progress.length:
                    time.sleep(3)
                    self.__retry__(_progress)
                    return
                else:
                    break
            # WHEN THE BUFFER IS FULL, WRITE AND CLEAR.
            if len(buff) >= MaxBuffSize:
                self.__release_buffer(buff, _progress)
                buff = ''
            elif _progress.go_inc >= _progress.length:
                buff = buff[:_progress.length - _progress.increment]
                self.__release_buffer(buff, _progress)
                break
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass


    def parse_HTTPMessage(self, HTTPmsg):

        headers_dict = {}
        _headers = HTTPmsg.split('\r\n')
        _status = int(_headers[0].split(' ')[1])

        for i in _headers[1:]:
            if i == '':
                continue
            _name = i[:i.index(':')].lower().strip()
            _value = i[i.index(':') + 1:].lstrip()

            if headers_dict.has_key(_name) is True:
                headers_dict[_name] = headers_dict[_name] + ';\r\n\r\n' + _value
            else:
                headers_dict[_name] = _value

        return _status, headers_dict

    def getinsSpeed(self):
        return self.GlobalProg.getinsSpeed()

    def getavgSpeed(self):
        return self.GlobalProg.getavgSpeed()

    def getLeft(self):
        return self.GlobalProg.getLeft()

    def __auto_AssignTask_(self):
        while True:
            if self.GlobalProg.status.pauseFlag is True:
                break
            if self.__isDone() is True:
                # print self.GlobalProg.queue.keys()
                # print self.GlobalProg.map
                if self.file.closed is False:
                    if self.file.VERIFY is True:
                        if self._fix_count != 0:
                            if self.verify_file() is False:
                                raise NotImplementedError('Failed to fix the file')
                            self.__close()
                        else:
                            if self.verify_file() is True:
                                self.__close()

                    else:
                        self.__close()
                    break
                else:
                    break
            elif self.GlobalProg.retry_wait.locked() is False:
                if len(self.GlobalProg.queue) == 0:
                    for i in range(len(self.urls)):

                        _url, _range = self.task.assign()
                        self.__build_download(_url, _range)
                else:
                    if self.file.MAX_THREAD > self.GlobalProg.getRuningQuantity():
                        # if self.getLeft() / self.file.size < 0.5:
                        _url, _range = self.task.assign()
                        self.__build_download(_url, _range)
            time.sleep(2)

    def start(self):

        if self.isRuning():
            return
        if self.GlobalProg.status.endFlag_go is False:
            if self.GlobalProg.status.pauseFlag is False:
                self.file.make_file()
                self.auto_assign_thread = threading.Thread(target=self.__auto_AssignTask_)
                self.auto_assign_thread.start()
                # self.GlobalProg.launch_monitor()
            else:

                self.GlobalProg._continue()
                self.auto_assign_thread = threading.Thread(target=self.__auto_AssignTask_)
                self.auto_assign_thread.start()
                # self.GlobalProg.launch_monitor()

        self.GlobalProg.status.pauseFlag = False

    def isDone(self):
        """return weather is running or not"""
        return self.GlobalProg.status.endFlag_done and self.file.closed

    def __isDone(self):
        return self.GlobalProg.status.endFlag_done

    def pause(self):

        threading.Thread(target=self.__pause).start()

    def __pause(self):
        if self.GlobalProg.status.endFlag_go is False:
            self.GlobalProg.pause()
            self.save()

    def isRuning(self):

        if self.GlobalProg.monitor is None:
            return False
        return self.GlobalProg.monitor.isAlive()

    def add_url(self):
        pass

    def __close(self):
        _name = unicode(self.file.name)
        _path_name = unicode(os.path.join(self.file.path, self.file.name))

        _count = 0
        if not self.file.force:
            self.file.validate_name()
        else:
            if os.path.exists(os.path.join(self.file.path, self.file.name)) is True:
                os.remove(os.path.join(self.file.path, self.file.name))
        os.rename(os.path.join(self.file.path, _name) + u'.download',
                  os.path.join(self.file.path, self.file.name))
        self.file.close()
        if os.path.exists(os.path.join(self.file.path, self.file.name + u'.db')) is True:
            os.remove(os.path.join(self.file.path, self.file.name + u'.db'))

    def verify_urls(self, sample_size=1024):
        if len(self.urls) == 1:
            return True

        import random
        _begin = random.randint(0, self.file.size - sample_size)
        _range = [_begin, _begin + sample_size]
        _Global_prog = GlobalProgress(self, self.urls, self.file, False)
        for index, value in enumerate(self.urls):
            _prog = _Global_prog.enqueue(value, _range)
            self.launch(_prog)

        while True:
            if _Global_prog.isDone() is True:
                break
            time.sleep(0.1)
        _box_buff = []
        for i in _Global_prog.queue.values():
            _box_buff.append(i.merge_buffer_piece())
        _one = _box_buff[0]
        for i in _box_buff[1:]:
            if i != _one:
                return False
        return True

    def verify_file(self, url_index=0, fix=False):
        _index = url_index
        _url = self.urls[_index]
        _Global_prog = GlobalProgress(self, self.urls, self.file, False)
        for i in self.GlobalProg.queue.keys():
            _range = [int(j) for j in i.split('-')]
            if _range[1] - _range[0] > 1024:
                _range[0] = _range[1] - 1024
            _prog = _Global_prog.enqueue(_url, _range)
            self.launch(_prog)
        while True:
            if _Global_prog.isDone() is True:
                break
            time.sleep(1)
        _damage = []

        with open(os.path.join(self.file.path, self.file.name + u'.download'), 'rb') as f:
            for i, j in _Global_prog.queue.items():
                _range = [int(k) for k in i.split('-')]
                f.seek(_range[0])
                _file_buf = f.read(_range[1] - _range[0])
                _buff = j.merge_buffer_piece()
                if _file_buf[:1024] != _buff[:1024]:
                    print len(_file_buf), len(_buff)
                    _damage.append(_range)
        # print 'damage_list: ', _damage
        if _damage:
            if fix is False:
                return False
            else:
                _damage_prog = []
                for i, j in enumerate(_damage):
                    _prog = self.GlobalProg.get_parent_prog(j)
                    _damage_prog.append(_prog)
                self.__fix__(_damage_prog)
        else:
            return True

    def __fix__(self, _damage_prog):
        self._fix_count += 1
        for i in _damage_prog:
            i.re_init()
            self.launch(i)

        self.auto_assign_thread = threading.Thread(target=self.__auto_AssignTask_)
        self.auto_assign_thread.start()

    def dump(self):
        _url_dump = []
        for i in self.urls:
            _url_dump.append(i.dump())
        _dump_dict = dict(
            url=_url_dump,
            file=self.file.dump(),
            GlobalProg=self.GlobalProg.dump()
        )
        return _dump_dict

    def save(self):
        import cPickle

        with open(os.path.join(self.file.path, self.file.name + u'.db'), 'wb') as f:
            cPickle.dump(self.dump(), f, protocol=cPickle.HIGHEST_PROTOCOL)

    @staticmethod
    def load(_data):
        _urls = []
        for i in _data['url']:
            _urls.append(DLInformation.URLinfo.load(i))

        dlm = DLManager(_urls, DLInformation.FileInfo.load(_data['file']))

        dlm.GlobalProg.activate(_data['GlobalProg'])

        return dlm


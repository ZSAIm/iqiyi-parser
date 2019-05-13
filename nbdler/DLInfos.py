# -*- coding: UTF-8 -*-

from wsgiref.headers import Headers
import re, time
from .packer import Packer
import threading
import socket
import sys
from .DLError import DLUrlError
import traceback
from . import DLCommon as cv

if sys.version_info >= (3, 0):
    from http.client import HTTPResponse
    from http.cookiejar import CookieJar
    from urllib.parse import splittype, splithost, splittype, splitport
    from urllib.request import build_opener, Request, HTTPCookieProcessor
    from urllib.error import URLError, HTTPError
    from ssl import SSLError

elif sys.version_info <= (2, 7):
    from cookielib import CookieJar
    from urllib import splittype, splithost, splittype, splitport
    from urllib2 import Request, build_opener, HTTPCookieProcessor, URLError
    from ssl import SSLError



def content_type(type):
    dict = {
        'application/octet-stream': '',
        'image/tiff': '.tif',
        'text/asp': '.asp',
        'text/html': '.html',
        'image/x-icon': '.ico',
        'application/x-ico': '.ico',
        'application/x-msdownload': '.exe',
        'video/mpeg4': '.mp4',
        'audio/mp3': '.mp3',
        'video/mpg': '.mpg',
        'application/pdf': '.pdf',
        'application/vnd.android.package-archive': '.apk',
        'application/vnd.rn-realmedia-vbr': '.rmvb',
        'application/vnd.rn-realmedia': '.rm',
        'application/vnd.ms-powerpoint': '.ppt',
        'application/x-png': '.png',
        'image/jpeg': '.jpg',
        'application/x-jpg': '.jpg',
        'application/x-bmp': '.bmp',
        'application/msword': '.doc',
        '': '',
    }
    return dict[type] if type in dict.keys() else ''


# DEFAULT_MAX_THREAD = 5
# DEFAULT_MAX_CONNECTIONS = 16
ERR_4XX_RETRY = 3

HEADERS_CHROME = Headers([
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36'),
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
    ('Accept-Encoding', 'gzip, deflate, br'),
    ('Accept-Language', 'zh-CN,zh;q=0.9')
])

class UrlPool(Packer, object):
    def __init__(self, parent, max_retry=-1, max_conn=1, max_speed=-1):
        self.parent = parent
        # self.list = []
        self._url_box = {}

        self._mapid = []

        self.max_conn = max_conn
        self.max_speed = max_speed

        self.max_retry = max_retry



    def reloadAll(self):
        if not self._url_box:
            return False
        for i in self._url_box.values():
            if self.load_url(i):
                self._mapid[self.getUrlId(i)] = True
                self.parent.file.updateFromUrl(urlobj)
                break
        else:
            return False
        return True


    def addNode(self, id=-1, url='', cookie='', headers=HEADERS_CHROME,
            host=None, port=None, path=None, protocol=None,
            proxy=None, max_thread=-1, range_format='Range: bytes=%d-%d'):

        if id == -1 or id is None:
            id = self.newId()

        urlobj = Url(id, url, cookie, headers, host, port, path, protocol, proxy, max_thread, range_format)
        if urlobj in self._url_box.values():
            return

        self._url_box[id] = urlobj
        try:
            if self.load_url(urlobj):
                self._mapid[id] = True
                self.parent.file.updateFromUrl(urlobj)
        except DLUrlError as e:
            if not self.reloadAll():
                raise


    def load_url(self, urlobj):
        retry_counter = self.max_retry
        counter_4xx = 0
        while True:
            if self.max_retry == -1 or retry_counter > 0:

                res = urlobj.activate()
                if isinstance(res, HTTPResponse):
                    break
                if isinstance(res, HTTPError):
                    if res.code >= 400 and res.code < 500:
                        counter_4xx += 1
                        if counter_4xx > ERR_4XX_RETRY or counter_4xx >= self.max_retry:
                            if self.parent.file.size == -1 and len(self.parent.threads.getAll(cv.ADDNODE)) <= 1:
                                _except = DLUrlError(self.parent, res)
                                self.parent.globalprog.raiseUrlError(_except)
                            return False

                if self.parent.status.pausing():
                    break
                if retry_counter != -1:
                    retry_counter -= 1
                    continue
                time.sleep(0.1)

            else:
                _except = DLUrlError(self.parent, Exception('MaxRetryExceed', 'UrlNotRespond'))
                self.parent.globalprog.raiseUrlError(_except)
                return False
        return True

    def getAllId(self):
        return self._mapid


    def getUrlId(self, Url):
        for i, j in self._url_box.items():
            if j == Url:
                return i

        return None


    def getNextId(self, cur_id):

        next_id = cur_id + 1
        while True:
            if next_id == cur_id:
                raise Exception('NoUrlToSwitch', 'NoValidUrl')
            if next_id >= len(self._mapid):
                next_id = 0
            if self._mapid[next_id]:
                break
            else:
                next_id += 1
        return next_id

    def getAllUrl(self):
        return self._url_box

    def getUrl(self, Urlid):
        return self._url_box[Urlid]

    def hasUrl(self, Url):
        return Url in self._url_box.keys()

    def newId(self):
        for i, j in enumerate(self._mapid):
            if not j:
                return i
        else:
            self._mapid.append(False)
            return len(self._mapid) - 1

    def delete(self, id):
        # for i, j in enumerate(self.list):
        #     if j.id == id:
        #         del self.list[i]
        #         break

        del self._url_box[id]
        self._mapid[id] = False

    # def getContentSize(self, index=0):
    #     if not self.list:
    #         return -1
    #
    #     return int(self.list[index].getContentSize())

    # def getFileName(self, index=0):
    #     if not self.list:
    #         return None
    #     return self.list[index].getFileName()


    def __packet_params__(self):
        return ['dict', 'id_map', 'max_conn', 'max_speed']

    def unpack(self, packet):
        Packer.unpack(self, packet)

        for i, j in self._url_box.items():
            url = Url(-1, '')
            url.unpack(j)
            self._url_box[i] = url
        # for i, j in enumerate(self.list[:]):
        #     self.list[i] = j


class Target(object):
    def __init__(self, url=None, headers=None):
        self.url = None
        self.protocol = self.host = self.port = self.path = None
        self.headers = None

        self.conn = None
        self.resp = None

        self.code = None

        if self.url:
            self.update(url, headers)

    def load(self, url):
        self.url = url

        self.protocol, s1 = splittype(self.url)
        s2, self.path = splithost(s1)
        self.host, port = splitport(s2)
        self.port = int(port) if port is not None else None

        if not self.port:
            if self.protocol == 'http':
                self.port = 80
            elif self.protocol == 'https':
                self.port = 443

        # self.headers = None

    def update(self, url=None, headers=None, code=None):
        if url:
            self.load(url)
        if headers:
            self.headers = Headers(headers)
        if code:
            self.code = code


class Url(Packer, object):
    def __init__(self, id, url, cookie='', headers=HEADERS_CHROME,
                 host=None, port=None, path=None, protocol=None,
                 proxy=None, max_thread=-1, range_format='Range: bytes=%d-%d'):

        self.id = id

        self.url = url

        self.host = host if host is not None else getattr(self, 'host', None)
        self.port = port if port is not None else getattr(self, 'port', None)

        self.path = path if path is not None else getattr(self, 'path', None)
        self.protocol = protocol if protocol is not None else getattr(self, 'protocol', None)

        self.cookie = cookie

        if isinstance(headers, Headers):
            self.headers = headers
        elif isinstance(headers, dict):
            self.headers = Headers(list(headers.items()))
        else:
            raise ValueError('headers must be an instance of dict or Headers')

        self.etag = None

        self.proxy = proxy
        self.target = Target()

        self.max_thread = max_thread

        self.range_format = range_format

    def __eq__(self, other):
        if isinstance(other, Url):
            return self.url == other.url and \
                self.cookie == other.cookie and \
                self.proxy == other.proxy and \
                self.range_format == other.range_format
        else:
            object.__eq__(self, other)

    def config(self):
        pass

    def getContentSize(self):
        if self.target.code == 200 and int(self.target.headers.get('Content-Length', -1)) != -1:
            return int(self.target.headers.get('Content-Length'))
        elif self.target.code == 206 and self.target.headers.get('Content-Range'):
            return int(self.target.headers.get('Content-Range').split('/')[-1])
        else:
            return -1

    def getFileName(self):

        ctd = self.target.headers.get('Content-Disposition')
        if ctd is not None:
            filename = re.findall(r'filename="(.*?)"', ctd)
            if filename:
                return filename[0]

        filename = self.path.split('?')[0].split('/')[-1]

        if filename != '':
            if '.' not in filename or filename.split('.')[-1] == '':

                extension = content_type(self.target.headers.get('Content-Type'))
                filename = filename + extension

        else:
            filename = None

        return filename

    def reload(self):
        self.target.load(self.url)

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'url':
            self.protocol, s1 = splittype(self.url)
            if s1:
                s2, self.path = splithost(s1)
                if s2:
                    self.host, port = splitport(s2)
                    self.port = int(port) if port is not None else None

            if not getattr(self, 'port', None):
                if self.protocol == 'http':
                    self.port = 80
                elif self.protocol == 'https':
                    self.port = 443

    def activate(self):
        res, cookie_dict = self.__request__()
        # if res.getcode() == 200 or res.getcode() == 206:
        if not res:
            return None
        if not isinstance(res, HTTPResponse):
            return res

        headers_items = ()
        if sys.version_info < (3, 0):
            headers_items = res.info().items()

        if sys.version_info >= (3, 0):
            headers_items = res.getheaders()
        self.target.update(res.geturl(), headers_items, res.getcode())
        return res
        # else:
        #     raise Exception('UrlNoRespond or UrlError')


    def __request__(self):

        Cookiejar = CookieJar()
        opener = build_opener(HTTPCookieProcessor(Cookiejar))
        _header = dict(self.headers.items())
        if self.cookie:
            _header.update({'Cookie': self.cookie})
        req = Request(self.url, headers=_header, origin_req_host=self.host)

        res = None

        try:
            res = opener.open(req)
            # break
        except HTTPError as e:
            # if e.code >= 400 and e.code < 500:
            return e, None

        except (socket.timeout, URLError) as e:
            return e, None
        except Exception as e:
            traceback.print_exc()
            return e, None

        return res, Cookiejar._cookies

    def getHeader(self, name, default=None):
        return self.headers.get(name, default)

    def __packet_params__(self):
        return ['id', 'url', 'host', 'port', 'protocal', 'cookie',
                'etag', 'proxy', 'max_thread', 'range_format', 'headers']



import os

class File(Packer, object):
    def __init__(self, parent, name='', path='', size=-1, block_size=1024*1024):
        self.parent = parent
        self.path = path

        self.name = name
        if name:
            self.name = self.checkName()

        self.extension = ''

        self.size = size

        self.BLOCK_SIZE = block_size

        self.buffer_size = 20 * 1024 * 1024

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'name':
            self.extension = self.name[self.name.rindex('.'):] if '.' in self.name else ''

    def makeFile(self, withdir=True):
        # thrs = self.parent.thrpool.getThreads('Nbdler-AddNode')
        # if len(thrs) == 1 and self.size == -1:
        #     thrs[0].join()
        #     if self.parent.is_shutdown():
        #         return False
        #
        # else:
        #     while len(self.parent.thrpool.getThreads('Nbdler-AddNode')):
        #         if self.size != -1:
        #             break
        #         if self.parent.is_shutdown():
        #             return False
        #         time.sleep(0.01)
        #
        # if self.size == -1:
        #     return False

        if withdir:
            try:
                if self.path and not os.path.exists(self.path):
                    os.makedirs(self.path)
            except FileExistsError:
                pass
        else:
            if not os.path.exists(self.path):
                raise Exception('DirNoFound', self.path)

        with open(os.path.join(self.path, self.name), 'wb') as f:
            if self.size == 0:
                f.write(b'\x00')
                # return
            else:
                f.seek(self.size - 1)
                f.write(b'\x00')
        return True

    def checkName(self):

        if not os.path.isfile(os.path.join(self.path, self.name)):
            return self.name

        tag_counter = 1
        while True:
            _name = '%s(%d)%s' % (self.name[:len(self.name)-len(self.extension)],
                                      tag_counter, self.extension)
            if not os.path.isfile(os.path.join(self.path, _name)):
                return _name

            tag_counter += 1

    def __packet_params__(self):
        return ['path', 'name', 'size', 'BLOCK_SIZE', 'buffer_size']

    def __del__(self):
        # self.fp.close()
        pass

    def updateFromUrl(self, Url):
        if self.size == -1:
            self.size = Url.getContentSize()
        if not self.name:
            self.name = Url.getFileName()
            self.name = self.checkName()



import io


def segToRange(seg):
    range_str = seg.split('-')
    return int(range_str[0]), int(range_str[1])



class FileStorage(object):
    def __init__(self):
        self._segs = {}

        self.startpos = 0
        self.offset = 0
        self.closed = False

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def insert(self, begin, end):
        if self.getParent(begin):
            raise Exception('SegsExistAlready')
        self._segs['%d-%d' % (begin, end)] = io.BytesIO()

    def read(self, n=-1):
        seg = self.check()
        Range = segToRange(seg)
        self._segs[seg].seek(self.offset - Range[0], self.startpos)

        return self._segs[seg].read(n)

    def write(self, s):
        seg = self.check()
        Range = segToRange(seg)

        if self.startpos - Range[0] + self.offset > Range[1]:
            raise Exception('PositionExceed: self.startpos - Range[0] + self.offset > Range[1]',
                            self.startpos - Range[0] + self.offset, Range[1])

        self._segs[seg].seek(self.offset - Range[0], self.startpos)
        self._segs[seg].write(s)

        self.offset += len(s)


    def getParent(self, pos):
        for i, j in self._segs.items():
            _range = segToRange(i)
            if pos >= _range[0] and pos < _range[1]:
                retrange = i
                break
        else:
            return None

        return retrange

    def seek(self, offset, whence=None):

        if whence is not None:
            self.startpos = whence

        self.offset = offset

        self.check()

    def check(self):
        seg = self.getParent(self.startpos + self.offset)
        if not seg:
            raise Exception('PositionExceed')

        return seg


    def close(self):
        for i in self._segs.values():
            i.close()
            del i

        self.closed = True

    def getStorageSize(self):
        size = 0
        for i in self._segs.values():
            size += len(i.getvalue())

        return size

    def getvalue(self):
        retvalue = {}
        for i, j in self._segs.items():
            retvalue[i] = j.getvalue()

        return retvalue


    def __del__(self):
        self.close()


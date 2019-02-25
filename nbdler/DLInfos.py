# -*- coding: UTF-8 -*-

import sys
if sys.version_info >= (3, 0):
    import http.cookiejar as cookiejar
    import urllib.parse as urllib_parse
    import urllib.request as urllib_request

if sys.version_info < (3, 0):
    import cookielib as cookiejar
    import urllib as urllib_parse
    import urllib2 as urllib_request

from wsgiref.headers import Headers
import re,time

from packer import Packer
import threading

def _content_type(type):
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


DEFAULT_MAX_THREAD = 5
DEFAULT_MAX_CONNECTIONS = 16

HEADERS_CHROME = Headers([
    ('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36'),
    ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'),
    ('Accept-Encoding', 'gzip, deflate, br'),
    ('Accept-Language', 'zh-CN,zh;q=0.9')
])

class UrlPool(Packer, object):
    def __init__(self, max_conn=DEFAULT_MAX_CONNECTIONS, max_speed=-1):
        self.list = []
        self.dict = {}

        self.id_map = []

        self.max_conn = max_conn
        self.max_speed = max_speed

    def addNode(self, id=-1, url='', cookie='', headers=HEADERS_CHROME,
            host=None, port=None, path=None, protocol=None,
            proxy=None, max_thread=-1):

        if not url:
            return False
        if id == -1 or id == None:
            id = self.newID()

        urlobj = Url(id, url, cookie, headers, host, port, path, protocol, proxy, max_thread)
        try:
            urlobj.activate()
        except Exception:
            return False
        else:
            self.list.append(urlobj)
            self.dict[id] = urlobj
            self.id_map[id] = True
            return True

    def getNextId(self, cur_id):

        next_id = cur_id + 1
        while True:
            if next_id == cur_id:
                raise Exception('NoUrlToSwitch', 'NoValidUrl')
            if next_id >= len(self.id_map):
                next_id = 0
            if self.id_map[next_id]:
                break
        return next_id

    def getUrls(self):
        return self.dict

    def getUrl(self, Urlid):
        return self.dict[Urlid]

    def hasUrl(self, url):
        return url in self.dict.keys()

    def newID(self):
        for i, j in enumerate(self.id_map):
            if not j:
                return i
        else:
            self.id_map.append(False)
            return len(self.id_map) - 1

    def delete(self, id):
        for i, j in enumerate(self.list):
            if j.id == id:
                del self.list[i]
                break

        del self.dict[id]
        self.id_map[id] = False

    def matchSize(self):
        if not self.list:
            raise Exception('EmptyUrlpool')

        content_length = int(self.list[0].target.headers.get('Content-Length', -1))


        for i in self.list[1:]:
            if int(i.target.headers.get('Content-Length', -1)) != content_length:
                return False

        return True

    def getFileSize(self):
        if not self.matchSize():
            raise Exception('FileSizeNoMatch')

        content_length = int(self.list[0].target.headers.get('Content-Length', -1))

        return content_length


    def getFileName(self, index=0):
        if not self.list:
            return None

        ctd = self.list[index].target.headers.get('Content-Disposition')
        if ctd is not None:
            filename = re.findall(r'filename="(.*?)"', ctd)
            if filename:
                return filename[0]

        _urlpath = self.list[0].path

        filename = _urlpath.split('?')[0].split('/')[-1]

        if filename != '':
            if '.' not in filename or filename.split('.')[-1] == '':

                extension = _content_type(self.list[index].target.headers.get('Content-Type'))
                filename = filename + extension

        else:
            filename = None

        return filename


    def __packet_params__(self):
        return ['dict', 'id_map', 'max_conn', 'max_speed']

    def unpack(self, packet):
        Packer.unpack(self, packet)

        for i, j in self.dict.items():
            url = Url(-1, '')
            url.unpack(j)
            self.dict[i] = url


class Target(object):
    def __init__(self, url=None, headers=None):
        self.url = None
        self.protocol = self.host = self.port = self.path = None
        self.headers = None

        if self.url:
            self.update(url, headers)

    def load(self, url):
        self.url = url

        self.protocol, s1 = urllib_parse.splittype(self.url)
        s2, self.path = urllib_parse.splithost(s1)
        self.host, self.port = urllib_parse.splitport(s2)

        if not self.port:
            if self.protocol == 'http':
                self.port = 80
            elif self.protocol == 'https':
                self.port = 443

        self.headers = None

    def update(self, url=None, headers=None):
        if url:
            self.load(url)
        if headers:
            self.headers = Headers(headers)


class Url(Packer, object):
    def __init__(self, id, url, cookie='', headers=HEADERS_CHROME,
                 host=None, port=None, path=None, protocol=None,
                 proxy=None, max_thread=-1):

        self.id = id

        self.url = url

        self.host = host if host is not None else getattr(self, 'host', None)
        self.port = port if port is not None else getattr(self, 'port', None)

        self.path = path if path is not None else getattr(self, 'path', None)
        self.protocol = protocol if protocol is not None else getattr(self, 'protocol', None)

        self.cookie = cookie

        self.headers = headers

        self.proxy = proxy
        self.target = Target()

        self.max_thread = max_thread


    def reload(self):
        self.target.load(self.url)

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'url':
            self.protocol, s1 = urllib_parse.splittype(self.url)
            if s1:
                s2, self.path = urllib_parse.splithost(s1)
                if s2:
                    self.host, self.port = urllib_parse.splitport(s2)

            if not getattr(self, 'port', None):
                if self.protocol == 'http':
                    self.port = 80
                elif self.protocol == 'https':
                    self.port = 443

    def activate(self):
        res, cookie_dict = self.__collect__()
        if res.getcode() == 200:
            headers_items = ()
            if sys.version_info < (3, 0):
                headers_items = res.info().items()

            if sys.version_info >= (3, 0):
                headers_items = res.getheaders()

            self.target.update(res.geturl(), headers_items)
        else:
            raise Exception('UrlNoRespond or UrlError')


    def __collect__(self):

        Cookiejar = cookiejar.CookieJar()
        opener = urllib_request.build_opener(urllib_request.HTTPCookieProcessor(Cookiejar))
        _header = dict(self.headers.items())
        if self.cookie:
            _header.update({'Cookie': self.cookie})
        req = urllib_request.Request(self.url, headers=_header, origin_req_host=self.host)
        error_counter = 0
        while error_counter < 5:
            try:
                res = opener.open(req)
                break
            except:
                error_counter += 1
            time.sleep(1)
        else:
            # return None, None
            raise Exception('UrlNotRespond')

        return res, Cookiejar._cookies

    def getHeader(self, name, default=None):
        return self.headers.get(name, default)

    def __packet_params__(self):
        return ['id', 'url', 'host', 'port', 'protocal', 'cookie', 'proxy', 'max_thread', 'headers']



import os

class File(Packer, object):
    def __init__(self, name='', path='', size=-1, block_size=1024*1024):
        self.path = path

        self.name = name
        if name:
            self.name = self.checkName()

        self.extension = ''

        self.size = size

        # self.fp = FileStorage()
        self.BLOCK_SIZE = block_size

        self.buffer_size = 20 * 1024 * 1024

    def __setattr__(self, key, value):
        object.__setattr__(self, key, value)
        if key == 'name':
            self.extension = self.name[self.name.rindex('.'):] if '.' in self.name else ''


    def makeFile(self, withdir=True):
        # self.name = self.checkName()

        if withdir:
            if self.path and not os.path.exists(self.path):
                os.makedirs(self.path)
        else:
            if not os.path.exists(self.path):
                raise Exception('DirNoFound', self.path)

        with open(os.path.join(self.path, self.name), 'wb') as f:
            f.seek(self.size - 1)
            f.write(b'\x00')

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


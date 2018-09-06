# -*- coding: UTF-8 -*-
import httplib, urllib, re, os, threading

def load_attr(obj, data, ignores=[]):
    for i, j in data.items():
        if i not in ignores:
            setattr(obj, i, j)

class URLinfo:
    def __init__(self, url=None, host=None, path=None, port=None, cookie=''):
        self.url = None
        self.host = None
        self.path = None
        self.protocol = None
        self.port = None

        self.cookie = ''
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/66.0.3359.117 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }
        self.res_headers = {}
        self.base_url = None
        self.__history = []

        self.dead = False
        self.retry_count = 0

        self.reload_lock = threading.Lock()

        if url is not None:
            self.base_url = [url, host, path, port, cookie]
            if self.__load(url, host, path, port, cookie) is False:
                raise Exception('UrlError')

    def get_filename(self):
        assert self.url is None

        if self.res_headers.get('content-disposition') is not None:
            filename = re.findall(r'filename="(.*?)"', self.res_headers['content-disposition'])
            if filename != []:
                return filename[0]

        filename = self.path.split('?')[0].split('/')[-1]

        if filename != '':
            if '.' not in filename or filename.split('.')[-1] == '':
                extension = unicode(self.get_type(self.res_headers['content-type']))
                filename = filename + extension
        else:
            filename = None
        return filename

    def add_headers(self, **args):
        for i, j in args.items():
            for k in self.headers.keys():
                if i.lower() == k.lower():
                    self.headers[k] = j
                    break
            else:
                self.headers[i] = j

    def __load(self, url, host=None, path=None, port=None, cookie=''):
        self.protocol, s1 = urllib.splittype(url)
        _host, self.path = urllib.splithost(s1)
        self.host, self.port = urllib.splitport(_host)

        if self.port is None:
            if self.protocol == 'http':
                self.port = 80
            elif self.protocol == 'https':
                self.port = 443

        if host:
            self.host = host
        if path:
            self.path = path
        if port:
            self.port = port

        self.cookie = cookie
        if self.base_url is None:
            self.base_url = [url, host, path, port, cookie]

        if self.host:
            for i in self.__history:
                if url == i[0]:
                    break
            else:
                self.__history.append([url, host, path, port, cookie])
            try:
                self.__get_request()
                if self.res_headers == {}:
                    return False
                else:
                    return True
            except:
                return False
        else:
            return False

    def get_type(self, type):
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
        if type in dict.keys():
            return dict[type]
        return ''

    @staticmethod
    def load(_data):
        urlinfo = URLinfo()
        load_attr(urlinfo, _data)
        urlinfo.reload()

        return urlinfo

    def reload(self):
        with self.reload_lock:
            self.__history = []
            self.__load(self.base_url[0], self.base_url[1], self.base_url[2], self.base_url[3], self.base_url[4])

    def dump(self):
        _dump_dict = dict(
            base_url=self.base_url,
        )

        return _dump_dict

    def __get_request(self):
        _count = 5
        while _count:
            try:
                conn = None
                if self.protocol == 'https':
                    conn = httplib.HTTPSConnection("%s:%s" % (self.host, self.port))
                elif self.protocol == 'http':
                    conn = httplib.HTTPConnection("%s:%s" % (self.host, self.port))

                assert conn is not None
                conn.timeout = 5
                conn.request('GET', self.path, {'cookie': self.cookie}.update(self.headers))
                res = conn.getresponse()
            except:
                _count -= 1
                continue

            self.res_headers = res.msg.dict

            if res.status == 302:
                if res.getheader('location') != self.url:
                    if res.getheader('set-cookie') is not None:
                        self.__load(res.getheader('location'), cookie=res.getheader('set-cookie'))
                    else:
                        self.__load(res.getheader('location'))

                    break
                else:
                    _count -= 1
                    continue

                # 'url seems to be invalid.'
            elif res.status == 405 or res.status == 404 or res.status == 500:
                _count -= 1
                continue
            conn.close()
            break
        else:
            self.res_headers = {}

    def reload_validate(self, url):
        for i in self.__history:
            if url == i[0]:
                self.reload()
                return
        else:
            self.__history.append([url, None, None, None, ''])
        _last_length = self.res_headers['content-length']

        if self.__load(url) is True:
            if self.res_headers['content-length'] != _last_length:
                self.reload()
        else:
            self.reload()


class FileInfo:
    def __init__(self):
        self.path = u''
        self.name = None
        self.size = None

        # self.object = None
        self.exist = False
        self.force = False
        self.closed = False

        self.MAX_THREAD = 5
        self.BLOCK_SIZE = 1024 * 1024
        self.FIX_TRY = True
        self.VERIFY = True


    def make_file(self):

        if self.path is not u'' and not os.path.exists(unicode(self.path)):
            os.makedirs(unicode(self.path))

        with open(os.path.join(unicode(self.path), unicode(self.name + u'.download')), 'wb') as f:
            # print self.size
            f.seek(self.size - 1)
            f.write(b'\x00')

    def validate_name(self):
        _name = unicode(self.name)
        _path = unicode(self.path)

        _count = 0
        while True:
            if _count != 0:
                if u'.' in _name:
                    dot_index = _name.rindex(u'.')
                    if os.path.exists(os.path.join(_path, u'%s(%d)%s' % (_name[:dot_index], _count, _name[dot_index:]))):
                        _count += 1
                        continue
                    self.name = u'%s(%d)%s' % (_name[:dot_index], _count, _name[dot_index:])
                    break
                    # return u'%s(%d)%s' % (_name[:dot_index], _count, _name[dot_index:])

                else:
                    if os.path.exists(os.path.join(_path, u'%s(%d)' % (_name, _count))):
                        _count += 1
                        continue
                    self.name = u'%s(%d)' % (_name, _count)
                    # return u'%s(%d)' % (_name, _count)
                    break
            else:
                if not os.path.exists(os.path.join(_path, self.name)):
                    self.name = _name
                    # return _name
                    break
                else:
                    _count += 1

    def dump(self):
        _dump_dict = dict(
            path=self.path,
            name=self.name,
            size=self.size,
            exist=self.exist,
            force=self.force,
            MAX_THREAD=self.MAX_THREAD,
            BLOCK_SIZE=self.BLOCK_SIZE,
            FIX_TRY=self.FIX_TRY,
            VERIFY=self.VERIFY
        )

        return _dump_dict

    @staticmethod
    def load(_data):
        fileinfo = FileInfo()
        load_attr(fileinfo, _data)
        return fileinfo

    def close(self):
        self.closed = True
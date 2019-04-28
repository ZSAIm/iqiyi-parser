
from io import BytesIO
import gzip, zlib
from urllib.parse import splitvalue, splitquery, urlencode
import socket
from urllib.error import URLError
from ssl import SSLError
import time, re
import CommonVar as cv

def raw_decompress(data, headers_msg):
    encoding = headers_msg.get('Content-Encoding')
    if encoding == 'gzip':
        src_stream = BytesIO(data)
        data = gzip.GzipFile(fileobj=src_stream).read()
    elif encoding == 'deflate':
        data = zlib.decompress(data)
    return data if isinstance(data, str) else data.decode('utf-8')


def extract_query(query_str):
    querys = {}
    for i in query_str.split('&'):
        key_value = splitvalue(i)
        querys[key_value[0]] = key_value[1]

    return querys

def make_query(url, new_query_dict):
    path, query_str = splitquery(url)
    old_query_dict = extract_query(query_str) if query_str else {}
    for i, j in new_query_dict.items():
        old_query_dict[i] = j

    query_str = urlencode(old_query_dict)
    return path + '?' + query_str



from http.cookiejar import CookieJar, Cookie
from urllib.request import build_opener, HTTPCookieProcessor, Request

HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}


CONTENT_TYPE_MAP = {
    'video/mp4': 'mp4'

}

def format_byte(bytes, format='%.2f%s'):
    if bytes > 1024 * 1024 * 1024:
        return format % (bytes / 1024.0 / 1024 / 1024, 'GB')
    elif bytes > 1024 * 1024:
        return format % (bytes / 1024.0 / 1024, 'MB')
    elif bytes > 1024:
        return format % (bytes / 1024.0, 'KB')
    else:
        return format % (bytes, 'B')


def dict_get_key(_dict, value):
    return list(filter(lambda i: i[1] == value, _dict.items()))[0][0]


class BasicParser:
    def __init__(self):
        self.cookiejar = None
        self.cookie_str = None
        self.opener = None
        self.headers = HEADERS
        self.initOpener()

    def initOpener(self):
        self.cookiejar = CookieJar()
        self.opener = build_opener(HTTPCookieProcessor(self.cookiejar))
        self.opener.addheaders = list(self.headers.items())

    def setHeaders(self, headers_dict):
        self.headers = headers_dict
        self.initOpener()

    def setCookie(self, name, value, domain, path):
        self.cookiejar.set_cookie(Cookie(0, name, value, None, False, domain, True, False, path, True, False,
                                                   None, False, None, None, None))

    def loadCookie(self, cookie_str):
        self.cookie_str = cookie_str
        self.headers['Cookie'] = cookie_str
        self.initOpener()

    def requestRaw(self, *args, **kwargs):
        counter = 0
        req = Request(*args, **kwargs)
        while True:
            try:
                time.sleep(0.05)
                res = self.opener.open(req)
            except (socket.timeout, URLError, SSLError):
                counter += 1
                time.sleep(0.3)
                if counter >= 10:
                    raise socket.timeout

                continue

            else:
                break
        return res

    def request(self, *args, **kwargs):
        res = self.requestRaw(*args, **kwargs)
        raw = res.read()
        text = raw_decompress(raw, res.info())
        res.close()
        return text

    def parse(self, *args):
        pass



class BasicRespond:
    def __init__(self, parent, full_json, res_json, extra_info):
        self.parent = parent
        self.full_json = full_json
        self.res_json = res_json
        self.extra_info = extra_info

        self._videosize = -1
        self._audiosize = -1

        self._video_len = -1

        self._target_video_urls = []
        self._target_audio_urls = []

    def __extract__(self, *args):
        pass

    def getVideoUrls(self):
        return []

    def getAudioUrls(self):
        return []

    def getTotalFileSize(self):
        return -1

    def getVideoSize(self):
        return self._videosize

    def getAudioSize(self):
        return self._audiosize

    def getFileFormat(self):
        return 'Unknown'

    def getVideoTitle(self):
        return self.extra_info.title

    def getRangeFormat(self):
        return 'Range: bytes=%d-%d'

    def getBaseUrl(self):
        return self.extra_info.base_url

    def getQuality(self):
        return self.extra_info.quality

    def getScreenSize(self):
        return None

    def getVideoTotal(self):
        return len(self._target_video_urls)

    def getAudioTotal(self):
        return len(self._target_audio_urls)

    def getM3U8(self):
        return None

    def setSelAudio(self, index):
        pass

    def getReqHeaders(self):
        return {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

    def getConcatMerger(self):
        return cv.MERGER_FFMPEG


    def getAllAudioInfo(self):
        return []

    def getVideoTimeLength(self):
        """    ms  """
        return self._video_len




    def getFeatures(self):
        return {
            'quality': self.getQuality(),
            'screensize': self.getScreenSize(),
        }

    def matchFeature(self, feature):
        return feature['quality'] == self.getQuality() and feature['screensize'] == self.getScreenSize()


    def __str__(self):
        return '[%s]-(%s)-(%s)' % (self.getQuality(), self.getScreenSize(), format_byte(self.getTotalFileSize()))


    def getVideoLegalTitle(self):
        return re.sub('[\\/:\?<>\|\*"]', ' ', self.getVideoTitle())


class BasicVideoInfo:
    def __init__(self, base_url, title, quality, **extra_info):
        self.base_url = base_url
        self.title = title
        self.quality = quality
        self.extra_info = extra_info

    def __getattr__(self, item):
        if not hasattr(self, item):
            return self.extra_info[item]
        else:
            return object.__getattribute__(self, item)



class BasicAudioInfo:
    def __init__(self, urls, size, info, **extra_info):
        self.urls = urls
        self.size = size
        self.info = info
        self.extra_info = extra_info

    def __getattr__(self, item):
        if not hasattr(self, item):
            return self.extra_info[item]
        else:
            return object.__getattribute__(self, item)



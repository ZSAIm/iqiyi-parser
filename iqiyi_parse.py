import cookielib
import random
import time
import re
import gzip, zlib
from io import BytesIO
import json
import urllib, urllib2
from BeautifulSoup import BeautifulSoup
import PyV8
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

def raw_decompress(data, headers_msg):
    encoding = headers_msg.get('Content-Encoding')
    if encoding == 'gzip':
        src_stream = BytesIO(data)
        data = gzip.GzipFile(fileobj=src_stream).read()
    elif encoding == 'deflate':
        data = zlib.decompress(data)
    return data

HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'http://www.iqiyi.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9',
}

global_params = {
    'tvid': '',
    'bid': '',
    'vid': '',
    'src': '01010031010000000000',
    'vt': '0',
    'rs': '1',
    'uid': '',
    'ori': "pcw",
    'ps': '0',  # ps: o.switchvd ? 1 : 0,
    'tm': '',
    'qd_v': "1",
    'k_uid': '',
    'pt': '0',
    'd': '0',
    's': "",
    'lid': "",
    'cf': "",
    'ct': "",
    'authKey': '',
    'k_tag': '1',
    'ppt': '0',
    'dfp': '',
    'locale': 'zh_cn',
    'prio': '{"ff": "mp4", "code": 2}',
    'pck': '',
    'k_err_retries': '0',
    'ut': '0',
    'bop': '{"version":"7.0","dfp":""}',
    'callback': '',
}

class Iqiyi:

    def __init__(self):
        self.cookiejar = None
        self.opener = None
        self.QC005 = None
        self.QP001 = '1'
        # self.uid = None
        self.tvid = None
        self.init_opener()

    def init_opener(self):
        self.cookiejar = cookielib.CookieJar()
        self.opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cookiejar))
        self.opener.addheaders = list(HEADERS.items())
        self.QC005 = self.make_random_id()
        # self.uid = self.make_random_id()
        self.set_cookie('QC005', self.QC005, 'iqiyi.com', '/')
        self.set_cookie('QP001', self.QP001, 'iqiyi.com', '/')

    def set_cookie(self, name, value, domain, path):
        self.cookiejar.set_cookie(cookielib.Cookie(0, name, value, None, False, domain, True, False, path, True, False,
                                                   None, False, None, None, None))

    def make_random_id(self):
        chars = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 'a', 'b', 'c', 'd', 'e', 'f']
        id = ""
        for index in range(0, 32):
            id += chars[random.randint(0, 15)]
        return id

    def parse(self, url, bids=[600]):
        """bid = [100, 200, 300, 400, 500, 600]
            mean video resolution. the higher bid the higher definition
            it need a list
            like [600].
        """
        # videoname , tvid
        req = urllib2.Request(url)
        res = self.opener.open(req)
        raw = res.read()
        text = str(raw_decompress(raw, res.info()))

        soup = BeautifulSoup(text)
        videoname = soup.title.string
        tvid = re.search('''param\['tvid'\] = "(.+?)"''', text, re.S).group(1)
        self.tvid = tvid
        vid = re.search('''param\['vid'\] = "(.+?)"''', text, re.I | re.S).group(1)
        uid = self.make_random_id()

        videos_msg = {}

        for bid in bids:
            json_msg = self.__parse(tvid, vid, uid, bid)
            if not json_msg:
                continue
            msg = json_msg['data']['program']['video']

            # scrsz = ''
            sel = None
            for i in msg:
                if 'fs' in i and i['_selected'] is True:
                    sel = i
                    # scrsz = i['scrsz']

                    # for j, k in i:
                    # fs.append(i['fs'])
            videos_msg[sel['scrsz']] = {'fs': sel['fs'], 'vsize': sel['vsize'], 'ff': sel['ff'], 'bid': sel['bid'], '@json': msg}

        return videoname, videos_msg

    def __parse(self, tvid, vid, uid, bid):
        js_context = ''
        with open("ArrayBuffer.js", 'r') as f:
            js_context += f.read()
        with open("pcweb.js", 'r') as f:
            js_context += f.read()

        time_str = str(int(time.time() * 1000))

        ctx = PyV8.JSContext()
        with PyV8.JSLocker():
            ctx.enter()
            ctx.eval(js_context)

            authkey = ctx.locals.authkey(ctx.locals.authkey('') + time_str + tvid)
            callback = ctx.locals.callback()


            params = {
                'tvid': tvid,
                'vid': vid,
                'bid': str(bid),
                'tm': time_str,
                'k_uid': uid,
                'callback': callback,
                'authKey': authkey,
            }

            global_params.update(params)
            params_encode = urllib.urlencode(global_params)

            path_get = '/jp/dash?' + params_encode
            vf = ctx.locals.vf(path_get)

            path_get += '&vf=%s' % vf
            ctx.leave()

        req = urllib2.Request('http://cache.video.iqiyi.com/' + path_get.lstrip('/'))
        res = self.opener.open(req)
        raw = res.read()
        text = raw_decompress(raw, res.info())
        json_str = re.search('try{\w{0,}\((.+})(\s)?\);}catch', text).group(1)
        if json_str:
            ret = json.loads(json_str)
        else:
            ret = None
        res.close()
        return ret

    def activate_path(self, path):
        params = {
            'cross-domain': '1',
            'qyid': self.QC005,
            'qypid': '%s__02020031010000000000' % self.tvid,
            'rn': str(int(time.time() * 1000)),
            'pv': '0.1',

        }
        encode_params = urllib.urlencode(params)

        req = urllib2.Request('http://data.video.iqiyi.com/videos/%s' % path.lstrip('/'), encode_params)
        res = self.opener.open(req)
        raw = res.read()
        text = raw_decompress(raw, res.info())
        msg = json.loads(text)
        return msg['l'], msg

if __name__ == "__main__":
    a = Iqiyi()
    # b = a.parse('http://www.iqiyi.com/a_19rrgxwtfh.html')
    b = a.parse('https://www.iqiyi.com/a_19rrhdfh2l.html')
    pass
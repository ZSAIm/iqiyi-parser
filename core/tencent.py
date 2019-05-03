
import os
from core.common import BasicParser, BasicRespond, BasicVideoInfo, BasicAudioInfo, \
    CONTENT_TYPE_MAP, make_query, dict_get_key, format_byte, BasicUrlGroup
from bs4 import BeautifulSoup
import re
import json
import PyJSCaller
import time
from urllib.parse import splittype, splithost, urlencode, unquote, splitvalue, splitquery
import CommonVar as cv


TENCENT = None
LASTRES = None

HEADERS = {
    'Connection': 'keep-alive',
    'Host': 'vd.l.qq.com',
    'Origin': 'https://v.qq.com',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',

}

QUALITY = {
    1: 'sd',
    2: 'sd',
    3: 'sd',
    4: 'hd',
    5: 'shd',
    6: 'fhd'
}


# adparam = {
#     'url': None,
#     'refer': None,
#     'flowid': None,
#     'vid': None,
#     'guid': None,
#     'coverid': None,                # cid
#
#
#     'pf': 'in',
#     'ad_type': 'LD|KB|PVL',
#     'chid': 0,
#     'pf_ex': 'pc',
#     'ty': 'web',
#     'plugin': '1.0.0',
#     'v': '3.5.57',
#     'adaptor': 2,
#     'dtype': 1,
#     'live': 0,
#     'req_type': 1,
#
#     'pt': '',
#
#     'vptag': '',
#     'pu': 0,
#
#
#     'resp_type': 'json',
#     'from': 0,
#     'appversion': '1.0.139',
#     'platform': '10201',
#     'tpid': '106',
#     # 'rfid': None                    # "TxpCreativePlayer-rfid"
# }

AUTH_REFRESH_URL = 'https://access.video.qq.com/user/auth_refresh?'


logintoken_auth_refresh = {
    'vappid': '11059694',
    'vsecret': 'fdf61a6be0aad57132bc5cdf78ac30145b6cd2c1470b0cfe',

    'type': None,                   # main_login
    # 'callback': 'jQuery19103462876083328801_',
    '_': None,        # str(int(time.time() * 1000))

}




vinfoparam = {
    'encryptVer': '9.1',
    'flowid': None,
    'guid': None,
    'tm': None,
    # 'unid': None,
    'vid': None,
    'cKey': None,

    'charge': 0,
    'otype': 'ojson',
    'sdtfrom': 'v1010',
    'defnpayver': 1,                # 0

    'appVer': "3.5.57",


    'defaultfmt': 'auto',

    'platform': '10201',

    'host': "v.qq.com",

    'ehost': None,              # base_url
    'refer': 'v.qq.com',
    'spwm': 4,


    # https://access.video.qq.com/user/auth_refresh?vappid=11059694&vsecret=fdf61a6be0aad57132bc5cdf78ac30145b6cd2c1470b0cfe
    # &type=qq&callback=jQuery19103462876083328801_1556698604671&_=1556698604672
    'logintoken': {
        "main_login": None,
        "openid": None,
        "appid": None,
        "access_token": None,
        "vuserid": None,
        "vusession": None,
    },


    'sphttps': 1,


    'show1080p': 1,
    'isHLS': 1,


    'dtype': 3,
    'spgzip': 1,
    'dlver': 2,
    'drm': 32,

    'hdcp': 0,
    'spau': 1,
    'spaudio': 15,

    'defn': None,             # '',  1080p: fhd,   270p: sd, 480p: hd, 720p: shd
    'fhdswitch': 1,
    'onlyGetinfo': 'true',

    'defsrc': 2,                # 1
    'fp2p': 1,
    'spadseg': 1,            # "https:" === location.protocol ? 1 : 0,

    'sphls': 2,               # hls m3u8 content in json


    'adsid': '',
    'adpinfo': '"',

}

global_params = {
    'buid': 'vinfoad',
    # 'adparam': adparam,
    'vinfoparam': vinfoparam,

}



class Tencent(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.setHeaders(HEADERS)
        self.user = TencentUser()

    def loadCookie(self, cookie_str):
        BasicParser.loadCookie(self, cookie_str)
        self.user.extract(cookie_str)

    def saveCookie(self, new_cookie_str):
        with open('cookies/tencent.txt', 'w') as f:
            f.write(new_cookie_str)


    def parse(self, url, quality):

        text = self.request(url)
        # bs4 = BeautifulSoup(text, features='html.parser')
        video_info_rex = re.compile('var VIDEO_INFO\s*=\s*({.+?})\s*</script>')


        video_info = json.loads(video_info_rex.search(text).group(1))

        # scripts = bs4.findAll('script')
        title = video_info['title']

        self.auth_refresh()

        res_videos = []
        for i in quality:
            # start = time.time_ns()
            with PyJSCaller.Sesson('./js/tencent.js') as sess:
                getckey, createGUID, setdocument = sess.require('getckey', 'createGUID', 'setdocument')
                setdocument(url)

                s1, s2 = splittype(url)
                host, path = splithost(s2)
                seg_path = path.split('/')

                vid = seg_path[-1].split('.html')[0]

                tm = int(time.time())

                guid = createGUID()
                flowid = createGUID() + '_10201'

                ckey = getckey('10201', '3.5.57', vid, '', guid, tm)
                sess.call(ckey)
                sess.call(flowid)
                sess.call(guid)

            req_globalparams = global_params.copy()


            new_token = {
                "main_login": self.user.main_login,
                "openid": self.user.openid,
                "appid": self.user.appid,
                "access_token": self.user.access_token,
                "vuserid": self.user.vuserid,
                "vusession": self.user.vusession,

            }

            add_vinfoparam = {
                'flowid': flowid.getValue(),
                'ehost': url,
                'vid': vid,
                'tm': tm,
                'cKey': ckey.getValue(),
                'guid': guid.getValue(),
                'defn': i,
                'logintoken': str(new_token).replace("'", '"')
            }

            req_vinfoparam = vinfoparam.copy()
            req_vinfoparam.update(add_vinfoparam)

            req_globalparams['vinfoparam'] = urlencode(req_vinfoparam)

            req_data = str(req_globalparams).replace("'", '"').encode('utf-8')
            text = self.request(method='POST', url='https://vd.l.qq.com/proxyhttp', data=req_data)

            res_json = json.loads(text)
            res_json['vinfo'] = json.loads(res_json['vinfo'])

            res_videos.append(TencentRespond(self, res_json, res_json, BasicVideoInfo(url, title, i)))



        return res_videos


    def auth_refresh(self):
        add_params = logintoken_auth_refresh.copy()
        add_params['_'] = str(int(time.time() * 1000))
        add_params['type'] = self.user.main_login

        new_url = make_query(AUTH_REFRESH_URL, add_params)

        res = self.requestRaw(url=new_url)

        self.user.extract_headers(res.info().get_all('set-cookie'))
        new_cookie_str = self.user.dumps()
        self.saveCookie(new_cookie_str)
        self.loadCookie(new_cookie_str)



class TencentUser:
    def __init__(self):
        self.main_login = ''
        self.openid = ''
        self.appid = ''
        self.access_token = ''
        self.vuserid = ''
        self.vusession = ''

        self.extra_info = {}

    def extract(self, cookie_str):

        eles = cookie_str.split(';')
        for i in eles:
            self.checkQuery(i)

    def checkQuery(self, query):
        key, value = [i.strip() for i in splitvalue(query)]
        if key == 'main_login':
            self.main_login = value
        elif 'openid' in key:
            self.openid = value
        elif 'appid' in key:
            self.appid = value
        elif 'access_token' in key:
            self.access_token = value
        elif 'vuserid' in key:
            self.vuserid = value
        elif 'vusession' in key:
            self.vusession = value
        else:
            self.extra_info[key] = value


    def dumps(self):
        if self.main_login == 'qq':
            add_info = {
                'main_login': self.main_login,
                'vqq_openid': self.openid,
                'vqq_appid': self.appid,
                'vqq_access_token': self.access_token,
                'vqq_vuserid': self.vuserid,
                'vqq_vusession': self.vusession,
            }
        elif self.main_login == 'wx':
            add_info = {
                'main_login': self.main_login,
                'openid': self.openid,
                'appid': self.appid,
                'access_token': self.access_token,
                'vuserid': self.vuserid,
                'vusession': self.vusession,
            }
        else:
            raise AttributeError('unknown "main_login"')

        add_info.update(self.extra_info)
        _list = ['%s=%s' % (i[0], i[1]) for i in add_info.items()]
        return '; '.join(_list)

    def extract_headers(self, headers_list):
        if headers_list:
            for i in headers_list:
                self.checkQuery(i.split(';')[0])





class TencentRespond(BasicRespond):
    def __init__(self, parent, full_json, res_json, extra_info):
        BasicRespond.__init__(self, parent, full_json, res_json, extra_info)
        self.__extract__()
        pass


    def __extract__(self):
        self.program = self.res_json['vinfo']['vl']['vi'][0]

        # target video urls
        m3u8 = self.getM3U8()
        if not m3u8:
            m3u8 = self.parent.request(url=self.program['ul']['ui'][0]['url'])

        m3u8_parts = re.compile('#EXTINF:([\d\.]+),\s+(.+?)\s+').findall(m3u8)

        m3u8_paths = [i[:i.rindex('/') + 1] for i in self.getM3U8Urls()]

        tmp_urls = []
        for i in m3u8_parts:
            tmp_urls.append([j + i[1] for j in m3u8_paths])
        self._target_video_urls = [BasicUrlGroup(tmp_urls)]

        # if


    def getM3U8(self):
        return self.program['ul'].get('m3u8')


    def getM3U8Urls(self):
        return list([i['url'] for i in self.program['ul']['ui']])


    def getVideoSize(self):
        return int(self.program['fs'])


    def getVideoTimeLength(self):
        return float(self.program['td']) * 1000

    # def getReqHeaders(self):
    def getScreenSize(self):
        return '%sx%s' % (self.program['vw'], self.program['vh'])

    def getVideoUrls(self):
        return self._target_video_urls

    def getFileFormat(self):
        return self.program['fn'][self.program['fn'].rindex('.')+1:]

    def getConcatMethod(self):
        return cv.MER_CONCAT_DEMUXER


def init():
    global TENCENT
    TENCENT = Tencent()
    load_cookie()


def load_cookie():
    global TENCENT

    if os.path.exists('cookies/tencent.txt'):
        with open('cookies/tencent.txt', 'r') as f:
            cookie = f.read().strip()

        if cookie:
            TENCENT.loadCookie(cookie)
    else:
        with open('cookies/tencent.txt', 'w'):
            pass


def parse(url, qualitys):
    global TENCENT, QUALITY
    return TENCENT.parse(url, [QUALITY[i] for i in qualitys])



if __name__ == '__main__':
    init()
    # tx = Tencent()
    load_cookie()
    user = TencentUser()

    user.extract(TENCENT.cookie_str)

    res = parse(url, [6])
    print(res[0].getM3U8Url())









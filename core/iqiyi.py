# -*- coding: utf-8 -*-

import time, random
import re
import json, os

from bs4 import BeautifulSoup
from urllib.parse import unquote

import PyJSCaller
from core.common import BasicParser, BasicRespond, BasicVideoInfo, make_query

IQIYI = None


QUALITY = {
    1: 100,
    2: 200,
    3: 300,
    4: 400,
    5: 500,
    6: 600,
}


HEADERS = {
    'Connection': 'keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
    'Accept': '*/*',
    'Referer': 'http://www.iqiyi.com/',
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}

global_params = {
    # discrete data
    'tvid': '',
    'vid': '',
    'src': '01010031010000000000',              # src: n.getPtid(c.isTWLocale()),
    'tm': '',

    # resolution
    'bid': '',

    # invariant
    'vt': '0',
    'rs': '1',
    'ori': "pcw",
    'pt': '0',
    'd': '0',
    'qd_v': "1",
    's': "",
    'lid': "",
    'cf': "",
    'ct': "",
    'k_tag': '1',

    # might change
    'prio': '{"ff": "f4v", "code": 2}',         # prio: u.prio || JSON.stringify({ff: "f4v", code: 2})
    'ps': '1',                                  # ps: o.switchvd ? 1 : 0,

    # verify needed
    'ost': '0',
    'ppt': '0',

    'locale': 'zh_cn',
    'k_err_retries': '0',                       # k_err_retries: S
    'ut': '1',                                  # ut = 0 , 600 bid isn't available


    # encrypt key
    'authKey': '',                              # authKey: r(r("") + L + A),
    'callback': '',
                                                # vf= cmd5x(t.url.replace(new RegExp("^(http|https)://" + i, "ig"), ""))

    # cookie key (not necessary)
    'uid': '',                                  # uid: d.getUid(),
    'dfp': '',                                  # dfp: h.get(),
    'pck': '',                                  # pck: d.passportCookie()
    'k_uid': '',                                # k_uid: l.getFluid() || l.getJsuid(),
                                                # e.bop = JSON.stringify({version: "7.0", dfp: h.get()})
    'bop': {"version": "7.0", "dfp": ""},

    # new params    2019/04/05
    # 'k_ft1': '',
    'k_ft4': '4'                                # k_ft = 4: prefer *.ts ,else *.f4v
}



class Iqiyi(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.headers = HEADERS

        self.user = IqiyiUser()

        self.initOpener()

    def getStaticUrlText(self, url):
        text = self.request(url)
        return text

    def parse(self, url, bids=[600]):
        """bid = [100, 200, 300, 400, 500, 600]
            : video resolution. the higher bid the higher definition
            require a list.
        """
        text = self.getStaticUrlText(url)

        tvid = re.search('''param\['tvid'\] = "(.+?)"''', text, re.S).group(1)
        vid = re.search('''param\['vid'\] = "(.+?)"''', text, re.I | re.S).group(1)

        videos_res = []

        for bid in bids:
            target_url = self.makeTargetUrl(tvid, vid, bid)

            res_json = self.getTargetJson(target_url)

            if not res_json:
                continue

            video_info = BasicVideoInfo(url, BeautifulSoup(text, features='html.parser').title.string,
                                        res_json['data']['ctl']['bid'])

            videos_res.append(IqiyiRespond(self, res_json, res_json, video_info))

        return videos_res

    def makeTargetUrl(self, tvid, vid, bid):

        time_str = str(int(time.time() * 1000))

        with PyJSCaller.Sesson('js/iqiyi.js') as sess:
            authkey, callback, require, cmd5x = sess.require('authkey', 'callback', 'require', 'cmd5x')

            # auk = authkey(authkey('') + time_str + tvid)
            # calb = callback()

            params = {
                'tvid': tvid,
                'vid': vid,
                'bid': str(bid),
                'tm': time_str,
                'uid': self.user.uid,
                'k_uid': self.user.k_uid,
                'pck': self.user.pck,
                'dfp': self.user.dfp,
                'callback': callback(),
                'authKey': authkey(authkey('') + time_str + tvid),
            }

            new_params = global_params.copy()
            new_params.update(params)

            querystring = require('querystring')
            querystring.require('stringify')
            params_encode = querystring.stringify(new_params)

            params_encode.operands.args[0].getExprText()

            req_path = '/jp/dash?' + params_encode

            vf = cmd5x(req_path)

            req_path += '&vf=' + vf
            sess.call(req_path)

        return 'http://cache.video.iqiyi.com/' + req_path.getValue().lstrip('/')


    def getTargetJson(self, req_url):
        text = self.request(req_url)
        json_str = re.search('try{\w{0,}\((.+})(\s)?\);}catch', text).group(1)
        if json_str:
            ret = json.loads(json_str)
        else:
            ret = None
        return ret


class IqiyiUser:
    def __init__(self):
        self.dfp = ''               # cookie: __dfp
        self.pck = ''               # cookie: P00001
        self.uid = ''               # cookie: P00002['uid]
        self.k_uid = ''             # cookie: QC005

    def extract(self, cookie_str):
        decode_cookie = unquote(cookie_str)
        __dfp = re.compile('__dfp=([a-z|A-Z|0-9]*)@')
        P00001 = re.compile('P00001=([a-z|A-Z|0-9]*);')
        QC005 = re.compile('QC005=([a-z|A-Z|0-9]*);')

        P00002 = re.compile('P00002=({.+?});')
        res_P00002 = P00002.search(decode_cookie)
        P00002_json = json.loads(res_P00002.group(1)) if res_P00002 else {}

        res_dfp = __dfp.search(decode_cookie)
        res_P00001 = P00001.search(decode_cookie)
        res_k_uid = QC005.search(decode_cookie)

        self.dfp = res_dfp.group(1) if res_dfp else ''
        self.pck = res_P00001.group(1) if res_P00001 else ''
        self.uid = P00002_json.get('uid', '')
        self.k_uid = res_k_uid.group(1) if res_k_uid else ''


class IqiyiRespond(BasicRespond):
    def __init__(self, parent, full_json, res_json, video_info):
        BasicRespond.__init__(self, parent, full_json, res_json, video_info)

        self.program = None

        self._target_video_urls = []

        self.__extract__(res_json)

    def __extract__(self, res_json):
        self.program = res_json['data'].get('program', None)
        self.sel_video = self.get_sel_video(self.program)

    def getRangeFormat(self):
        if self.getM3U8():
            return '&start=%d&end=%d'
        else:
            return '&ranges=%d-%d'

    def getM3U8(self):
        return self.sel_video.get('m3u8')

    def getFileFormat(self):
        return self.sel_video['ff']

    def getTotalFileSize(self):
        return self.getVideoSize()

    def getVideoSize(self):
        return self.sel_video['vsize']

    def getVideoTotal(self):
        m3u8 = self.getM3U8()
        if m3u8:
            self._target_video_urls = self.__extract_m3u8__(self.getM3U8())
            return len(self._target_video_urls)
        else:
            return len(self.get_sel_fs())

    def getScreenSize(self):
        return self.sel_video['scrsz']

    def getReqHeaders(self):
        return {
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.186 Safari/537.36',
            'Accept': '*/*',
            'Referer': 'http://www.iqiyi.com/',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9'
        }

    def getVideoUrls(self):
        if not self._target_video_urls:
            self.__getVideoFullUrl__()
        return self._target_video_urls

    def getFeatures(self):
        return {
            'quality': self.getQuality(),
            'screensize': self.getScreenSize(),
        }

    def matchFeature(self, feature):
        return feature['quality'] == self.getQuality() and feature['screensize'] == self.getScreenSize()



    def get_sel_video(self, program):
        if program:
            video = program['video']
            sel = None
            for i in video:
                if i.get('_selected', False) is True:
                    sel = i
                    break

            return sel
        return None

    def get_boss_msg(self):
        boss_ts = self.full_json['data'].get('boss_ts')
        boss = self.full_json['data'].get('boss')

        if boss_ts:
            return boss_ts.get('msg', '')
        if boss:
            return boss.get('msg', '')
        return ''

    def getSelBid(self):
        return self.sel_video['bid']

    def get_sel_fs(self):
        return self.sel_video['fs']

    def __getVideoFullUrl__(self):
        m3u8 = self.getM3U8()
        self._target_video_urls = []
        if m3u8:
            self._target_video_urls = self.__extract_m3u8__(self.getM3U8())
        else:
            res = self.make_dispatch_urls(self.get_sel_fs())
            self._target_video_urls = [i['l'] for i in res]

    def get_tvid(self):
        return self.full_json['data'].get('tvid', None)

    def get_vid(self):
        return self.sel_video['vid']

    def __extract_m3u8__(self, m3u8):
        if m3u8:
            m3u8_parts = re.compile('#EXTINF:\d+,\s+(http://data.video.iqiyi.com/videos/\S+)').findall(m3u8)
            rex_filename = re.compile('/([a-z|A-Z|0-9]+)\.([A-Z|a-z|0-9]+)\?')

            filenames = []
            reverse_parts = m3u8_parts[::-1]
            reverse_part_tails = []
            for i in reverse_parts:
                res = rex_filename.search(i)
                if res.group(1) not in filenames:
                    filenames.append(res.group(1))
                    reverse_part_tails.append(i)

            # complete total file
            part_tails = reverse_part_tails[::-1]
            ret = []
            for i in part_tails:
                ret.append(make_query(i, {'start': '0'}))

            return ret
        return []

    def get_albumid(self):
        return self.full_json['data']['aid']


    def get_boss(self):
        return self.full_json['data'].get('boss')

    def get_video_language(self):
        return self.sel_video['name']

    def make_dispatch_urls(self, fs):
        rex_filename = re.compile('/([a-z|A-Z|0-9]+)\.([A-Z|a-z|0-9]+)\?')
        paths = []
        filenames = []
        t_s = []

        boss = self.get_boss()
        albumid = self.get_albumid()
        tvid = self.get_tvid()
        vid = self.get_vid()
        qyid = self.parent.user.k_uid
        qypid = '%s__02020031010000000000' % tvid

        for i, j in enumerate(fs):
            paths.append(j['l'])
            filenames.append(rex_filename.search(paths[i]).group(1))
            t_s.append(str(boss.get('data', {}).get('t', '')) if boss else '')

        ibts_tmp = []
        with PyJSCaller.Sesson('js/iqiyi.js') as sess:
            cmd5x = sess.require('cmd5x')
            for i in range(len(fs)):
                ibt = cmd5x(str(t_s[i] + filenames[i]))
                ibts_tmp.append(ibt)
                sess.call(ibt)

        ibts = [i.getValue() for i in ibts_tmp]
        all_res = []
        for i in range(len(fs)):
            if boss and boss.get('data', {}).get('prv') == 1 and boss['previewTime'] == 1:
                ptime = int(60*1*1e3)
            else:
                ptime = 0

            QY00001 = boss.get('data', {}).get('u', '') if boss else ''

            params = {
                'cross-domain': '1',
                'qyid': qyid,
                'qypid': qypid,
                't': t_s[i],
                'cid': 'afbe8fd3d73448c9',
                'vid': vid,
                'QY00001': QY00001,
                'ibt': ibts[i],
                'ib': '4',
                'ptime': ptime,  # pcweb.js: getPreviewTime: function(e)
                'su': qyid,
                'client': '',  # pcweb.js: e.currentUserIP
                'z': '',  # pcweb.js: e.preDispatchArea
                'bt': '',  # pcweb.js: e.preDefinition
                'ct': '5',  # pcweb.js: e.currentDefinition
                # pcweb.js: mi: "tv_" + t.albumId + "_" + t.tvid + "_" + t.vid,
                'mi': 'tv_%s_%s_%s' % (albumid, tvid, vid),
                'e': '',
                'pv': '0.1',
                'tn': str(random.random()),

            }

            path = make_query(paths[i], params)
            text = self.parent.request('https://data.video.iqiyi.com/videos/%s' % path.lstrip('/'))
            msg = json.loads(text)
            all_res.append(msg)

        return all_res





def init():
    global IQIYI
    IQIYI = Iqiyi()
    load_cookie()

def parse(url, qualitys):
    global IQIYI, QUALITY
    return IQIYI.parse(url, [QUALITY[i] for i in qualitys])

def matchParse(url, quality, features):
    global IQIYI
    res = IQIYI.parse(url, [quality])
    for i in res:
        if i.matchFeature(features):
            return i

    return None



def load_cookie():
    global IQIYI

    if os.path.exists('cookies/iqiyi.txt'):
        with open('cookies/iqiyi.txt', 'r') as f:
            cookie = f.read().strip()

        if cookie:
            IQIYI.loadCookie(cookie)
    else:
        with open('cookies/iqiyi.txt', 'w'):
            pass





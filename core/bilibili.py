
import os
from core.common import BasicParser, BasicRespond, BasicVideoInfo, BasicAudioInfo, \
    CONTENT_TYPE_MAP, make_query, dict_get_key, format_byte
from bs4 import BeautifulSoup
import re
import json
import CommonVar as cv

BILIBILI = None
LASTRES = None

HEADERS = {
    # 'Host': 'www.bilibili.com',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',

}

QUALITY = {
    1: 16,
    2: 32,
    3: 64,
    4: 74,
    5: 80,
    6: 116
}


API = {
    'durl': 'https://api.bilibili.com/x/player/playurl?',
    'dash': 'https://api.bilibili.com/pgc/player/web/playurl?',
}

durl_params = {
    'avid': '',
    'cid': '',
    'qn': '',   # quality
    'type': '',
    'otype': 'json',
    'fnver': '0',
    'fnval': '0',
    'session': ''

}

dash_params = {
    'avid': '',
    'cid': '',
    'qn': '',   # quality
    'type': '',
    'otype': 'json',
    'fnver': '0',
    'fnval': '16',
    'session': ''
}


"""
r.fetchPlayurl({
    avid: n.aid,
    cid: n.cid,
    qn: r.cookie.get("CURRENT_QUALITY"),
    fnver: 0,
    fnval: r.cookie.get("CURRENT_FNVAL") || 16,
    type: "",
    otype: "json"
})
"""




class Bilibili(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.setHeaders(HEADERS)

    def parse(self, url, qualitys):
        text = self.request(url)
        bs4 = BeautifulSoup(text, features='html.parser')
        title = bs4.find('h1').getText()
        rex_playinfo = re.compile('window\.__playinfo__\s*=\s*({.*})')
        rex_aid = re.compile('window\.__INITIAL_STATE__\s*=\s*({.*})\s*;')

        playinfo = None
        inital_state = None
        for i in bs4.findAll('script'):
            i_text = i.getText()
            if playinfo and inital_state:
                break
            if not playinfo:
                tmp = rex_playinfo.search(i_text)
                if tmp:
                    playinfo = tmp.group(1)
            if not inital_state:
                tmp = rex_aid.search(i_text)
                if tmp:
                    inital_state = tmp.group(1)

        playinfo_json = json.loads(playinfo) if playinfo else {}
        inital_state_json = json.loads(inital_state)

        video_res = []

        add_params = self.get_info_dict(playinfo_json, inital_state_json, QUALITY[6])

        if playinfo_json:
            dash_full_json = playinfo_json
            if not dash_full_json['data'].get('dash'):
                add_params['qn'] = str(QUALITY[6])
                dash_full_json = self.api_parse(dash_params, add_params)
            if dash_full_json['data'].get('dash'):
                audios_info = self.get_audios_info(url, dash_full_json)
                for i in dash_full_json['data']['dash']['video']:
                    extra_info = BasicVideoInfo(url, title, i['id'])
                    video_res.append(BilibiliRespond(self, dash_full_json, i, extra_info, False, audios_info))
            elif dash_full_json['data'].get('durl'):
                if QUALITY[6] in qualitys:
                    extra_info = BasicVideoInfo(url, title, dash_full_json['data']['quality'])
                    video_res.append(BilibiliRespond(self, dash_full_json, dash_full_json['data'], extra_info, True))
                    qualitys.remove(QUALITY[6])

        for i in qualitys:
            add_params['qn'] = str(i)
            full_json = self.api_parse(durl_params, add_params)
            if full_json['data']:
                extra_info = BasicVideoInfo(url, title, full_json['data']['quality'])
                video_res.append(BilibiliRespond(self, full_json, full_json['data'], extra_info, True))

        return video_res

    def get_audios_info(self, url, full_json):

        headers = HEADERS.copy()
        headers['Range'] = 'bytes=0-0'
        headers['Referer'] = url

        audios_info = []
        for i in full_json['data']['dash']['audio']:

            if i['backupUrl']:
                urls = [i['baseUrl'], *i['backupUrl']]
            else:
                urls = [i['baseUrl']]

            res = self.requestRaw(url=urls[0], headers=headers)
            size = int(res.info().get('Content-Range').split('/')[-1])

            info = 'bandwidth: %10s size: %10s' % (i['bandwidth'], format_byte(size))

            audios_info.append(BasicAudioInfo(urls, size, info))

        return audios_info

    def get_info_dict(self, playinfo_json, inital_state_json, quality):
        if inital_state_json.get('videoData'):
            aid = inital_state_json['videoData']['aid']
            cid = inital_state_json['videoData']['cid']
        elif inital_state_json.get('epInfo'):
            aid = inital_state_json['epInfo']['aid']
            cid = inital_state_json['epInfo']['cid']
        else:
            raise ValueError('unknown type')

        session = playinfo_json.get('session', '')

        _params = {
            'avid': str(aid),
            'cid': str(cid),
            'qn': str(quality),  # quality
            'session': str(session)
        }

        return _params

    def api_parse(self, base_params, add_params):
        """from api: https://api.bilibili.com/x/player/playurl?
        """
        req_params = base_params.copy()

        req_params.update(add_params)
        playurl = make_query(API['durl'], req_params)

        text = self.request(playurl)

        return json.loads(text)



class BilibiliRespond(BasicRespond):
    def __init__(self, parent, full_json, res_json, extra_info, isdurl, audio_info=None):
        BasicRespond.__init__(self, parent, full_json, res_json, extra_info)
        self._videosize = -1
        self._audiosize = -1        # selected one

        self.isdurl = isdurl

        self._target_video_urls = []
        self._target_audio_urls = []

        self._audios_info = audio_info

        self._video_len = -1

        self.__extract__()


    def __extract__(self):
        if self.isdurl:
            # target video urls
            for i in self.res_json['durl']:
                if i['backup_url']:
                    self._target_video_urls.append([i['url'], *i['backup_url']])
                else:
                    self._target_video_urls.append([i['url']])

            # video size
            size = 0
            for i in self.res_json['durl']:
                size += i['size']
            self._videosize = size



        else:
            # target video urls
            if self.res_json['backupUrl']:
                self._target_video_urls.append([self.res_json['baseUrl'], *self.res_json['backupUrl']])
            else:
                self._target_video_urls.append([self.res_json['baseUrl']])

            # video size
            self._videosize = self._get_file_size_from_url_(self._target_video_urls[0][0])

        self._video_len = self.full_json['data']['timelength']


    def getVideoTotal(self):
        return len(self._target_video_urls)

    def getAudioTotal(self):
        if self.isdurl:
            return 0
        else:
            return 1 if len(self._audios_info) > 0 else 0

    def getVideoSize(self):
        return self._videosize

    def getAudioSize(self):
        return self._audiosize

    def getFileFormat(self):
        if self.isdurl:
            if 'flv' in self.res_json['format']:
                return 'flv'
            else:
                return self.res_json['format'].replace('/', '').replace('\\', '')
        if CONTENT_TYPE_MAP.get(self.res_json['mimeType'].strip()):
            return CONTENT_TYPE_MAP.get(self.res_json['mimeType'].strip())
        else:
            return self.res_json['mimeType'].strip().split('/')[-1]

    def getScreenSize(self):
        if self.isdurl:
            index = self.res_json['accept_quality'].index(self.getQuality())
            return self.res_json['accept_description'][index]
        else:
            return "%dx%d" % (self.res_json['width'], self.res_json['height'])

    def getTotalFileSize(self):
        return self._videosize + self._audiosize if self._audiosize > 0 else self._videosize

    def getReqHeaders(self):
        return {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.103 Safari/537.36',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'Range': 'bytes=0-0',
            'Referer': self.getBaseUrl(),
        }

    def setSelAudio(self, index):
        self._target_audio_urls = [self._audios_info[index].urls]
        self._audiosize = self._audios_info[index].size

    def getAllAudioInfo(self):
        if self.isdurl:
            return None
        else:
            return [i.info for i in self._audios_info]

    def getVideoUrls(self):
        return self._target_video_urls

    def getAudioUrls(self):
        return self._target_audio_urls

    def getFeatures(self):
        return {
            'quality': self.getQuality(),
            'screensize': self.getScreenSize(),
        }

    def matchFeature(self, feature):
        return feature['quality'] == self.getQuality() and feature['screensize'] == self.getScreenSize()

    def getConcatMethod(self):
        return cv.MER_CONCAT_DEMUXER

    def _get_file_size_from_url_(self, url):
        res = self.parent.requestRaw(url=url, headers=self.getReqHeaders())
        return int(res.info().get('Content-Range').split('/')[-1])



def init():
    global BILIBILI
    BILIBILI = Bilibili()
    load_cookie()


def parse(base_url, qualitys):
    global BILIBILI, QUALITY
    return BILIBILI.parse(base_url, [QUALITY[i] for i in qualitys])


def matchParse(base_url, quality, features):
    global BILIBILI
    res = BILIBILI.parse(base_url, [quality])
    for i in res:
        if i.matchFeature(features):
            return i

    return None



def load_cookie():
    global BILIBILI

    if os.path.exists('cookies/bilibili.txt'):
        with open('cookies/bilibili.txt', 'r') as f:
            cookie = f.read().strip()

        if cookie:
            BILIBILI.loadCookie(cookie)
    else:
        with open('cookies/bilibili.txt', 'w'):
            pass


if __name__ == '__main__':
    init()
    load_cookie()
    
    print(1)
    pass

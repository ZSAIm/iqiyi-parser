
import os
from core.common import BasicParser, BasicRespond, BasicVideoInfo, BasicAudioInfo, \
    CONTENT_TYPE_MAP, make_query, dict_get_key, format_byte
from bs4 import BeautifulSoup
import re
import json


TENCENT = None
LASTRES = None

HEADERS = {
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



class Tencent(BasicParser):
    def __init__(self):
        BasicParser.__init__(self)
        self.setHeaders(HEADERS)


    def parse(self):
        pass



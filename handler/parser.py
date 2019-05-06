# -*- coding: utf-8 -*-

# import time, random
# import re
# import json, os
# # import CommonVar as cv
# from bs4 import BeautifulSoup
# from urllib.parse import unquote
#
# import PyJSCaller
# from core.common import BasicParser, BasicRespond, BasicVideoInfo, make_query, BasicUserCookie, BasicUrlGroup, BasicAudioInfo, raw_decompress, extract_query

from urllib.parse import splithost, splittype
import os
import CommonVar as cv
import traceback


PARSER = {}

def init():
    # parsers = os.listdir(cv.PARSER_PATH)
    error_msg = []
    for i, j in cv.PARAER_DOMAIN_MAPPING.items():
        name, ext = os.path.splitext(i)
        if ext.lower() == '.py':

            namespace_ = {}
            try:
                with open(os.path.join(cv.PARSER_PATH, i), 'r') as f:
                    code = f.read()
                    exec(code, namespace_)
            except:
                msg = u'      < %s > 加载失败：\n' % os.path.join(cv.PARSER_PATH, i)
                error_msg.append(msg + traceback.format_exc())

            for m in j:
                PARSER[m] = DictModule(namespace_)
            # a = __import__(os.path.join(cv.PARSER_PATH, name))
    return error_msg


LASTRES = None
LASTREQ = None




# PARSER = {
#     'iqiyi': core.iqiyi,
#     'bilibili': core.bilibili,
#     'v.qq': core.tencent,
#     'youku': core.youku
#
# }

class DictModule:
    def __init__(self, dict):
        self._____ = dict

    def __getattr__(self, item):
        if item in dir(self):
            return object.__getattribute__(self, item)
        else:
            return self._____.get(item)

def getRespond():
    global LASTRES
    return LASTRES


def get_parser_from_url(url):
    global PARSER
    protocol, s1 = splittype(url)
    host, path = splithost(s1)
    for i, j in PARSER.items():
        if i in host:
            return j

    return None


def parse(url, *args):
    global LASTREQ, LASTRES
    LASTREQ = (url, *args)
    sel_parser = get_parser_from_url(url)

    sel_parser.init()
    LASTRES = sel_parser.parse(url, *args)
    return LASTRES


def matchParse(url, quality, features):
    global LASTREQ, LASTRES
    LASTREQ = (url, quality, features)
    sel_parser = get_parser_from_url(url)

    sel_parser.init()
    return sel_parser.matchParse(*LASTREQ)

if __name__ == '__main__':

    init()
# pass

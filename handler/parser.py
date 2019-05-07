# -*- coding: utf-8 -*-

import time, random
import re
import json, os
from bs4 import BeautifulSoup
from urllib.parse import unquote

import PyJSCaller
from core.common import BasicParser, BasicRespond, BasicVideoInfo, \
    make_query, BasicUserCookie, BasicUrlGroup, BasicAudioInfo, raw_decompress, extract_query
import urllib.parse
import urllib.request
import urllib.error
import urllib.response
from urllib.parse import splithost, splittype, urljoin, urlencode
import os
import CommonVar as cv
import traceback
import random


PARSER = {}




LASTRES = None
LASTREQ = None




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
    for i in LASTRES:
        print(i.full_json)
    return LASTRES


def matchParse(url, quality, features):
    global LASTREQ, LASTRES
    LASTREQ = (url, quality, features)
    sel_parser = get_parser_from_url(url)

    sel_parser.init()
    return sel_parser.matchParse(*LASTREQ)


def init():
    error_msg = []
    if not os.path.exists(cv.PARSER_PATH):
        os.mkdir(cv.PARSER_PATH)
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
    return error_msg
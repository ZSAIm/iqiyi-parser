# -*- coding: utf-8 -*-

from urllib.parse import splithost, splittype
import core


LASTRES = None
LASTREQ = None

PARSER = {
    'iqiyi': core.iqiyi,
    'bilibili': core.bilibili,
    'v.qq': core.tencent,
    'youku': core.youku

}


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





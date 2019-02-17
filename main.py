"""
**********************************************************************
**********************************************************************
**      author: ZSAIm
**      email:  405935987@163.com
**      github: https://github.com/ZSAIm/iqiyi-parser
**
**                                          programming by python 2.7
**
**                                                      02.17-2019
**********************************************************************
**********************************************************************
"""

import nbdler
import merger
import urllib
import time
from ___progressbar import progressBar
import os, pyperclip
import iqiyi_parse
import ConfigParser
import json

iqiyi = iqiyi_parse.Iqiyi()
global_bids = [100, 200, 300, 400, 500, 600]
MAX_TASK = 5
SAVE_PATH = ''
DEL_AFTER = True



def save_config():
    if os.path.exists('config.ini') is True:
        return
    config = ConfigParser.SafeConfigParser()
    config.add_section('settings')
    json.dumps(global_bids)
    config.set('settings', 'bids', json.dumps(global_bids))
    config.set('settings', 'max_task', str(MAX_TASK))
    config.set('settings', 'save_path', str(SAVE_PATH))
    config.set('settings', 'del_after', 'T' if DEL_AFTER else 'F')
    with open('config.ini', 'wb') as f:
        config.write(f)


def load_config():
    global global_bids, MAX_TASK, SAVE_PATH, DEL_AFTER
    if os.path.exists('config.ini') is False:
        return False

    config = ConfigParser.SafeConfigParser()

    config.read('config.ini')
    json_raw = config.get('settings', 'bids')
    MAX_TASK = int(config.get('settings', 'max_task'))

    SAVE_PATH = config.get('settings', 'save_path')
    DEL_AFTER = True if config.get('settings', 'del_after') == 'T' else False
    global_bids = json.loads(json_raw)




def react_wait():
    while True:
        _input = raw_input('>>> ').lower()
        if 'n' in _input and 'y' not in _input:
            return False
        if 'y' in _input and 'n' not in _input:
            return True

def int_select_input(begin, end):
    while True:
        _input = raw_input('>>> ').lower()
        if _input == '-1':
            return -1
        if not _input.isalnum():
            continue
        else:
            if int(_input) < begin or int(_input) >= end:
                continue
            else:
                return int(_input)

def catch_url(last_url):
    last_clip = ''
    while True:
        time.sleep(0.1)
        clip = pyperclip.paste()
        if clip:
            protocal, s1 = urllib.splittype(clip)

            host, path = urllib.splithost(s1)
            if host is None or 'iqiyi' not in host:
                continue
            else:
                if last_clip != clip and clip != last_url:
                    print '" \033[31m' + clip + '\033[0m "'

                last_clip = clip
                if last_url == clip:

                    continue
                else:
                    return clip

def make_filenames(filename, msg):
    names = []
    for i, j in enumerate(msg['fs']):
        name = '%04d-%s.%s' % (i, filename, msg['ff'])
        names.append(name)

    return names

def build_dl(videoname, names_list, sel_msg):
    dlm = nbdler.Manager()
    for i, j in enumerate(names_list):
        _url, _ = iqiyi.activate_path(sel_msg['fs'][i]['l'])
        filepath = os.path.join(SAVE_PATH, videoname)

        if os.path.exists(os.path.join(filepath, j)) is True:
            if os.path.exists(os.path.join(filepath, j + '.nbdler')):
                dl = nbdler.open(fp=os.path.join(filepath, j))
                dlm.addHandler(dl)
            continue

        dl = nbdler.open(filename=j, filepath=filepath, max_conn=5, urls=[_url])
        dlm.addHandler(dl)

    return dlm

def dl_process(dlm):
    colors = ['red', 'blue', 'yellow', 'white', 'cyan', 'green', 'magenta']

    dlm.config(max_task=MAX_TASK)

    id_pbar = []
    color_index = 0
    for i, j in dlm.getAllTask().items():
        if color_index == len(colors):
            color_index = 0
        pbar = progressBar(i, j.file.size, color=colors[color_index])
        id_pbar.append((i, pbar))
        color_index += 1
    dlm.run()

    while not dlm.isEnd():
        cur_queue = dlm.getRunQueue()
        ids, pbars = zip(*id_pbar)

        for i in cur_queue:
            dl = dlm.getHandler(i)
            inc = dl.file.size - dl.getLeft()
            speed = round(dl.getInsSpeed() / 1024, 1)
            pbars[i].update(inc, '%6s kb/s' % speed)


        time.sleep(1)

def del_seg_video(name_paths, filepath):
    for i in name_paths:
        os.remove(i)
    os.removedirs(filepath)


def main():
    save_config()
    load_config()
    # last_url = ''
    url = ''
    # print top
    print '[Ctrl + C] to copy the iqiyi video url, and go back to see this console.'
    while True:
        last_url = url
        url = catch_url(last_url)
        if last_url == url:
            continue
        videoname, _msg = iqiyi.parse(url, global_bids)
        if _msg:
            print '+---------------------------------------------------------------+'
            print '\033[0;37;41m' + videoname + '\033[0m'
            print '+---------------------------------------------------------------+'
            _count = 0
            for i, j in _msg.items():
                print '[%d]%9s - Total size: %4s mb - Add up %d parts' % (
                    _count, i, int(j['vsize']) * 1.0 / 1024 / 1024, len(j['fs']))
                _count += 1
            print '[-1] back.'
            index = int_select_input(0, _count)
            if index == -1:
                continue
            else:
                break
        else:
            continue
    if _msg:

        _count = 0
        for i, j in _msg.items():
            if index == _count:
                sel_msg = j
                break
            _count += 1
        else:
            raise AttributeError
        names = make_filenames(videoname, sel_msg)

        if not os.path.exists(unicode(videoname)):
            os.mkdir(unicode(videoname))

        dlm = build_dl(videoname, names, sel_msg)
        dl_process(dlm)

        merger_bar = progressBar(0, len(names), 30)

        name_paths = []
        filepath = unicode(os.path.join(SAVE_PATH, unicode(videoname)))
        for i in names:
            name_paths.append(os.path.join(filepath, i))

        mer = merger.merger(os.path.join(SAVE_PATH, unicode(videoname)) + u'.f4v', name_paths)
        mer.start()
        while True:
            merger_bar.update(mer.now)
            time.sleep(0.2)
            if mer.now == mer.sum:
                merger_bar.update(mer.now)
                break
        if DEL_AFTER:
            del_seg_video(name_paths, filepath)

        print 'OK!'

        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()



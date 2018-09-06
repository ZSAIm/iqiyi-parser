"""
**********************************************************************
**********************************************************************
**      author: ZSAIm
**      email:  405935987@163.com
**      github: https://github.com/ZSAIm/iqiyi-parser
**
**                                          programming by python 2.7
**
**                                                      8.31-2018
**********************************************************************
**********************************************************************
"""

from dl.downloader import downloader
import merger
import urllib
import time
import ___progressbar,os, pyperclip
import iqiyi_parse
import ConfigParser
import json

iqiyi = iqiyi_parse.Iqiyi()
global_bids = [100, 300, 600]
MAX_TASK = 3
FILE_VERIFY = True
SAVE_PATH = ''
# iqiyi.parse(url, [100])




def save_config():
    if os.path.exists('config.ini') is True:
        return
    config = ConfigParser.SafeConfigParser()
    config.add_section('settings')
    json.dumps(global_bids)
    config.set('settings', 'bids', json.dumps(global_bids))
    config.set('settings', 'max_threads', str(MAX_TASK))
    config.set('settings', 'file_verify', str(FILE_VERIFY))
    config.set('settings', 'save_path', str(SAVE_PATH))

    with open('config.ini', 'wb') as f:
        config.write(f)


def load_config():
    global global_bids, MAX_TASK, FILE_VERIFY, SAVE_PATH
    if os.path.exists('config.ini') is False:
        return False

    config = ConfigParser.SafeConfigParser()

    config.read('config.ini')
    json_raw = config.get('settings', 'bids')
    MAX_TASK = int(config.get('settings', 'max_threads'))
    file_verify_str = config.get('settings', 'file_verify')
    if file_verify_str.lower() == 'false':
        FILE_VERIFY = False
    else:
        FILE_VERIFY = True

    SAVE_PATH = config.get('settings', 'save_path')
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
    dl_list = []
    for i, j in enumerate(names_list):
        if os.path.exists(os.path.join(videoname, j)) is True:
            continue
        dl = downloader()
        dl.config(file_name=j, file_path=os.path.join(SAVE_PATH, videoname), max_thread=5, verify=FILE_VERIFY)
        _url, _ = iqiyi.activate_path(sel_msg['fs'][i]['l'])
        dl.add_url(_url)
        try:
            dlm = dl.open()
            dl_list.append(dlm)
        except Exception('FileExistsError'):
            pass
    return dl_list

def dl_process(dl_list):
    dl_tmp = dl_list[:]
    colors = ['red', 'blue', 'yellow', 'white', 'cyan', 'black', 'green', 'magenta']
    running_list = []
    while True:
        running_list = filter(lambda (x, y): x.isDone() is False, running_list)
        if len(running_list) <= MAX_TASK:
            cur_run_len = MAX_TASK - len(running_list)
            for i in dl_list[:cur_run_len]:
                isin = False
                for j in running_list:
                    if i in j:
                        isin = True
                        break
                if isin is True:
                    break
                i.start()
                sel_color = None
                for m in colors:
                    for j, k in running_list:
                        if k.color == m:
                            break
                    else:
                        sel_color = m
                        break

                if sel_color is None:
                    sel_color = colors[0]
                pbar = ___progressbar.progressBar(dl_tmp.index(i), i.file.size, color=sel_color)
                running_list.append((i, pbar))
            dl_list = dl_list[cur_run_len:]
        for i, j in running_list:
            left_size = i.file.size - i.getLeft()
            j.update(left_size, '%d kb/s' % int(i.getinsSpeed() / 1024))
        time.sleep(1)

        if len(dl_list) == 0 and len(running_list) == 0:
            break



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
        dl_list = build_dl(videoname, names, sel_msg)
        dl_process(dl_list)

        merger_bar = ___progressbar.progressBar(0, len(names), 30)

        name_path = []
        for i in names:
            name_path.append(os.path.join(unicode(videoname), i))

        mer = merger.merger(unicode(videoname) + u'.f4v', name_path)
        mer.start()
        while True:
            merger_bar.update(mer.now)
            time.sleep(0.2)
            if mer.now == mer.sum:
                merger_bar.update(mer.now)
                break
        print 'OK!'
        while True:
            time.sleep(1)


if __name__ == '__main__':
    main()



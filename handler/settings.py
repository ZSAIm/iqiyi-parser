
import os, time
from configparser import ConfigParser, NoSectionError, NoOptionError
import CommonVar as cv
import gui

FILE_URL = {
    'node': 'https://npm.taobao.org/mirrors/node/v0.12.18/node.exe',
    'ffmpeg': 'https://ffmpeg.zeranoe.com/builds/win64/static/ffmpeg-3.2-win64-static.zip'
}



def setUndoneJob(url, title, quality, features):
    cv.UNDONE_JOB = {
        'url': url,
        'quality': quality,
        'title': title,
        'features': features
    }

def clearUndoneJob():
    cv.UNDONE_JOB = ''


def initConfig():

    cv.FFMPEG_PATH = 'ffmpeg.exe'

    saveConfig()

    if not os.path.exists('cookies'):
        os.mkdir('cookies')

def saveConfig():
    config = ConfigParser()
    config.add_section('Settings')

    config.set('Settings', 'max_task_num', str(cv.MAX_TASK))
    config.set('Settings', 'max_thread_num', str(cv.MAX_CONN))
    config.set('Settings', 'buffer_size', str(cv.BUFFER_SIZE))
    config.set('Settings', 'block_size', str(cv.BLOCK_SIZE))
    config.set('Settings', 'last_save_path', str(cv.FILEPATH))
    config.set('Settings', 'undone_job', str(cv.UNDONE_JOB))
    config.set('Settings', 'ffmpeg', str(cv.FFMPEG_PATH))

    with open('config.ini', 'w') as f:
        config.write(f)


def __loadConfig__():
    if os.path.exists('config.ini') is False:
        initConfig()
        return False
    config = ConfigParser()

    config.read('config.ini')
    try:
        cv.MAX_TASK = int(config.get('Settings', 'max_task_num'))
        cv.MAX_CONN = int(config.get('Settings', 'max_thread_num'))
        cv.BUFFER_SIZE = int(config.get('Settings', 'buffer_size'))
        cv.BLOCK_SIZE = int(config.get('Settings', 'block_size'))
        cv.FILEPATH = config.get('Settings', 'last_save_path')
        undonejob = config.get('Settings', 'undone_job')
        cv.FFMPEG_PATH = config.get('Settings', 'ffmpeg')
        cv.UNDONE_JOB = eval(undonejob) if undonejob else ''
    except (NoSectionError, NoOptionError):
        initConfig()


def loadConfig():
    __loadConfig__()

    # gui.frame_parse.textctrl_path.SetValue(cv.FILEPATH)


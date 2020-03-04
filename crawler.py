# -*- coding: UTF-8 -*-

"""  解析引擎。"""

from worker import Worker

from script import supported_script, get_script
from config import REGISTERED_SCRIPT
from utils import split_name_version


class CrawlerWorker(Worker):
    order = 10

    def __init__(self, urls):
        self.urls = urls
        self.script_guards = [None for _ in range(len(urls))]

    def run(self):
        for index, url in enumerate(self.urls):
            supporteds = supported_script(url)
            if not supporteds:
                # 无法处理该URL
                continue
            # 获取优先级高的脚本
            script_name = min(supporteds, key=lambda x: int(
                REGISTERED_SCRIPT[split_name_version(x)[0]]['order']
            ))
            script = get_script(script_name)
            self.script_guards[index] = script
            # 提交脚本到
            (url, dict(REGISTERED_SCRIPT[script.name]))

    def getinfo(self):
        return [guard.progress.getinfo() if guard else None for guard in self.script_guards]

    def close(self):
        pass



def init_







# from base import BaseScript

# import re
# print(re.search(r'a', 'bab'))
from script import BaseScript
import script
print(script)


class BilibiliCrawlerScript(BaseScript):
    """ Bilibili爬虫脚本。"""
    name = 'bilibili'
    version = 0.1
    supported_domains = ['bilibili.com']


if __name__ == '__main__':
    # from script import
    pass
# -*- coding: UTF-8 -*-
"""
Supplied Library:
    - requests:
    - bs4:

Supplied Utility:
    - js_session:   from jscaller import session
    - extract_cookies_str_to_jar:

"""

from utils import extract_cookies_str_to_jar
import requests


class BaseScript(object):
    """ 爬虫脚本基类。继承基类 BaseClass
    :class variable
        name:               脚本名称
        version:            脚本版本
        supported_domains:  脚本支持的域
    """
    name = 'base'
    version = 0.1
    supported_domains = []
    TIMEOUT = 10

    def __init__(self, progress, config, url):
        """
        :param
            guard:  脚本监控对象
            url:    要处理的URL
            config: 爬虫脚本配置信息
        """
        self.progress = progress
        # 从配置中读入cookies。
        cookies = config.get('cookies', '')
        cookies = extract_cookies_str_to_jar(cookies)
        self.url = url
        self.cookies = cookies
        self.config = config
        # requests 会话。
        self.session = requests.session()
        self._init()

    def _init(self):
        """ 自定义初始化。"""
        pass

    def _request(self, method, url, **kwargs):
        """ 处理URL资源。具体参数参考方法 requests.Session.request()。"""
        # cookies参数
        self.cookies.update(kwargs.pop('cookies', {}))
        kwargs['cookies'] = self.cookies
        # timeout参数。
        timeout = kwargs.pop('timeout', self.TIMEOUT)
        kwargs['timeout'] = timeout
        return self.session.request(method, url, **kwargs)

    def run(self):
        """ """
        res = self._request('GET', self.url)
        print(res)

    def report(self, *, percent=None, message=None):
        """ 报告进度消息。"""
        if percent or message:
            # 报告进度。写入当前的进度。
            self.progress.report(percent, message)


class BaseScriptV2(BaseScript):
    """ 爬虫脚本基类。继承基类 BaseClass
    :class variable
        name:               脚本名称
        version:            脚本版本
        supported_domains:  脚本支持的域
    """
    name = 'base'
    version = 2.0
    supported_domains = []
    TIMEOUT = 10


if __name__ == '__main__':
    # 基类脚本测试
    class TestCrawlerScript(BaseScript):
        name = 'test'
        supported_domains = ['www.baidu.com']
        version = 1.0

        def run(self):
            res = self._request('GET', 'http://www.qq.com')
            print(res.text)

    from script import ScriptProgress
    from config import create_script_config

    test = TestCrawlerScript(ScriptProgress(), create_script_config(), 'http://www.baidu.com')
    test.run()

# -*- coding: UTF-8 -*-

from config import REGISTERED_SCRIPT, create_script_config, SCRIPT_CONFIG
from urllib.parse import urlparse
import requests, bs4
from jsworker import js_session
from utils import utility_package, split_name_version
from collections import defaultdict
import os


BaseScript = object
# 已编译的脚本
COMPILED_SCRIPTS = {}

# 注册的域
# 'example.com': 'name-version'
registered_domains = defaultdict(list)

# 为脚本提供的第三方库
supplied_utilities = {
    'BaseScript': BaseScript,
    'requests': requests,
    'bs4': bs4,
    'js_session': js_session,
}
supplied_utilities.update(utility_package)


class ScriptProgress:
    """ 脚本进度。"""
    def __init__(self):
        self.msg = '脚本准备就绪。'
        # 进度百分比。
        self.percent = 0

    def getinfo(self):
        """ 返回当前的进度信息字典。"""
        return {
            'message': self.msg,
            'percent': self.percent
        }

    def start(self, message=None):
        """ 进度开始。"""
        self.percent = 0
        self.report(message=message)

    def end(self, message=None):
        """ 进度结束。"""
        self.percent = 100
        self.report(message=message)

    def report(self, percent=None, message=None):
        """ 进度消息报告。"""
        if message:
            self.msg = message
        if percent:
            self.percent = percent


class ScriptGuard:
    """ 脚本运行监视。 """
    def __init__(self, script, config):
        self.script = script
        self.config = config
        self.progress = ScriptProgress()

    def __call__(self, *args, **kwargs):
        """ 初始化爬虫脚本。 """
        self.progress.start('开始执行。')
        res = self.script(self.progress, self.config, *args, **kwargs)
        self.progress.end('执行完毕。')
        return res

    def getinfo(self):
        """ 获取当前脚本的执行进度。"""
        return self.progress.getinfo()

    def join(self):
        """ 脚本监视，阻塞至脚本执行完毕，若超时则抛出异常。"""

    def __repr__(self):
        return '<ScriptGuard %s==%s>' % (self.script.name, self.script.version)


class CompiledScript:
    """ 编译的脚本。"""
    def __init__(self, name):
        """
        :param
            name:       脚本名称。
            timeout:    脚本运行超时时间，若为None则不设置超时。
        """
        self.name = name
        self.scripts = {}
        self._active = None

    @property
    def supported_domains(self):
        """ 返回active脚本所支持的域。"""
        return self._active.supported_domains

    @property
    def version(self):
        """ 返回active脚本的版本号。"""
        return self._active.version

    def get(self, version=None):
        """ 返回指定版本的脚本。"""
        if version is None:
            version = self.version
        script = self.scripts.get(version, None)
        if script is None:
            return None
        return ScriptGuard(script, SCRIPT_CONFIG.get(script.name, create_script_config()))

    def install(self, script):
        """ 安装已编译的脚本。
        注意：若安装了更高版本的脚本，将会自动更改激活新的版本。所以若要使用低版本，
        需要在安装新脚本后重新激活旧版本的脚本。
        """
        self.scripts[script.version] = script
        if not self._active or script.version > self._active.version:
            self.active(script.version)

    def active(self, version):
        """ 激活指定版本的脚本。"""
        if version not in self.scripts:
            raise ValueError('找不到版本号: %s。' % version)
        self._active = self.scripts[version]

    def get_versions(self):
        """ 返回该脚本所有的版本号。"""
        return sorted(self.scripts.keys(), reverse=True)

    def __repr__(self):
        return '<CompiledScript %s==%s>' % (self.name, self.version)


def script_validate(source_byte, key):
    """ 脚本校验。"""
    from hashlib import sha256
    s = sha256()
    s.update(source_byte)
    if s.hexdigest() != key:
        return None
    return source_byte


def compile_script(script_name, verify=True):
    """ 编译指定脚本。"""
    with open(os.path.join('script', script_name), 'rb') as fb:
        source = fb.read()
    # 脚本校验。
    if verify and not script_validate(source, REGISTERED_SCRIPT.get(script_name, None)):
        return None
    # 脚本编译
    code = compile(source, '', 'exec')
    # 脚本全局环境构建
    _globals = supplied_utilities.copy()
    _locals = {}
    try:
        # 加载脚本
        exec(code, _globals, _locals)
    except Exception as err:
        return err
    else:
        global COMPILED_SCRIPTS, registered_domains, BaseScript
        # 从脚本中提取爬虫继承类。
        for k, script in _locals.items():
            try:
                if issubclass(script, BaseScript):
                    # 保存编译的脚本
                    if script.name not in COMPILED_SCRIPTS:
                        COMPILED_SCRIPTS[script.name] = CompiledScript(script.name)
                    COMPILED_SCRIPTS[script.name].install(script)
                    # 域-脚本 映射。
                    for domain in script.supported_domains:
                        registered_domains[domain].append('%s-%s' % (script.name, script.version))
            except TypeError:
                # 非class，跳过检测
                continue


def get_script(script_name, version=None):
    """ 返回已经编译好的爬虫脚本对象。
    :param
        script_name:脚本名称。若脚本名称带有版本号，那么将返回指定版本号的脚本，否则返回被激活的脚本。
        version:    若None获取最新的版本。
    """
    name, _version = split_name_version(script_name)
    if _version is not None:
        version = _version

    script = COMPILED_SCRIPTS.get(name, None)
    # 没有找到指定名称的脚本。
    if not script:
        return None
    return script.get(version)


def supported_script(url):
    """ 返回能处理该URL的脚本名称-版本。
    :param
        url:            提供要处理的URL。
        with_version:   返回名称是否带有版本号。
    """
    return registered_domains.get(urlparse(url).netloc, [])


def register(script_name, sha256_key):
    """ 注册爬虫脚本。 """
    if not os.path.isfile('script/%s' % script_name):
        raise FileNotFoundError('在脚本目录script下未找到指定名称的脚本，请检查是否存在该文件。')

    if script_name in REGISTERED_SCRIPT:
        raise PermissionError('该脚本已被注册，请不要重复注册。')

    REGISTERED_SCRIPT[script_name] = sha256_key


def init_script():
    """ 脚本初始化。"""
    global BaseScript
    # 初始化爬虫脚本基类
    compile_script('base.py', verify=False)
    # 更新base.py的默认使用版本
    version = SCRIPT_CONFIG['base']['default_version']
    try:
        version = float(version)
    except (TypeError, ValueError):
        version = None
    if version is not None:
        COMPILED_SCRIPTS['base'].active(version)
    # 准备脚本基类。
    BaseScript = get_script('base').script
    supplied_utilities['BaseScript'] = BaseScript

    # 编译所有注册的脚本。
    for script in [filename for filename in REGISTERED_SCRIPT.keys() if filename != 'base.py']:
        compile_script(script, False)

    # 加载脚本配置
    for k, v in SCRIPT_CONFIG.items():
        script = COMPILED_SCRIPTS.get(k, None)
        try:
            default_version = float(v['default_version'])
        except (TypeError, ValueError):
            default_version = None
        if script and default_version is not None:
            # 激活配置中的默认信息。
            script.active(default_version)

    script = get_script('bilibili')
    print(script)
    ins = script('http://www.baidu.com')
    ins.run()
    print(script)
# e = compile_script('bilibili.py')
# s = get_script('bilibili')
# print(s)
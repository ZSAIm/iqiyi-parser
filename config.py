import hashlib
from configparser import ConfigParser
import os
ADMIN_AUTH = 'ADMIN'
USER_AUTH = 'USER'
SCRIPT_AUTH = 'SCRIPT'

ADMIN_CONFIG = {

}
# 用户配置
USER_CONFIG = {
    'max_concurrent': 3,
    'validate': True,
}

# 已注册的脚本
REGISTERED_SCRIPT = {
    # 'base.py': '',
    'bilibili.py': ''
}

SCRIPT_CONFIG = {
    'base': {
        # 脚本优先级, 数值越小，优先级越高
        'order': 100,
        'cookies': '',
        'proxies': None,
        'default_version': None,
        'default_quality': None,
    }
}
# 全局程序配置
GLOBAL_CONFIG = {
    ADMIN_AUTH: ADMIN_CONFIG,
    USER_AUTH: USER_CONFIG,
    SCRIPT_AUTH: REGISTERED_SCRIPT,

}


def create_script_config():
    """ 创建空的脚本配置。"""
    return {
        # 脚本优先级, 数值越小，优先级越高
        'order': 100,
        'cookies': '',
        'proxies': None,
        'default_version': None,
        'default_quality': None,
    }


def get(name):
    """ 返回配置信息。"""
    return GLOBAL_CONFIG.get(name, None)


def set(name, value, permission=None):
    """ 设置配置。"""
    target = GLOBAL_CONFIG.get(permission, None)
    if target is None:
        raise PermissionError('未授权的行为。')
    target[name] = value


def load():
    """ 加载配置文件。"""
    # 系统配置
    config = ConfigParser(allow_no_value=True)
    if not config.read('config.ini'):
        write_back()
    # GLOBAL_CONFIG[ADMIN_AUTH] = config['ADMIN']
    # GLOBAL_CONFIG[USER_AUTH] = config['USER']
    # GLOBAL_CONFIG[SCRIPT_AUTH] = config['SCRIPT']

    ADMIN_CONFIG.update(config['ADMIN'])
    USER_CONFIG.update(config['USER'])
    REGISTERED_SCRIPT.update(config['SCRIPT'])

    # 加载脚本配置
    script_config = ConfigParser(allow_no_value=True)
    if not script_config.read('script.ini') or not script_config.sections():
        script_config.update(SCRIPT_CONFIG)
        with open('script.ini', 'w') as configfile:
            script_config.write(configfile)

    for section in script_config.sections():
        SCRIPT_CONFIG[section] = dict(script_config[section])


def write_back():
    """ 配置回写。"""
    config = ConfigParser(allow_no_value=True)
    config['ADMIN'] = ADMIN_CONFIG
    config['USER'] = USER_CONFIG
    config['SCRIPT'] = REGISTERED_SCRIPT
    with open('config.ini', 'w') as configfile:
        config.write(configfile)

# -*- coding: UTF-8 -*-

from app import create_flask_app
from webdriver import create_wx_app
from downloader import mgr
from utils import forever_run
from script import init_script
import config


def main():
    """ 主程序。 """
    # 加载程序配置
    config.load()
    # 创建GUI
    wx_app = create_wx_app()
    # 创建后台服务器
    flask_app = create_flask_app()
    # 启动后台服务器
    forever_run(flask_app.run, port=5999)
    # 初始化脚本
    init_script()
    # 启动下载管理器
    mgr.start()

    # 加载WebUI
    wx_app.frame.browser.LoadURL('http://127.0.0.1:{port}'.format(port=5999))

    # GUI主循环
    wx_app.MainLoop()


def destroy():
    """ 销毁程序。"""
    # 关闭下载管理器。
    mgr.close()


if __name__ == '__main__':
    main()
    destroy()



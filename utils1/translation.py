
from jinja2.ext import i18n


def translate(text):
    toolbar = {
        'new': '新建',
        'start': '开始',
        'pause': '暂停',
        'delete': '删除',
        'select all': '选择全部',
        'display order': '显示顺序',
        'help': '帮助',
    }
    return toolbar.get(text.lower(), text)

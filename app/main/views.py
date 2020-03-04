
from flask import render_template, request, abort
from . import main
import json
import downloader


@main.route('/')
def index():
    return render_template('index.html')


@main.route('/getinfo')
def getinfo():
    detail = int(request.args.get('detail', 0))
    tids = json.loads(request.args.get('tids', '[]'))
    print(detail, tids)
    # # 单独分开获取每一个任务的ID的详细信息。

    return render_template('index.html')


@main.route('/godownload', methods=['POST'])
def godownload():
    """ 建立解析下载请求。"""
    if request.method != 'POST':
        abort(403)
    data = json.loads(request.get_data().decode(encoding='utf-8'))
    print(data)
    # print(data.decode(encoding='utf-8'))
    urls = data.get('urls', [])
    for url in urls:
        tid = downloader.request(url)

    print(data)
    return '[]'


@main.route('/getresponse')
def getresponse():
    """ 获取解析响应。"""
    task_id = request.args.get('task_id', None)
    if not task_id:
        abort(403)

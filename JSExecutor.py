
import os
import execjs
import execjs.runtime_names

_JSExec_ = None


def init():
    global _JSExec_
    js_context = ''

    with open("pcweb.js", 'r') as f:
        js_context += f.read()

    os.environ["PATH"] = os.environ["PATH"] + ';' + 'nodejs'
    os.environ["EXECJS_RUNTIME"] = "Node"  # v0.11.8
    reload(execjs)
    execjs.get(execjs.runtime_names.Node)
    _JSExec_ = execjs.compile(js_context)

def call(*args):
    global _JSExec_
    return _JSExec_.call(*args)



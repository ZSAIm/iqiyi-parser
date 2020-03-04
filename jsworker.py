""" JS引擎执行队列。"""

from contextlib import contextmanager
from threading import Semaphore
import jscaller
import os


sema = Semaphore(2)


@contextmanager
def js_session(s, timeout=None, engine=None):
    """ 限制JS执行的并发量。"""
    if os.path.isfile(s):
        session = jscaller.session
    else:
        session = jscaller.Session
    with sema:
        with session(s, timeout, engine) as sess:
            yield sess



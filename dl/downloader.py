# -*- coding: UTF-8 -*-

import os
from DLManager import DLManager
import DLInformation

class downloader:

    def __init__(self):
        self.file = DLInformation.FileInfo()
        self.url = []

    def config(self, **kwargs):
        """specify [name,[path,[thread_count]

        args:
            ::param:    file_name       :
            ::param:    file_path       :
            ::param:    max_thread      :
            ::param:    force           :
            ::param:    verify          :
            ::param:    fix_try         :
            ::param:    block_size      :
        """

        self.file.path = unicode(kwargs.get('file_path', ''))

        if kwargs.get('file_name') is not None:
            self.file.name = unicode(kwargs.get('file_name'))

        self.file.VERIFY = kwargs.get('verify', True)
        self.file.FIX_TRY = kwargs.get('fix_try', True)

        self.file.force = kwargs.get('force', False)

        self.file.BLOCK_SIZE = kwargs.get('block_size', None)
        self.file.MAX_THREAD = kwargs.get('max_thread', 5)

    def add_url(self, url, host=None, path=None, port=None, cookie='', headers=None):
        self.url.append(DLInformation.URLinfo(url, host, path, port, cookie))
        if headers is not None:
            self.url[-1].add_headers(headers)

        if len(self.url) == 1 and self.file.name is None:
            self.file.name = self.url[0].get_filename()
            self.file.size = int(self.url[0].res_headers.get('content-length', 0))

    def clear_urls(self):
        self.url = []

    def __config(self):
        _size = self.url[0].res_headers['content-length']
        for i in self.url:
            if _size != i.res_headers['content-length']:
                raise Exception("ContentLenNoMatch", _size, i.res_headers['content-length'])

        if not self.file.force:
            self.file.validate_name()
        else:
            if os.path.exists(os.path.join(self.file.path, self.file.name)):
                raise Exception('FileExistsError')
        self.file.size = int(_size)

        if self.file.BLOCK_SIZE is None:
            if self.file.size <= 10 * 1024 * 1024:
                self.file.BLOCK_SIZE = 64 * 1024    # 64 KB
            elif self.file.size <= 100 * 1024 * 1024:
                self.file.BLOCK_SIZE = 512 * 1024   # 512 KB
            else:
                self.file.BLOCK_SIZE = 1024 * 1024  # 1 MB

    def open(self, **kwargs):
        """open url to get ready to download.

        args:
            ::param:    file_name       :
            ::param:    file_path       :
            ::param:    max_thread      :
            ::param:    force           :
            ::param:    verify          :
            ::param:    fix_try         :
            ::param:    block_size      :

        """
        if not self.url:
            raise AttributeError('NoUrlError, you need to .add_url() before open.')
        if kwargs:
            self.config(**kwargs)
        self.__config()
        return DLManager(self.url, self.file)

    def load(self, path, name):
        import cPickle
        if os.path.exists(os.path.join(path, name + '.db')) is True:
            with open(os.path.join(path, name + '.db'), 'rb') as f:
                pkl = cPickle.Unpickler(f)
                return DLManager.load(pkl.load())
        else:
            return None
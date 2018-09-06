

class TaskAssign:
    def __init__(self, DLMobj, GlobalProg, urls, file):

        self.DLMobj = DLMobj
        self.GlobalProg = GlobalProg
        self.file = file
        self.urls = urls

    def free_block(self):
        """GlobalProgress.map"""
        free_list = []
        _begin = None
        for index, value in enumerate(self.GlobalProg.map):
            if value is None:
                if _begin is None:
                    _begin = index
            else:
                if _begin is not None:
                    free_list.append((_begin, index))
                    _begin = None
        else:
            if _begin is not None and _begin != len(self.GlobalProg.map) - 1:

                free_list.append((_begin, len(self.GlobalProg.map) - 1))

        return free_list

    def block_to_range(self, block_range):
        if block_range == []:
            return [None, None]

        if block_range[0] == 0:
            _begin_pos = 0
        else:
            _begin_pos = (block_range[1] + block_range[0]) * self.file.BLOCK_SIZE / 2.0
            _begin_pos = int(_begin_pos - _begin_pos % self.file.BLOCK_SIZE)
            if _begin_pos == block_range[0] * self.file.BLOCK_SIZE:
                _begin_pos += self.file.BLOCK_SIZE

        if block_range[1] == len(self.GlobalProg.map) - 1:
            _end_pos = self.DLMobj.file.size
        else:
            _end_pos = block_range[1] * self.file.BLOCK_SIZE
        _range = [_begin_pos, _end_pos]

        if _range[0] == _range[1]:
            _range = [None, None]
        return _range


    def assign(self):

        _blocks = self.free_block()
        if _blocks == []:
            _range = [None, None]
        else:
            _max_block = sorted(_blocks, key=lambda x: (x[1] - x[0]), reverse=True)[0]
            _range = self.block_to_range(_max_block)

        # fetch appropriate server, which is the highest speed per thread.
        _dict = self.GlobalProg.getQueueServerMes()
        _url = None
        if len(_dict) >= len(self.urls):
            _speed_up = sorted(list(_dict.items()), key=lambda x: x[1]['SPEED'] / x[1]['COUNT'])
            _url = _speed_up[-1][0]
        else:
            for i in self.urls:
                if i not in _dict.keys():
                    _url = i
                    break

        if len(self.GlobalProg.queue) != 0 and None not in _range:
            _parent_progress = self.GlobalProg.get_parent_prog(_range)
            _range = _parent_progress.clip_range_req(_range)

        if _url is None:
            _url = self.urls[0]
        if None not in _range:
            self.GlobalProg.map[int(_range[0] / self.file.BLOCK_SIZE)] = self.urls.index(_url)

        return _url, _range

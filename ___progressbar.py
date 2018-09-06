# -*- coding=utf-8 -*-

from colorama import init
init()

class progressBar(object):
    def __init__(self, id, sum, width=30, color='red', char=' '):
        self.width = width
        self.index = 0
        self.sum = sum
        self.char = char
        self.color = color
        self.id = id

    def __pbarprint(self, color, mass_end=''):

        perc = int((self.index*1.0/self.sum)*100)
        count = int(perc / 100.0 * self.width)
        bar = ''
        bar1 = ''
        for i in range(count):
            bar += self.char

        for i in range(self.width - count):
            bar1 += ' '

        colors = {
            'black': '\033[0;37;40m',
            'red': '\033[0;37;41m',
            'green': '\033[0;37;42m',
            'yellow': '\033[0;37;43m',
            'blue': '\033[0;37;44m',
            'magenta': '\033[0;37;45m',
            'cyan': '\033[0;37;46m',
            'white': '\033[0;30;47m'
        }

        sumlen = str(self.__countNum(self.sum))

        if mass_end:
            format_txt = '%03d: %3d%% |' + colors[color] + '%s\033[0m%s| %0' + sumlen + 'd/%0' + sumlen + 'd [ %s ]'
            if len(bar) == 0: format_txt = '%03d: %3d%% |%s\033[0m%s| %0' + sumlen + 'd/%0' + sumlen + 'd [ %s ]'
            print format_txt % (self.id, perc, bar, bar1, self.index, self.sum, mass_end)
        else:
            format_txt = '%03d: %3d%% |' + colors[color] + '%s\033[0m%s| %0' + sumlen + 'd/%0' + sumlen + 'd'
            if len(bar) == 0: format_txt = '%03d: %3d%% |%s\033[0m%s| %0' + sumlen + 'd/%0' + sumlen + 'd'
            print format_txt % (self.id, perc, bar, bar1, self.index, self.sum)



    def update(self, index, mass_end='', color=None):
        self.index = index
        if color is None:
            color = self.color
        self.__pbarprint(color, mass_end)


    def __placeSpace(self, words, space, left_align):
        count = space - len(words)
        sp = ''
        for i in range(count):
            sp += ' '
        if left_align:
            return words + sp
        else:
            return sp + words

    def __countNum(self, num):
        count = 1

        while num / 10:

            count += 1
            num /= 10

        return count
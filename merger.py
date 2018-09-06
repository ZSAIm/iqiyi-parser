import threading,os

class merger(threading.Thread):
    def __init__(self, destination_path_name, source_path_name_list):
        threading.Thread.__init__(self)
        self.destpathNa = destination_path_name
        self.sourpathNa = source_path_name_list
        self.sum = len(self.sourpathNa)
        self.sumSize = 0
        for i in self.sourpathNa:
            if not os.path.exists(i):
                break
            self.sumSize += os.path.getsize(i)
        else:
            self.sumSize = 0

        self.now = 0
    def run(self):
        # print self.destpathNa.decode('UTF-8')
        with open(unicode(self.destpathNa), 'wb') as destFile:
            for path in self.sourpathNa:
                # print path.decode('UTF-8')
                self.now += 1
                with open(unicode(path), 'rb') as sourFile:
                    destFile.write(sourFile.read())
        self.now = len(self.sourpathNa)
        # print 'OK'


# text = merger('2.txt', '0.txt', '1.txt')
# text.start()
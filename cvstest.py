import csv, sys

class Statistics():
    def __init__(self, maxdev, fileObj = sys.stdout):
        self.statistics = {}
        self.file = fileObj

        for i in range (1, maxdev + 1):
            self.statistics[i] = {'id': i, 'total': 0, 'success': 0, 'failure': 0}

    def getiter(self):
        i = iter(sorted(self.statistics.iteritems()))
        return i

    def __repr__(self):
        string = ''
        for j in self.getiter():
            string = string + str(j) + "\n"
        return string

    def __getitem__(self, i):
        return self.statistics[i]

    def failure(self, i):
        self.statistics[i]['total'] = self.statistics[i]['total'] + 1
        self.statistics[i]['failure'] = self.statistics[i]['failure'] + 1

    def success(self, i):
        self.statistics[i]['total'] = self.statistics[i]['total'] + 1
        self.statistics[i]['success'] = self.statistics[i]['success'] + 1
    
    def writeCSV(self):
        w = csv.DictWriter(self.file, ['id', 'total', 'success', 'failure'])
        w.writeheader()
        for j in self.getiter():
            w.writerow(j[1])


with open('derp.cvs', 'w') as cvsfile:

    s = Statistics(5, fileObj = cvsfile)
    for i in range(8):
        s.success(1)

    for i in range(4):
        s.success(2)
        s.failure(2)

    for i in range(2):
        s.success(3)
        s.failure(3)
        s.failure(3)
        s.failure(3)

    for i in range(3):
        s.failure(4)
        s.success(4)
        s.success(4)
        s.success(4)

    for i in range(8):
        s.failure(5)

    s.writeCSV()

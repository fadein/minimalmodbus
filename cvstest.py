import csv, sys, datetime

# can I have a nested class in Python?
class UTC(datetime.tzinfo):
    ZERO = datetime.timedelta(0)
    def utcoffset(self, dt):
        return UTC.ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return UTC.ZERO


class Statistics():
    def __init__(self, fileObj = sys.stdout):
        self.eventLog = []
        self.file = fileObj
        self.total = 0
        self.success = 0
        self.failure = 0
        self.utc = UTC()


    def getiter(self):
        i = iter(sorted(self.eventLog))
        return i


    def __repr__(self):
        string = ''
        for j in self.getiter():
            string = string + str(j) + "\n"
        return string


    def __getitem__(self, i):
        return self.eventLog[i]

    def logReading(self, device, register, value, desc):
        record = {'when': datetime.datetime.now(self.utc).strftime("%a %b %d %H:%M:%S %Z %Y"),
                'device': device,
                'register': register,
                'value': value,
                'desc': desc}
        self.eventLog.append(record)
        self.total += 1

    def badReading(self, device, register, desc=''):
        self.logReading(device, register, False, desc)
        self.failure += 1

    def goodReading(self, device, register, value, desc=''):
        self.logReading(device, register, value, desc)
        self.success += 1

    def descLine(self, desc):
        record = {'when'   : '',
                'device'   : '',
                'register' : '',
                'value'    : '',
                'desc'     : desc}
        self.eventLog.append(record)

    def writeCSV(self):
        w = csv.DictWriter(self.file, [ 'when', 'device', 'register', 'value', 'desc', ])
        w.writeheader()
        for r in self.eventLog:
            w.writerow(r)

    def summarize(self):
        self.writeCSV()
        print self

s = Statistics()
s.descLine('just trying to make it in this wirld')
s.goodReading(1, 400, 1492)
s.goodReading(2, 400, 1492)
s.goodReading(3, 400, 1492)
s.writeCSV()

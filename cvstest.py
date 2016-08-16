import csv, sys, datetime



class Statistics():
    class UTC(datetime.tzinfo):
        ZERO = datetime.timedelta(0)
        def utcoffset(self, dt):
            return Statistics.UTC.ZERO

        def tzname(self, dt):
            return "UTC"

        def dst(self, dt):
            return Statistics.UTC.ZERO

    def __init__(self, fileObj = sys.stdout):
        self.eventLog = []
        self.file = fileObj
        self.total = 0
        self.success = 0
        self.failure = 0
        self.utc = Statistics.UTC()
        self.begin = datetime.datetime.now(self.utc)


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
        record = {'when'   : None,
                'device'   : None,
                'register' : None,
                'value'    : None,
                'desc'     : desc}
        self.eventLog.append(record)


    def writeCSV(self):
        w = csv.DictWriter(self.file, [ 'when', 'device', 'register', 'value', 'desc', ])
        w.writeheader()
        for r in self.eventLog:
            w.writerow(r)


    def summarize(self):
        """ Tally up the statistics """
        self.descLine('Total readings: {}'.format(self.total))
        self.descLine('Successful readings: {} ({:03.2f}%)'.format(self.success, (self.success * 100.0 / self.total)))
        self.descLine('Failed readings: {} ({:03.2f}%)'.format(self.failure, (self.failure * 100.0 / self.total)))
        self.descLine('Number of devices polled: {}'.format( len(set([x['device'] for x in self.eventLog if isinstance(x['device'], int)])) ))
        self.writeCSV()


s = Statistics()
s.descLine('just trying to make it in this wirld')
for i in [(x, y) for x in range(3) for y in range(400, 404)]:
    s.goodReading(i[0], i[1], 1492, 'columbus sailed the ocean blue')

for i in [(x, y) for x in range(3) for y in range(300, 303)]:
    s.badReading(i[0], i[1])

s.summarize()

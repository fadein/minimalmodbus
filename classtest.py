class Statistics():
        def __init__(self, maxdev):
            self.statistics = {}

            for i in range (1, maxdev + 1):
                self.statistics[i] = {'total': 0, 'success': 0, 'failure': 0}

        def getiter(self):
            i = iter(sorted(self.statistics.iteritems()))
            return i

        def __repr__(self):
            string = ''
            for j in self.getiter():
                string = string + str(j) + "\n"
            return string

s = Statistics(4)

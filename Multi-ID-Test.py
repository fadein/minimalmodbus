import minimalmodbus, time, serial, datetime, sys, csv
from argparse import ArgumentParser

MAX_DEVICE = 4
COMPORT = 'COM8'
addr = 400
debug = False
cycleDelay = .300

parser = ArgumentParser()
parser.add_argument("-c", "--comport", dest="comport", default="COM8", metavar="COM8", type=str,
        help="COM port the ModBus network is on")
parser.add_argument("-n", "--numsensors", dest="numsensors", default=1, metavar="N", type=int,
        help="How many sensors to poll (i.e. maximum sensor address)")
parser.add_argument('-y', '--cycles', dest='cycles', default=-1, metavar='N', type=int,
        help='How many times to poll each sensor before terminating')
parser.add_argument('-t', '--cycle-timeout', dest='cycleTimeout', default=5.0, metavar='N', type=float,
        help='How long to wait between cycles')
parser.add_argument('-d', '--cycle-delay', dest='cycleDelay', default=0.3, metavar='N', type=float,
        help='How long to wait between cycles')
parser.add_argument('-f', '--file', dest='file', default='modbus.csv', metavar='FILE', type=str,
        help='Filename to store CSV output')
parser.add_argument('-D', '--desc', dest='desc', default='', metavar='DESC', type=str,
        help='Description of this test, noted within CSV file')
args = parser.parse_args()

COMPORT  = args.comport
MAX_DEVICE = args.numsensors

minimalmodbus.BAUDRATE = 9600
minimalmodbus.PARITY = 'N'
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1
minimalmodbus.TIMEOUT = 0.5 #500ms


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


# modbus function 1  -> Read Coil Status
# modbus function 2  -> Read Input Status
# modbus function 3  -> Read Holding Register
# modbus function 4  -> Read Input Register
# modbus function 5  -> Force Single Coil
# modbus function 6  -> Preset Single Register
# modbus function 15 -> Force Multiple Coils
# modbus function 16 -> Preset Multiple Registers

def readHoldingRegister(dbg, address, stats):
    pass

def readInputRegister(dbg, address, stats):
    pass

# TODO: refactor this to not recreate the modbusH each time
def getModbusValues(dbg, address, stats):
        register = 300

        for id in range (1, MAX_DEVICE + 1):
                print  "Polling device ",id
                print  "-------------------"
                modbusH = minimalmodbus.Instrument(COMPORT, id,mode='rtu')
                minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
                if (dbg == True):
                    modbusH.debug = True

                    # print handler info
                    print modbusH

                try:
                    #Read Holding Register
                    # read_registers(register_addr, num_registers, functioncode=3)
                    holR = modbusH.read_registers(address - 1, 1)
                    print ("Holding Register -> Slave ID: <%d>  Address : %d  "%(id, address ) + " Value(s) : " + ",".join(str(v) for v in holR ) )
                    time.sleep(args.cycleDelay)

                    #Read Input Register
                    # read_registers(register_addr, num_registers, functioncode=3)
                    inputR = modbusH.read_registers(register - 1, 1, 4)
                    print ("Input Register -> Slave ID: <%d>  Address : %d  "%(id, register ) + " Value(s) : " + ",".join(str(v) for v in inputR ) )
                    stats.goodReading(id, address, str(inputR))
                    time.sleep(args.cycleDelay)

                except IOError, e:
                    print "%s : %s : %s" % ('echoTime()', e , e.errno)
                    stats.badReading(id, address)

                print
                time.sleep(args.cycleDelay)
        return

statistics = Statistics()
try:
        if len(args.desc) > 0:
            statistics.descLine(args.desc)

        cycle = 0
        while args.cycles - cycle != 0:
                cycle = cycle + 1
                print "=============================="
                print "Cycle #%d" % cycle
                print "=============================="
                getModbusValues(debug, addr, statistics)
                print
                print
                time.sleep(args.cycleTimeout)

except KeyboardInterrupt:
        print
        print "Terminating program..."

finally:
        print "=================================================="
        print "                 Final statistics"
        print "=================================================="
        statistics.summarize()

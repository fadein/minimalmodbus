import minimalmodbus, time, serial, datetime, sys, csv
from argparse import ArgumentParser

MAX_DEVICE = 4
COMPORT = 'COM8'
DEBUG = False

parser = ArgumentParser()
parser.add_argument("-c", "--comport", dest="comport", default="COM8", metavar="COM8", type=str,
        help="COM port the ModBus network is on")

parser.add_argument("-n", "--numsensors", dest="numsensors", default=1, metavar="N", type=int,
        help="How many sensors to poll (i.e. maximum sensor address)")
parser.add_argument('-y', '--cycles', dest='cycles', default=-1, metavar='N', type=int,
        help='How many times to poll each sensor before terminating')

parser.add_argument('-a', '--intra-cycle-delay', dest='intraDelay', default=0.3, metavar='0.3', type=float,
        help='How long to wait between polling devices within a cycle')

parser.add_argument('-e', '--inter-cycle-delay', dest='interDelay', default=5.0, metavar='5.0', type=float,
        help='How long to wait between cycles')

parser.add_argument('-f', '--file', dest='file', default='', metavar='FILE', type=str,
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
minimalmodbus.TIMEOUT = 1.5 #500ms


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
        self.overall = {'total': 0, 'success': 0, 'failure': 0}
        self.by_device = {}
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
        self.overall['total'] += 1

    def badReading(self, device, register, desc=''):
        self.logReading(device, register, False, desc)
        self.overall['failure'] += 1
        if (self.by_device.has_key(device)):
            self.by_device[device]['total'] += 1
            self.by_device[device]['failure'] += 1
        else:
            self.by_device[device] = {'total': 1, 'success': 0, 'failure': 1}


    def goodReading(self, device, register, value, desc=''):
        self.logReading(device, register, value, desc)
        self.overall['success'] += 1
        if (self.by_device.has_key(device)):
            self.by_device[device]['total'] += 1
            self.by_device[device]['success'] += 1
        else:
            self.by_device[device] = {'total': 1, 'success': 1, 'failure': 0}

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
        for fact in ('Total readings: {}'.format(self.overall['total']),
                'Successful readings: {} ({:03.2f}%)'.format(self.overall['success'], (self.overall['success'] * 100.0 / self.overall['total'])),
                'Failed readings: {} ({:03.2f}%)'.format(self.overall['failure'], (self.overall['failure'] * 100.0 / self.overall['total'])),
                'Number of devices polled: {}'.format( len(set([x['device'] for x in self.eventLog if isinstance(x['device'], int)])) ),
                '',
                'Stats by Modbus address:',
                '------------------------'):
            print fact
            self.descLine(fact)

        for addr in self.by_device.iteritems():
            for fact in ('Dev #{}: Total readings: {}'.format(addr[0], addr[1]['total']),
                    'Dev #{}: Successful readings: {} ({:03.2f}%)'.format(addr[0], addr[1]['success'], addr[1]['success'] * 100.0 / addr[1]['total']),
                    'Dev #{}: Failed readings: {} ({:03.2f}%)'.format(addr[0], addr[1]['failure'], addr[1]['failure'] * 100.0 / addr[1]['total']),
                    ''):
                print fact
                self.descLine(fact)

        self.writeCSV()


# modbus function 1  -> Read Coil Status
# modbus function 2  -> Read Input Status
# modbus function 3  -> Read Holding Register
# modbus function 4  -> Read Input Register
# modbus function 5  -> Force Single Coil
# modbus function 6  -> Preset Single Register
# modbus function 15 -> Force Multiple Coils
# modbus function 16 -> Preset Multiple Registers


def readHoldingRegister(device, address, stats, dbg):
    modbusH = minimalmodbus.Instrument(COMPORT, device, mode='rtu')
    v = False
    if (dbg == True):
        modbusH.debug = True
        # print handler info
        print modbusH

    try:
        v = modbusH.read_register(address, 0, 3, False)
        stats.goodReading(device, address, str(v))
    except IOError, e:
        v = False
        stats.badReading(device, address, 'bad reading')
        print "\tBad read on device ", device
    time.sleep(args.intraDelay)
    return v


def readInputRegister(device, address, stats, dbg):
    modbusH = minimalmodbus.Instrument(COMPORT, device, mode='rtu')
    v = False
    if (dbg == True):
        modbusH.debug = True
        # print handler info
        print modbusH

    try:
        v = modbusH.read_register(address, 0, 4, False)
        stats.goodReading(device, address, str(v))
    except IOError, e:
        v = False
        stats.badReading(device, address, 'bad reading')
        print "\tBad read on device ", device
    time.sleep(args.intraDelay)
    return v


def allDevicesHoldingRegister(address, stats, dbg):
    for dev in range (1, MAX_DEVICE + 1):
        print "Polling device ", dev
        readHoldingRegister(dev, address, stats, dbg)

def allDevicesInputRegisters(address, stats, dbg):
    for dev in range (1, MAX_DEVICE + 1):
        print "Polling device ", dev
        readInputRegister(dev, address, stats, dbg)


def getModbusValues(dbg, address, stats):
    """DEPRECATED : the orginal code
    reads from a Holding reg, followed by a read from an Input reg
    """

    register = 300

    for id in range (1, MAX_DEVICE + 1):
            print  "Polling device ",id
            print  "-------------------"
            modbusH = minimalmodbus.Instrument(COMPORT, id, mode='rtu')
            if (dbg == True):
                modbusH.debug = True

                # print handler info
                print modbusH

            try:
                #Read Holding Register
                # read_registers(register_addr, num_registers, functioncode=3)
                holR = modbusH.read_registers(399, 1)
                print ("Holding Register -> Slave ID: <%d>  Address : %d  "%(id, address ) + " Value(s) : " + ",".join(str(v) for v in holR ) )
                time.sleep(args.intraDelay)

                #Read Input Register
                # read_registers(register_addr, num_registers, functioncode=4)
                # reg
                inputR = modbusH.read_registers(299, 1, 4)
                print ("Input Register -> Slave ID: <%d>  Address : %d  "%(id, register ) + " Value(s) : " + ",".join(str(v) for v in inputR ) )
                stats.goodReading(id, address, str(inputR))
                time.sleep(args.intraDelay)

            except IOError, e:
                print "%s : %s : %s" % ('echoTime()', e , e.errno)
                stats.badReading(id, address)

            print
            time.sleep(args.interDelay)
    return


statistics = None
if args.file == '':
    statistics = Statistics()
else:
    statistics = Statistics(open(args.file, 'wb'))

try:
    if len(args.desc) > 0:
        statistics.descLine(args.desc)

    cycle = 0
    while args.cycles - cycle != 0:
            cycle += 1
            print "=============================="
            print "Cycle #%d" % cycle
            print "=============================="
            allDevicesInputRegisters(299, statistics, DEBUG)
            print
            print
            time.sleep(args.interDelay)

except KeyboardInterrupt:
        print
        print "Terminating program..."

except IOError:
        print
        print "%s : %s : %s" % ('echoTime()', e , e.errno)
        print "Terminating program..."

finally:
        print "=================================================="
        print "                 Final statistics"
        print "=================================================="
        statistics.summarize()

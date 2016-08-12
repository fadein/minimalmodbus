import minimalmodbus, time, serial, datetime, sys
from argparse import ArgumentParser

MAX_ADDR = 4
COMPORT = 'COM8'
add = 400
ADDR_BASE = 1
debug = False
cycleDelay = .300

parser = ArgumentParser()
parser.add_argument("-c", "--comport", dest="comport", default="COM8", metavar="COM8", type=str,
        help="COM port the ModBus network is on")
parser.add_argument("-n", "--numsensors", dest="numsensors", default=1, metavar="N", type=int,
        help="How many sensors to poll (i.e. maximum sensor address)")
args = parser.parse_args()

COMPORT  = args.comport
MAX_ADDR = args.numsensors

minimalmodbus.BAUDRATE = 9600
minimalmodbus.PARITY = 'N'
minimalmodbus.BYTESIZE = 8
minimalmodbus.STOPBITS = 1
minimalmodbus.TIMEOUT = 0.5 #500ms

ZERO = datetime.timedelta(0)

class UTC(datetime.tzinfo):

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return "UTC"

    def dst(self, dt):
        return ZERO

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

        def __getitem__(self, i):
            return self.statistics[i]

def echoTime():
        t = datetime.datetime.now(utc).strftime("%a %b %d %H:%M:%S %Z %Y")
        return t

def getModbusValues(dbg, address, ADDR_BASE, stats):
        modbusVal = 0
        register = 300
        delay = 1
        for id in range (1, MAX_ADDR + 1):
                print  "Polling device ",id
                print  "-------------------"
                modbusH = minimalmodbus.Instrument(COMPORT, id,mode='rtu')
                minimalmodbus.CLOSE_PORT_AFTER_EACH_CALL = True
                if (dbg == True):
                        modbusH.debug = True

                        # print handler info
                        print modbusH

                try:
                        stats[id]['total'] = stats[id]['total'] + 1
                        print(echoTime())
                        holR=modbusH.read_registers(address - ADDR_BASE, 1)  # last parameter is # of registers.
                        print ("Holding Register -> Slave ID: <%d>  Address : %d  "%(id, address ) + " Value(s) : " + ",".join(str(v) for v in holR ) )

                        time.sleep(1) #wait for a second

                        #Read Input Register
                        print(echoTime())
                        inputR=modbusH.read_registers(register - ADDR_BASE, 1, 4) # last parameter is # of registers.
                        print ("Input Register -> Slave ID: <%d>  Address : %d  "%(id, register ) + " Value(s) : " + ",".join(str(v) for v in inputR ) )

                        stats[id]['success'] = stats[id]['success'] + 1
                        time.sleep(1) #wait for a second

                except IOError, e:
                        print "%s : %s : %s" % (echoTime(), e , e.errno)
                        stats[id]['failure'] = stats[id]['failure'] + 1

                print
                time.sleep(cycleDelay)
        return

# modbus function 1 -> Read Coil Status
# modbus function 2     -> Read Input Status
# modbus function 3 -> Read Holding Register
# modbus function 4 -> Read Input Register
# modbus function 5 -> Force Single Coil
# modbus function 6 -> Preset Single Register
# modbus function 15 -> Force Multiple Coils
# modbus function 16 -> Preset Multiple Registers


utc = UTC()
try:
        statistics = Statistics(MAX_ADDR)
        cycles = 1
        while True:
                print "=============================="
                print "Cycle #%d" % cycles
                print "=============================="
                getModbusValues(debug, add, ADDR_BASE, statistics)
                print
                print
                cycles = cycles + 1
                time.sleep(5)

except KeyboardInterrupt:
        print
        print "Terminating program..."

finally:
        print "=================================================="
        print "                 Final statistics"
        print "=================================================="
        print statistics

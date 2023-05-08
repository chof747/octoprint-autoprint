from logging import Logger
import re
import gpiod
from time import sleep
from octoprint.printer import PrinterInterface
from octoprint.util import ResettableTimer

CONNECTION_WAIT = 1
CONNECTION_TIMEOUT_REPEAT = 5
TEMP_WAIT_CYCLE = 5

# Configuration for both the printer power and light GPIOs
GPIO_CONFIG = gpiod.line_request()
GPIO_CONFIG.consumer = 'octoprint-autoprint'
GPIO_CONFIG.request_type = gpiod.line_request.DIRECTION_OUTPUT

# All the data fields we need to do GPIO
class GpioBundle:
    def __init__(self, chip, line, name):
        self.chip = chip
        self.line = line
        self.name = name

# Lists all GPIO Names
def ListGpioNames():
    gpioNames = []
    for chip in gpiod.chip_iter():
        for line in chip.get_all_lines():
            if not line.is_used():
                gpioNames.append(line.name)
    
    # Remove duplicates sicne they cannot be identified by name
    uniqueGpioNames = []
    for name in gpioNames:
        if gpioNames.count(name) == 1:
            uniqueGpioNames.append(name)
    
    return uniqueGpioNames

class PrinterControl:

    def __init__(self, logger: Logger, printer: PrinterInterface) -> None:
        self._gpioPrinter = None
        self._gpioLight = None
        self._startupTime = None
        self._cooldownTemp = None
        self._turnOffAfterPrint = False

        self._logger = logger
        self._printer = printer
        self._cooldownTimer = None

    def startUpPrinter(self, callback = None, lightsOn=True) -> bool:
        """Command that starts up the printer and turns on the light"""

        self._statePrinter = True
        if (lightsOn):
            self._stateLight = True

        connectTimer = ResettableTimer(self._startupTime, self._connectPrinter, [callback])        
        connectTimer.start();   


    def shutDownPrinter(self):
        """Command that shutdowns the printer and turns off the light"""

        if (self._checkTemperatures()):
            self._cooldownTimer = None
            self._shutDown()
        else:
            self._logger.debug("Wait a few seconds for tool to cooldown")
            self._cooldownTimer = ResettableTimer(TEMP_WAIT_CYCLE, self.shutDownPrinter)
            self._cooldownTimer.start()

    def cancelShutDown(self):
        """Cancel a given shutdown command"""
        if (None != self._cooldownTimer):
            self._cooldownTimer.cancel();
            self._cooldownTimer = None;

    def toggleLight(self):
        """Command to toggle the state of the light"""
        self._stateLight = not self._stateLight
    
# ~~ Private helper Methods

    def _getPrinterState(self):
        return bool(self._gpioPrinter.line.get_value()) if None != self._gpioPrinter else None
    def _setPrinterState(self, state):
        self._gpioPrinter.line.set_value(state)
        self._logger.debug("Printer turned %s" %
                           ("on" if state else "off"))
    
    _statePrinter = property(_getPrinterState, _setPrinterState)

    def _getLightState(self):
        return bool(self._gpioLight.line.get_value()) if None != self._gpioLight else None
    def _setLightState(self, state):
        self._gpioLight.line.set_value(state)
        self._logger.debug("Light turned %s" %
                           ("on" if state else "off"))
    
    _stateLight = property(_getLightState, _setLightState)


    def _checkTemperatures(self):
        tempData = self._printer.get_current_temperatures()
        tempOK = True
        
        for temp in [t for k,t in tempData.items() if 'tool' in k]:
            self._logger.debug(temp)
            tempOK = tempOK and (temp['actual'] <= self._cooldownTemp)

        return tempOK

    def _shutDown(self):
            self._printer.disconnect()

            while (not self._printer.is_closed_or_error()): 
                pass
            
            self._statePrinter = False
            self._stateLight = False

    def _findGPIOPin(self, pinName):
        for chip in gpiod.chip_iter():
            for line in chip.get_all_lines():
                if line.name == pinName:
                    self._logger.debug(f"Found Exact Match for GPIO \"{pinName}\"")
                    return GpioBundle(chip, line, pinName)
        
        self._logger.error(f"Could not find GPIO \"{pinName}\"")

    def _prepGPIOPin(self, gpioBundle):
        gpioBundle.line.request(GPIO_CONFIG)

    def _cleanupGpioPin(self, gpioBundle):
        gpioBundle.line.release()

    def _connectPrinter(self, callback):
        self._printer.connect()
        callback()

# ~~ Properties

    isPrinterOn = property(_getPrinterState, None, None,
                           "Represents the state of the printer relais")

    isLightOn = property(_getLightState, None, None,
                         "Represents the state of the light relais")

    def _getPrinterGPIO(self):
        return self._gpioPrinter.name

    def _setPrinterGPIO(self, pinName):
        if (None != self._gpioPrinter):
            self._cleanupGpioPin(self._gpioPrinter)
            self._gpioPrinter = None

        if (None == pinName): return
        newPrinterGpio = self._findGPIOPin(pinName)

        if (None != newPrinterGpio):
            self._gpioPrinter = newPrinterGpio
            self._prepGPIOPin(self._gpioPrinter)
            self._logger.info(
                f"New printer GPIO port is gpio {self._gpioPrinter.name} and it is {self._statePrinter}")

    printerGpio = property(_getPrinterGPIO, _setPrinterGPIO,
                           None, "The GPIO pin triggering the printer relais")

    def _getLightGPIO(self):
        return self._gpioLight.name

    def _setLightGPIO(self, pinName):
        if (None != self._gpioLight):
            self._cleanupGpioPin(self._gpioLight)
            self._gpioLight = None

        if (None == pinName): return
        newLightGpio = self._findGPIOPin(pinName)

        if (None != newLightGpio):
            self._gpioLight = newLightGpio
            self._stateLight = self._prepGPIOPin(self._gpioLight)
            self._logger.info(
                f"New light GPIO port is gpio {self._gpioLight.name} and it is {self._stateLight}")

    lightGpio = property(_getLightGPIO, _setLightGPIO, None,
                         "The GPIO pin triggering the light relais")

    def _getStartupTime(self):
        return self._startupTime

    def _setStartupTime(self, time):
        if ((type(time) == int) or (type(time) == str and time.isnumeric())) and (int(time) > 0):
            self._startupTime = int(time)
            self._logger.debug(f"Set printer startup time to {time} sec.")
        else:
            self._logger.warn(
                f"Could not assign '{time}' as printer startup time: Not a valid number > 0")

    startupTime = property(_getStartupTime, _setStartupTime,
                           None, "The startup time of the printer")

    def _getCooldownTemp(self):
        return self._cooldownTemp

    def _setCooldownTemp(self, temp):
        if ((type(temp) == int) or (type(temp) == str and temp.isnumeric())) and (int(temp) > 0):
            self._cooldownTemp = int(temp)
            self._logger.debug(
                f"Set cooldown nozzle temperature threshold to {temp}°C")
        else:
            self._logger.warn(
                f"Could not assign '{temp}' as the nozzle cool down temperature threshold: Not a valid number > 0")

    cooldownTemp = property(_getCooldownTemp, _setCooldownTemp,
                            None, "The nozzle cooldown temperature Threshold")

    def _getTurnOffAfterPrint(self):
        return self._turnOffAfterPrint

    def _setTurnOffAfterPrint(self, turnOff):
        self._turnOffAfterPrint = True if (turnOff) else False

    turnOffAfterPrint = property(_getTurnOffAfterPrint, _setTurnOffAfterPrint, None,
                                 "Default value if to turn off printer after print")

    @property
    def isCoolingDown(self):
        return (None != self._cooldownTimer)
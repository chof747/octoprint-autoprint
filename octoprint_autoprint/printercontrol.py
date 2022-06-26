from logging import Logger
import RPi.GPIO as GPIO
from time import sleep
from octoprint.printer import PrinterInterface
from octoprint.util import ResettableTimer

CONNECTION_WAIT = 1
CONNECTION_TIMEOUT_REPEAT = 5
TEMP_WAIT_CYCLE = 5

class PrinterControl:

    def __init__(self, logger: Logger, printer: PrinterInterface) -> None:
        self._statePrinter = False
        self._stateLight = False
        self._gpioPrinter = None
        self._gpioLight = None
        self._startupTime = None
        self._cooldownTemp = None
        self._autoprintFolder = None
        GPIO.setmode(GPIO.BCM)

        self._logger = logger
        self._printer = printer
        self._cooldownTimer = None

    def startUpPrinter(self) -> bool:
        """Command that starts up the printer and turns on the light"""

        self._switchPrinter(True)
        self._switchLight(True)

        connectTimer = ResettableTimer(self._startupTime, self._connectPrinter)        
        connectTimer.start();


    def shutDownPrinter(self):
        """Command that shutdowns the printer and turns off the light"""

        if (self._checkTemperatures()):
            self._cooldownTimer = None
            self._shutDown()
        else:
            self._logger.debug("Wait a few seconds for tool to cooldown")
            self._cooldownTimer = ResettableTimer(TEMP_WAIT_CYCLE, PrinterControl.shutDownPrinter, [self])
            self._cooldownTimer.start()

    def cancelShutDown(self):
        """Cancel a given shutdown command"""
        if (None != self._cooldownTimer):
            self._cooldownTimer.cancel();
            self._cooldownTimer = None;

    def toggleLight(self):
        """Command to toggle the state of the light"""
        self._switchLight(not self._stateLight)

# ~~ Private helper Methods

    def _checkTemperatures(self):
        tempData = self._printer.get_current_temperatures()
        tempOK = True
        
        for temp in [t for k,t in tempData.items() if 'tool' in k]:
            self._logger.debug(temp)
            tempOK = tempOK and (temp['actual'] <= self._cooldownTemp)

        return tempOK

    def _shutDown(self):
            self._printer.disconnect();

            while (not self._printer.is_closed_or_error()): 
                pass
            self._switchPrinter(False)
            self._switchLight(False)

    def _prepGPIOPin(self, pin) -> bool:
        GPIO.setup(pin, GPIO.IN)
        state = 1 == GPIO.input(pin)

        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, state)

        return state

    def _connectPrinter(self):
        self._printer.connect()

    def _switchLight(self, state):
        GPIO.output(self._gpioLight, state)
        self._logger.debug("Light turned %s" %
                           ("on" if state else "off"))
        self._stateLight = state

    def _switchPrinter(self, state):
        GPIO.output(self._gpioPrinter, state)
        self._logger.debug("Printer turned %s" %
                           ("on" if state else "off"))
        self._statePrinter = state

# ~~ Properties

    def _getPrinterState(self):
        return self._statePrinter

    isPrinterOn = property(_getPrinterState, None, None,
                           "Represents the state of the printer relais")

    def _getLightState(self):
        return self._stateLight

    isLightOn = property(_getLightState, None, None,
                         "Represents the state of the light relais")

    def _getPrinterGPIO(self):
        return self._gpioPrinter

    def _setPrinterGPIO(self, pin):
        if (None != self._gpioPrinter):
            GPIO.cleanup(self._gpioPrinter)
        self._gpioPrinter = int(pin)
        self._statePrinter = self._prepGPIOPin(self._gpioPrinter)
        self._logger.info(
            f"New printer GPIO port is gpio{self._gpioPrinter} and it is {self._statePrinter}")

    printerGpio = property(_getPrinterGPIO, _setPrinterGPIO,
                           None, "The GPIO pin triggering the printer relais")

    def _getLightGPIO(self):
        return self._gpioLight

    def _setLightGPIO(self, pin):
        if (None != self._gpioLight):
            GPIO.cleanup(self._gpioLight)
        self._gpioLight = int(pin)
        self._stateLight = self._prepGPIOPin(self._gpioLight)
        self._logger.info(
            f"New light GPIO port is gpio{self._gpioLight} and it is {self._stateLight}")

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

    @property
    def isCoolingDown(self):
        return (None != self._cooldownTimer)

    def _getAutoprintFolder(self):
        return self._autoprintFolder

    def _setAutoprintFolder(self, folder):
        if ("" != folder):
            self._autoprintFolder = folder
            self._logger.debug(
                f"Set the autoprint folder to {folder}")

    autoprintFolder = property(_getAutoprintFolder, _setAutoprintFolder, None,
                               "Folder where files are stored that can be used for automatic start")

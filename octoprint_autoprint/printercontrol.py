from logging import Logger
import RPi.GPIO as GPIO
from time import sleep
from octoprint.printer import PrinterInterface

CONNECTION_WAIT = 1
CONNECTION_TIMEOUT_REPEAT = 5

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

    def startUpPrinter(self) -> bool:
        """Command that starts up the printer and turns on the light"""
        self._switchPrinter(True)
        self._switchLight(True)
        
        sleep(self._startupTime)
        self._printer.connect()

        c = 0
        while (c<CONNECTION_TIMEOUT_REPEAT) and (not self._printer.is_operational()):
            sleep(CONNECTION_WAIT)

        if (self._printer.is_operational()):
            self._logger.info("Connected to printer")
            return True
        else:
            self._logger.warn("Printer connection could not be established immideately - try further actions later!")
            return False


    def shutDownPrinter(self):
        """Command that starts up the printer and turns on the light"""
        self._switchPrinter(False)
        self._switchLight(False)

    def toggleLight(self):
        """Command to toggle the state of the light"""
        self._switchLight(not self._stateLight)

# ~~ Private helper Methods

    def _prepGPIOPin(self, pin) -> bool:
        GPIO.setup(pin, GPIO.IN)
        state = 1 == GPIO.input(pin)

        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, state)

        return state

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

    def _getAutoprintFolder(self):
        return self._autoprintFolder

    def _setAutoprintFolder(self, folder):
        if ("" != folder):
            self._autoprintFolder = folder
            self._logger.debug(
                f"Set the autoprint folder to {folder}")

    autoprintFolder = property(_getAutoprintFolder, _setAutoprintFolder, None,
                               "Folder where files are stored that can be used for automatic start")

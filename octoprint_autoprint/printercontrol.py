from logging import Logger
import RPi.GPIO as GPIO


class PrinterControl:

    def __init__(self, logger: Logger) -> None:
        self._statePrinter = False
        self._stateLight = False
        self._gpioPrinter = None
        self._gpioLight = None
        GPIO.setmode(GPIO.BCM)

        self._logger = logger

    def startUpPrinter(self):
        """Command that starts up the printer and turns on the light"""
        GPIO.output(self._gpioPrinter, 1)
        self._logger.debug("Printer turned on")

        GPIO.output(self._gpioLight, 1)
        self._logger.debug("Light turned on")

        self._statePrinter = True;
        self._stateLight = True;

    def shutDownPrinter(self):
        """Command that starts up the printer and turns on the light"""
        GPIO.output(self._gpioPrinter, 0)
        self._logger.debug("Printer turned off")

        GPIO.output(self._gpioLight, 0)
        self._logger.debug("Light turned off")

        self._statePrinter = False;
        self._stateLight = False;

    def toggleLight(self):
        """Command to toggle the state of the light"""
        self._stateLight = not self._stateLight
        GPIO.output(self._gpioLight, self._stateLight)
        self._logger.debug("Light turned %s" % ("on" if self._stateLight else "off"))

    # ~~ Properties

    def _getPrinterState(self):
        return self._statePrinter

    isPrinterOn = property(_getPrinterState, None, None, "Represents the state of the printer relais")

    def _getLightState(self):
        return self._stateLight
    
    isLightOn = property(_getLightState, None, None, "Represents the state of the light relais")

    def _getPrinterGPIO(self):
        return self._gpioPrinter
    
    def _setPrinterGPIO(self, pin):
        if (None != self._gpioPrinter):
            GPIO.cleanup(self._gpioPrinter)
        self._gpioPrinter = int(pin)
        self._statePrinter = self._prepGPIOPin(self._gpioPrinter)
        self._logger.info(f"New printer GPIO port is gpio{self._gpioPrinter} and it is {self._statePrinter}")

    printerGpio = property(_getPrinterGPIO, _setPrinterGPIO, None, "The GPIO pin triggering the printer relais")

    def _getLightGPIO(self):
        return self._gpioLight
    
    def _setLightGPIO(self, pin):
        if (None != self._gpioLight):
            GPIO.cleanup(self._gpioLight)
        self._gpioLight = int(pin)
        self._stateLight = self._prepGPIOPin(self._gpioLight)
        self._logger.info(f"New light GPIO port is gpio{self._gpioLight} and it is {self._stateLight}")

    lightGpio = property(_getLightGPIO, _setLightGPIO, None, "The GPIO pin triggering the light relais")

    # ~~ Private helper Methods

    def _prepGPIOPin(self, pin) -> bool:
        GPIO.setup(pin, GPIO.IN)
        state = 1 == GPIO.input(pin)
        
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, state)

        return state

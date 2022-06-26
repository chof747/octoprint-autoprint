from octoprint.util import ResettableTimer
from octoprint.printer import PrinterInterface
from logging import Logger
from .printjob import PrintJob
from .printercontrol import PrinterControl



class AutoPrinterTimer:
    """
    Controller that waits until the time is ready and then starts the printer as well as the selected print
    """

    def __init__(self, printer: PrinterInterface, logger: Logger, printerControl : PrinterControl) -> None:
        self._logger = logger
        self._printer = printer
        self._controller = printerControl
        self._timer = None
        self._job = None
        self._printing = False

    def scheduleJob(self, job: PrintJob) -> bool:

        if (self._timer != None):
            self._timer.cancel()

        self._job = job
        self._timer = ResettableTimer(job.secondsToStart, self.startPrintJob)
        self._timer.start()


    def cancelJob(self) -> bool:

        if (self._timer != None):
            self._timer.cancel();
            self._timer = None
            self._job = None

    def processPrintJobEnd(self, printEvent: dict):
        if (self._printing) and (self._job != None) and (self._job.fileToPrint == printEvent.get("path")):
            self._controller.shutDownPrinter();
            
            
    def startPrintJob(self) -> None:

        if (not self._printer.is_operational()):
            if (self._controller.startUpPrinter()):
                self._printer.select_file(self._job.fileToPrint, False, True)
                self._printing = True
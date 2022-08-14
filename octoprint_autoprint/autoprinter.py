from time import sleep
from octoprint.util import ResettableTimer
from octoprint.printer import PrinterInterface
from logging import Logger
from .printjob import PrintJob
from .printercontrol import PrinterControl



class AutoPrinterTimer:
    """
    Controller that waits until the time is ready and then starts the printer as well as the selected print
    """

    def __init__(self, logger: Logger, printer: PrinterInterface, printerControl : PrinterControl) -> None:
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
        self._logger.info(f"Trigger  autoprint timer in {job.secondsToStart}")
        self._timer = ResettableTimer(job.secondsToStart, self.startPrintJob)
        self._timer.start()


    def cancelJob(self) -> bool:

        if (self._timer != None):
            self._timer.cancel();
            self._logger.info(f"Cancelling printjob for {self._job.fileToPrint} to be started in {self._job.secondsToStart} seconds.")
            self._timer = None
            self._job = None


    def processPrintJobEnd(self, printEvent: dict):
        if (self._printing) and (self._job != None) and (self._job.fileToPrint == printEvent.get("path")):
            self._logger.info("Printjob ended will %s the printer" % ("shutdown" if self._job.turnOffAfter else "leave on"))
            self._printing = False
            if self._job.turnOffAfter:
                self._controller.shutDownPrinter();
            
            self._timer = None
            self._job = None

            
    def startPrintJob(self) -> None:

        if (not self._printer.is_operational()):
            self._controller.startUpPrinter(self._runJob)
        else:
            self._controller.cancelShutDown();
            self._runJob()
    
    def _runJob(self) -> None:
            while not self._printer.is_operational():
                sleep(1)
            self._logger.info("Starting Print Job")
            self._printer.select_file(self._job.fileToPrint, False, True)
            self._printing = True

    def _getJob(self):
        return self._job

    job = property(_getJob, scheduleJob, None, "Job to be scheduled")

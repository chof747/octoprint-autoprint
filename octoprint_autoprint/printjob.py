from lib2to3.pygram import python_grammar_no_print_statement
from logging import Logger
from datetime import datetime, timedelta

from octoprint.filemanager import FileManager


class PrintJob:
    """
    Class representing a print job for the autoprint plugin
    """

    def __init__(self, file: str, time: datetime, turnoffAfter: bool, startFinish: str,
                 logger: Logger, fileManager: FileManager):
        self._logger = logger
        self._fileManager = fileManager

        self._jobFile = file
        self._time = time
        self._startTime = None
        self._turnOffAfter = turnoffAfter
        self.startFinish = startFinish

        self._calcStartTime()

    def _calcStartTime(self):
        duration = 0
        if ("finish" == self.startFinish):
            metadata = self._fileManager.get_metadata("local", self._jobFile)
            duration =metadata['analysis']['estimatedPrintTime']
            duration += 60 - (duration % 60)
            self._logger.info(f"Adjusting time by {duration} seconds to finish at {self._time.isoformat()}")

        self._startTime = self._time - timedelta(seconds=duration)
        if (self._startTime < datetime.now()):
            self._startTime = None
            raise PrintJobTooEarly()

    def __dict__(self):
        return {
            "file": self._jobFile,
            "time": self._time.timestamp()*1000,
            "startTime": self._startTime.timestamp()*1000
        }

class PrintJobTooEarly(Exception):
    pass

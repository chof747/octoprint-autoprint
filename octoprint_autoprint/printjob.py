from logging import Logger
from datetime import datetime, timedelta
from math import ceil
from datetime import datetime

from octoprint.filemanager import FileManager


class PrintJob:
    """
    Class representing a print job for the autoprint plugin
    """

    def __init__(self, file: str, time: datetime, turnoffAfter: bool, startFinish: str, startWithLights: bool,
                 logger: Logger, fileManager: FileManager):
        self._logger = logger
        self._fileManager = fileManager

        self._jobFile = file
        self._time = time
        self._startTime = None
        self._turnOffAfter = turnoffAfter
        self._startFinish = startFinish
        self._startWithLights = startWithLights
        
        if ("asap" != self._startFinish):
            self._calcStartTime()
        else:
            self._startTime = datetime.now()

    def _calcStartTime(self):
        duration = 0
        if ("finish" == self._startFinish):
            metadata = self._fileManager.get_metadata("local", self._jobFile)
            if ('analysis' in metadata) and ('estimatedPrintTime' in metadata['analysis']):
                duration =metadata['analysis']['estimatedPrintTime']
                duration += 60 - (duration % 60)
            else:
                self._logger.warn(f"No estimated print time available use time as start time!")
                duration = 0

            self._logger.info(f"Adjusting time by {duration} seconds to finish at {self._time.isoformat()}")

        self._startTime = self._time - timedelta(seconds=duration)
        if (self._startTime < datetime.now()):
            wrongtime = self._startTime
            self._startTime = None
            raise PrintJobTooEarly((datetime.now() - wrongtime).total_seconds() / 60);

    def __dict__(self):
        return {
            "file": self._jobFile,
            "time": self._time.timestamp()*1000,
            "startTime": self._startTime.timestamp()*1000,
            "turnOffAfter" : self._turnOffAfter
        }

    # ~Properties

    def _getSecondsToStart(self):
        if ("asap" == self._startFinish):
            return 0;
        else:
            return (self._startTime - datetime.now()).total_seconds()

    secondsToStart = property(_getSecondsToStart, None, None,
                            "The time in second until the printjob should start")

    def _isStartingWithLights(self):
        return True if self._startWithLights else False

    startWithLights = property(_isStartingWithLights, None, None,
                            "Determining if the printer should start with the lights on")

    def _getJobFile(self):
        return self._jobFile

    fileToPrint = property(_getJobFile, None, None,
                            "Filename of the file to print")

    def _setTurnOffAfter(self, turnOff) -> None:
        self._turnOffAfter = True if turnOff else False

    turnOffAfter = property(lambda self: self._turnOffAfter, _setTurnOffAfter)


class PrintJobTooEarly(Exception):

    def __init__(self, delay):

        delay_suitable = delay
        time_unit = "minutes"
        
        if (delay>=60*24):
            delay_suitable = ceil(delay / 60 /24 * 10) / 10
            time_unit = "days"
        if (delay>=120):
            delay_suitable = ceil(delay / 60)
            time_unit = "hours"

        self.message = f"Printjob is scheduled too early (move by {delay_suitable} {time_unit})."
        super().__init__(self.message)


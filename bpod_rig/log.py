import datetime
import logging
import shutil
import tempfile
from pathlib import Path

from bpod_rig.defaults import LOGFILE_PREFIX, TIME_FORMAT

logger = logging.getLogger(__name__)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "time": {
            "format": "%(asctime)s.%(msecs)d - [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%H:%M:%S",
        },
        "notime": {
            "format": "[%(levelname)s] %(name)s: %(message)s",
        },
    },
    "filters": {
        "stdout_filter": {
            "()": "bpod_rig.log.stdout_filter",
        }
    },
    "handlers": {
        "stdout": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "notime",
            "filters": ["stdout_filter"],
            "stream": "ext://sys.stdout",
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "ERROR",
            "formatter": "time",
            "stream": "ext://sys.stderr",
        },
        "dynamic_file": {
            "class": "bpod_rig.log.DynamicFileHandler",
            "formatter": "time",
        },
    },
    "loggers": {
        "": {
            "handlers": ["stdout", "stderr", "dynamic_file"],
            "level": "DEBUG",
            "propagate": True,
        }
    },
}


def stdout_filter():
    def filter(lf: logging.LogRecord) -> bool:  # noqa: A001
        return logging.ERROR > lf.levelno >= logging.INFO
        # If 40 > lf.levelno >= 20

    return filter


class DynamicFileHandler(logging.FileHandler):
    """Dynamic log file handler.

    When bpod-rig is initialized, the logging directory is not known.
    DynamicFileHandler creates a temporary file to output the initialization logging
    to. Once the logging directory is known, the output stream is swapped and the
    contents of the temp log copied over.

    Logfiles are created with each launch of bpod-rig. Logfiles are named based on
    the current ISO 8601-formatted date and time and a prefix.

        e.g.: bpod-YYYY-MM-DDTHH:MM:SS.log

    """

    def __init__(self):
        logger.debug("Opening temporary file stream")
        self.temp_stream = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="w", delete=False, suffix=".log"
        )
        self.log_dir: Path | None = None
        self.new_filepath: Path | None = None
        super().__init__(self.temp_stream.name)

    def __del__(self) -> None:
        self.temp_stream.close()
        self.close()

    def swap_stream(self, logging_dir: Path | str):
        """Swaps the temporary stream for a file in the logging_dir directory.

        This function takes a path to a logging directory, gets the new filename,
        swaps the filestream for the FileStreamHandler, copies any log entries over, and
        closes all the dangling streams.

        Parameters
        ----------
        logging_dir : Path | str
            Directory to store logfiles in

        Returns
        -------
            None
        """
        if isinstance(logging_dir, str):
            logging_dir = Path(logging_dir)

        if not logging_dir.exists():
            raise FileNotFoundError(f"Logging directory {logging_dir} does not exist!")

        self.log_dir = logging_dir
        logger.debug("Logging directory set to: %s", self.log_dir)
        if self.log_dir is None:
            raise TypeError("Logging directory is not specified!")

        self._set_new_filepath()
        # Determine what our new logfile name should be

        self.close()
        # Close current file stream and flush buffer

        if self.new_filepath is not None:
            shutil.copyfile(self.temp_stream.name, self.new_filepath)
            # Copy and rename the temp logfile
            self.stream = open(self.new_filepath, "a")  # NOQA SIM115
            # Open new stream and set to current stream

        self.temp_stream.close()  # Close the tempfile which should delete it

    def _set_new_filepath(self) -> None:
        current_dt = datetime.datetime.now().strftime(TIME_FORMAT)
        if self.log_dir is not None:
            self.new_filepath = self.log_dir / f"{LOGFILE_PREFIX}-{current_dt}.log"
            logger.debug("New logfile path set to: %s", self.new_filepath)


class BpodLogger(logging.Logger):
    """Bpod logger class.

    Small wrapper class to bring the "swap_stream" functionality of the
    DynamicFileHandler to the top level if it is present in the root logger handlers
    property.

    """

    def __init__(self, name: str):
        super().__init__(name)

        self.file_handler: DynamicFileHandler | None = None

        for handler in self.root.handlers:
            if isinstance(handler, DynamicFileHandler):
                self.file_handler = handler

    def swap_stream(self, logging_dir: Path | str):
        if self.file_handler:
            self.file_handler.swap_stream(logging_dir)
        else:
            raise AttributeError(
                "There is no DynamicFileHandler instance present for this logger!"
            )

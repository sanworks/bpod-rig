import atexit
import datetime
import logging
import shutil
import tempfile
from pathlib import Path

from bpod_rig.defaults import LOGFILE_PREFIX, TIME_FORMAT

# logger = logging.getLogger(__name__)

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


def get_log_config(debug: bool = False) -> dict:
    """Factory function to get logging configuration.

    If debug is True, DEBUG messages are passed through to stdout

    Parameters
    ----------
    debug : bool (optional)
        Flag to enable/disable debug messages in stdout

    Returns
    -------
        LOGGING_CONFIG: dict

    """
    if debug:
        LOGGING_CONFIG["handlers"]["stdout"]["level"] = "DEBUG"
        LOGGING_CONFIG["handlers"]["stdout"]["filters"] = ""

    return LOGGING_CONFIG


def stdout_filter():
    def filter(lf: logging.LogRecord) -> bool:  # noqa: A001
        return logging.ERROR > lf.levelno >= logging.INFO
        # If 40 > lf.levelno >= 20

    return filter


class DynamicFileHandler(logging.FileHandler):
    """Dynamic log file handler.

    When bpod-rig is initialized, the logging directory is not known.
    DynamicFileHandler creates a temporary file to output the initialization logging
    to. Once the logging directory is known, the contents of the temp log are copied
    over to the logging directory, and the output stream is swapped.

    Logfiles are created with each launch of bpod-rig. Logfiles are named based on
    the current date and time with a prefix:

        bpod-YYYY-MM-DD-HH-MM-SS.log

    """

    def __init__(self):
        atexit.register(self._cleanup)
        self.temp_stream = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="w", delete=False, suffix=".log"
        )
        self.log_dir: Path | None = None
        self.new_filepath: Path | None = None
        self.logger: logging.Logger | None = None
        super().__init__(self.temp_stream.name)

        self._set_new_filepath()
        # Determine what our new logfile name should be

    def _cleanup(self) -> None:
        if self.temp_stream is not None:
            self.temp_stream.close()
        if self.stream is not None:
            self.close()

    def swap_stream(self, logging_dir: Path | str):
        """Swaps the temporary stream for a file in the logging_dir directory.

        This function has multiple steps:
            1) checks for the existence of the logging directory
            2) stops the current stream to flush the buffer
            3) copies and renames the temporary logfile
            4) opens and sets the new FileHandler stream
            5) closes the temporary stream

        Parameters
        ----------
        logging_dir : Path | str
            Directory to store logfiles in

        Returns
        -------
            None
        """
        self.logger = logging.getLogger("temp_file_handler")

        if isinstance(logging_dir, str):
            logging_dir = Path(logging_dir)

        if not logging_dir.exists():
            raise FileNotFoundError(f"Logging directory {logging_dir} does not exist!")

        self.log_dir = logging_dir
        self.logger.debug("Logging directory set to: %s", self.log_dir)
        if self.log_dir is None:
            raise TypeError("Logging directory is not specified!")

        self.close()
        # Close current file stream and flush buffer

        if self.new_filepath is not None:
            shutil.copyfile(self.temp_stream.name, self.new_filepath)
            self.logger.debug(
                "Copying and renaming temp logfile to %s", self.new_filepath
            )
            # Copy and rename the temp logfile
            self.stream = open(self.new_filepath, "a")  # NOQA SIM115
            self.logger.debug("Opening new file stream")
            # Open new stream and set to current stream

        self.temp_stream.close()  # Close the tempfile which should delete it
        self.logger.debug("Closing temp file stream")

    def _set_new_filepath(self) -> None:
        current_dt = datetime.datetime.now().strftime(TIME_FORMAT)
        if self.log_dir is not None:
            self.new_filepath = self.log_dir / f"{LOGFILE_PREFIX}-{current_dt}.log"
            if self.logger is not None:
                self.logger.debug("New logfile path set to: %s", self.new_filepath)


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

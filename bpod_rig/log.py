import atexit
import datetime
import logging
import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any, cast

from bpod_rig.defaults import LOGFILE_PREFIX, TIME_FORMAT

LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
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


def get_log_config(*, debug: bool = False) -> dict:
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


def stdout_filter() -> Callable[[logging.LogRecord], bool]:
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

    def __init__(self) -> None:
        atexit.register(self._cleanup)
        self.temp_stream = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="w", delete=False, suffix=".log"
        )
        self.log_dir: Path | None = None
        self.new_filename: str | None = None
        self.logger: logging.Logger | None = None
        super().__init__(self.temp_stream.name)

        self._generate_filename()
        # Determine what our new logfile name should be

    def _cleanup(self) -> None:
        if self.temp_stream is not None:
            self.temp_stream.close()
        if self.stream is not None:
            self.close()

    def swap_stream(self, logging_dir: Path | str) -> None:
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
        self.logger = get_logger("temp_file_handler")

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

        if self.new_filename is not None:
            new_logfile_path = self.log_dir / self.new_filename
            shutil.copyfile(self.temp_stream.name, new_logfile_path)

            # Copy and rename the temp logfile
            self.stream = open(new_logfile_path, "a")  # NOQA SIM115
            self.logger.debug("Opening new file stream")
            self.logger.debug("Temp logfile copied and renamed to %s", new_logfile_path)
            # Open new stream and set to current stream

        self.temp_stream.close()  # Close the tempfile which should delete it
        self.logger.debug("Closing temp file stream")

    def _generate_filename(self) -> None:
        current_dt = datetime.datetime.now().strftime(TIME_FORMAT)
        self.new_filename = f"{LOGFILE_PREFIX}-{current_dt}.log"
        if self.logger is not None:
            self.logger.debug("New logfile path set to: %s", self.new_filename)


class BpodLogger(logging.Logger):
    """Bpod logger class.

    Small wrapper class to bring the "swap_stream" functionality of the
    DynamicFileHandler to the top level if it is present in the root logger handlers
    property.

    """

    def __init__(self, name: str) -> None:
        super().__init__(name)

        self.file_handler: DynamicFileHandler | None = None

        for handler in self.root.handlers:
            if isinstance(handler, DynamicFileHandler):
                self.file_handler = handler

    def swap_stream(self, logging_dir: Path | str) -> None:
        if self.file_handler:
            self.file_handler.swap_stream(logging_dir)
        else:
            raise AttributeError(
                "There is no DynamicFileHandler instance present for this logger!"
            )


def get_logger(name: str) -> BpodLogger:
    """Get a logger with a specific name and case its type to BpodLogger."""
    return cast("BpodLogger", logging.getLogger(name))

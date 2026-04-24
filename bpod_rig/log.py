import datetime
import logging
import shutil
import tempfile
from pathlib import Path

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "time": {
            "format": "%(asctime)s - [%(levelname)s] %(name)s: %(message)s",
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

    Currently, the naming convention for the currently used logfile will be:
        current-[date].log

    The DynamicFileHandler will automatically handle logfile naming, renaming, and
    selection using the criteria below.

    When swapping from the tempfile to a known logging directory, the DynamicFileHandler
    will choose the correct logfile by making several checks within the new self.log_dir
    directory:
        1) If no logfiles exist, a new logfile named current-[date].log is used
        2) If there are existing logfiles, but none contain the keyword `current`, a
        new logfile named current-[date].log is created
        3) If there is a logfile containing the keyword `current`, but the date is not
        today, the keyword `current` is removed from the name, leaving just
        [old_date].log Then, a new logfile named current-[date].log is created
        4) If there is a logfile with the name current-[date].log and [date] is today,
        that logfile is used
    """

    def __init__(self):
        self.temp_stream = tempfile.NamedTemporaryFile()  # noqa: SIM115
        self.log_dir: Path | None = None
        self.current_logfile: Path | None = None
        self.new_filepath: Path
        super().__init__(self.temp_stream.name)

    def __del__(self) -> None:
        self.temp_stream.close()
        self.stream.close()

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

        self.log_dir = logging_dir
        self._get_new_filepath()
        # Determine what our new logfile name should be

        old_stream = self.setStream(open(self.new_filepath, "a"))  # noqa: SIM115
        # Let's do this first so any remaining data is flushed from the stream
        # Set the stream to our new stream, which returns the old stream

        shutil.copyfile(self.temp_stream.name, self.new_filepath)
        # Copy contents of temporary logfile into our new logfile
        if old_stream is not None:
            old_stream.close()  # Close the old filestream
        self.temp_stream.close()  # Close the tempfile which should delete it

    def _get_new_filepath(self) -> None:
        """Function to help determine new logfile path.

        This function uses the current logfile, determines if the date in the name is
        old, triggers the file rename (if needed) and sets the self.new_filepath
        parameter

        Returns
        -------
            None
        """
        self._find_current_logfile()  # Is there a file with pattern current-[date].log?

        if self.current_logfile is not None:
            if self._current_file_from_past():
                # Most recent logfile is old, rename it and create new "current"
                self._rename_current_logfile()
                new_path = self._new_logfile_path()
                if new_path is not None:
                    self.new_filepath = new_path
            else:
                # Most recent logfile is current
                self.new_filepath = self.current_logfile
        else:
            # Catchall for a new log directory
            new_name = self._new_logfile_path()
            if new_name is not None:
                self.new_filepath = new_name

    def _find_current_logfile(self) -> None:
        """Checks self.log_dir for logfile matching the `current-[date].log` format."""
        if self.log_dir is None:
            return

        logfiles = self.log_dir.glob("*.log")
        current_logfile = [file for file in logfiles if "current" in file.name]
        if len(current_logfile) == 0:
            # There is no current logfile
            self.current_logfile = None
        else:
            # logfile with 'current' in name found
            self.current_logfile = current_logfile[0]

    def _current_file_from_past(self) -> bool | None:
        """Determines whether the date in a filename is from the past."""
        if self.current_logfile:
            date = self.current_logfile.stem.split("_")[1]
            file_date = datetime.date.fromisoformat(date)
            today_date = datetime.date.today()

            return file_date < today_date

        return None

    def _rename_current_logfile(self) -> None:
        """Removes 'current' from logfile by renaming.

        Takes the logfile with the name format "current-[date].log" and renames it
        to "[date].log"

        Returns
        -------
            None
        """
        if self.current_logfile is None:
            return

        date = self.current_logfile.stem.split("_")[1]
        new_name = self.current_logfile.with_stem(date)
        self.current_logfile.rename(new_name)

    def _new_logfile_path(self) -> Path | None:
        if self.log_dir is None:
            return None
        return self.log_dir.joinpath(f"current-{datetime.date.today()}.log")


class BpodLogger(logging.Logger):
    """Bpod logger class.

    Small wrapper class to bring the "swap_stream" functionality of the
    DynamicFileHandler to the top level if it is present in the root logger handlers
    property.

    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.file_handler: DynamicFileHandler | None = None

        for handler in self.root.handlers:
            if isinstance(handler, DynamicFileHandler):
                self.file_handler = handler

    def swap_stream(self, logging_dir: Path | str):
        if self.file_handler:
            self.file_handler.swap_stream(logging_dir)
        else:
            self.error(
                "There is no DynamicFileHandler instance present for this logger!"
            )

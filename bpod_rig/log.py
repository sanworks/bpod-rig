import datetime
import logging
import shutil
import tempfile
from pathlib import Path
from logging.config import dictConfig

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters':
        {
        'time':
            {
            'format': '%(asctime)s - [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%H:%M:%S',
            },
        'notime':
            {
                'format': '[%(levelname)s] %(name)s: %(message)s',
            }
        },
    'filters':
        {
            'stdout_filter':
                {
                    '()': 'bpod_rig.log.stdout_filter',
                }
        },
    'handlers':
        {
        'stdout':
            {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'notime',
            'filters': ['stdout_filter'],
            'stream': 'ext://sys.stdout'
            },
        'stderr':
            {
            'class': 'logging.StreamHandler',
            'level': 'ERROR',
            'formatter': 'time',
            'stream': 'ext://sys.stderr'
            },
        'dynamic_file':
            {
                'class': 'bpod_rig.log.DynamicFileHandler',
                'formatter': 'time',

            }
        },
    'loggers':
        {
        '':
            {
            'handlers': ['stdout', 'stderr', 'dynamic_file'],
            'level': 'DEBUG',
            'propagate': True
            }
        }
    }

def stdout_filter():
    def filter(lf: logging.LogRecord) -> bool:
        return logging.ERROR > lf.levelno >= logging.INFO
        # If 40 > lf.levelno >= 20
    return filter


class DynamicFileHandler(logging.FileHandler):
    """Dynamic log file handler.

    When bpod-rig is initialized, the logging directory is not known.
    DynamicFileHandler creates a temporary file to output the initialization logging
    to. Once the logging directory is known, the output stream is swapped and the
    contents of the temp log copied over.
    """

    def __init__(self):
        self.temp_stream = tempfile.NamedTemporaryFile()  # noqa: SIM115
        self.log_dir: Path | None = None
        self.current_logfile: Path | None = None
        self.new_filepath: Path | None = None
        super().__init__(self.temp_stream.name)


    def __del__(self) -> None:
        self.temp_stream.close()
        self.stream.close()

    def swap_stream(self, logging_dir: Path | str):
        if isinstance(logging_dir, str):
            logging_dir = Path(logging_dir)

        self.log_dir = logging_dir
        self._get_new_filepath()
        # Determine what our new logfile name should be

        old_stream = self.setStream(open(self.new_filepath, 'a'))
        # Let's do this first so any remaining data is flushed from the stream
        # Set the stream to our new stream, which returns the old stream

        shutil.copyfile(self.temp_stream.name, self.new_filepath)
        # Copy contents of temporary logfile into our new logfile

        old_stream.close() # Close the old filestream
        self.temp_stream.close() # Close the tempfile which should delete it


    def _get_new_filepath(self) -> None:
        self._find_current_logfile()  # Is there a file with pattern "current-[date].log"

        if self.current_logfile is not None:
            if self._current_file_from_past():
                # Most recent logfile is old, rename it and create new "current"
                self._rename_current_logfile()
                self.new_filepath = self._new_logfile_path()
            else:
                # Most recent logfile is current
                self.new_filepath = self.current_logfile
        else:
            # Catchall for a new log directory
            self.new_filepath = self._new_logfile_path()


    def _find_current_logfile(self):
        logfiles = self.log_dir.glob('*.log')
        current_logfile = [file for file in logfiles if "current" in file.name]
        if len(current_logfile) == 0:
            # There is no current logfile
            self.current_logfile = None
        else:
            # logfile with 'current' in name found
            self.current_logfile = current_logfile[0]


    def _current_file_from_past(self):
        date = self.current_logfile.stem.split("_")[1]
        file_date = datetime.date.fromisoformat(date)
        today_date = datetime.date.today()

        return file_date < today_date


    def _rename_current_logfile(self):
        """Removes 'current' from logfile by renaming.

        Takes the logfile with the name format "current-[date].log" and renames it
        to "[date].log"

        Returns
        -------
            None
        """
        date = self.current_logfile.stem.split("_")[1]
        new_name = self.current_logfile.with_stem(date)
        self.current_logfile.rename(new_name)


    def _new_logfile_path(self) -> Path:
        return self.log_dir.joinpath(f"current-{datetime.date.today()}.log")

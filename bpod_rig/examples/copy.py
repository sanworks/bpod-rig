import logging
import pathlib
import shutil

from bpod_rig import examples

logger = logging.getLogger(__name__)

def copy_examples(source_key: str, destination: pathlib.Path, override_contents: bool = False):
    source_modules = examples.__all__

    if source_key not in source_modules:
        raise ValueError(f"{source_key} is not a valid example source! \n"
                         f"Valid example sources are: {", ".join(examples.__all__)}"
                         )

    if not destination.exists():
        raise FileNotFoundError(f"{destination} does not exist!")

    logger.info("Copying %s files to %s", source_key, destination)

    destination_dir_contents = list(destination.iterdir())

    source_file_dir = pathlib.Path(source_modules[source_key].__path__[0])
    source_items = source_file_dir.iterdir()

    if len(destination_dir_contents) == 0 or override_contents:
        for cal_file in source_items:
            try:
                logger.debug("Attempting to copy %s to %s...", cal_file, destination)
                shutil.copy2(cal_file, destination)
            except Exception as e:  # NOQA PERF203
                logger.error("Error copying %s!", cal_file)
                raise e

import logging
import pathlib
import shutil

from bpod_rig import examples, log

logger = log.get_logger(__name__)


def copy_examples(
    source_key: str, destination: pathlib.Path, *, override_contents: bool = False
) -> None:
    source_modules = examples.__all__

    if source_key not in source_modules:
        raise ValueError(
            f"{source_key} is not a valid example source! \n"
            f"Valid example sources are: {{",
            ".join(source_modules)}}",
        )

    if not destination.exists():
        raise FileNotFoundError(f"{destination} does not exist!")

    logger.info("Copying %s files to %s", source_key, destination)

    destination_dir_contents = list(destination.iterdir())
    # Since we verified source_Key is in __all__, this folder must exist
    source_file_dir = pathlib.Path(examples.__path__[0]) / source_key
    source_items = source_file_dir.iterdir()

    if len(destination_dir_contents) == 0 or override_contents:
        for file in source_items:
            try:
                logger.debug("Attempting to copy %s to %s...", file, destination)
                shutil.copy2(file, destination)
            except Exception:  # noqa: PERF203
                logger.exception("Error copying %s!", file)
                raise

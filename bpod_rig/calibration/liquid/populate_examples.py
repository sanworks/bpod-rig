"""Create the example liquid calibration JSON with 8 vales and dummy measurements."""
from pathlib import Path

from bpod_rig.examples import calibration as example_folder
from .utils import create_default_json

def main():
    """Create the example liquid calibration JSON with 8 vales and dummy measurements."""
    example_json = create_default_json()
    example_path = Path(example_folder.__path__[0]) / "LiquidCalibration.json"
    example_path.write_text(example_json)

if __name__ == "__main__":
    main()

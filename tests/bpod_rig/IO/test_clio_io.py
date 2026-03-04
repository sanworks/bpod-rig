import logging
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner
from unittest.mock import patch
from bpod_rig.IO.cli_io import yes_no_prompt, prompt_for_path


class TestCliIO:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.exists_path = self.temp_path / "exists"
        self.exists_path.mkdir(parents=True)
        self.dne_path = self.temp_path / "dne"

        self.runner = CliRunner()

        yield  # test runs here

        self.temp_dir.cleanup()

    def test_yes_no_prompt(self, caplog):
        y1 = self.runner.invoke(
            yes_no_prompt, ["Testing..."], input="Y", standalone_mode=False
        )
        assert y1.return_value == True
        assert y1.exit_code == 0
        assert "Testing..." in y1.output

        y2 = self.runner.invoke(
            yes_no_prompt, ["Testing..."], input="y", standalone_mode=False
        )
        assert y1.return_value == True
        assert y2.exit_code == 0
        assert "Testing..." in y2.output

        n1 = self.runner.invoke(
            yes_no_prompt, ["Testing..."], input="N", standalone_mode=False
        )
        assert n1.return_value == False
        assert n1.exit_code == 0
        assert "Testing..." in n1.output

        n2 = self.runner.invoke(
            yes_no_prompt, ["Testing..."], input="n", standalone_mode=False
        )
        assert n2.return_value == False
        assert n2.exit_code == 0
        assert "Testing..." in n2.output

        garbage = self.runner.invoke(
            yes_no_prompt, ["Testing..."], input="asdfasdf", standalone_mode=False
        )
        assert "invalid" in garbage.output

        with patch("bpod_rig.IO.cli_io.yes_no_prompt", side_effect=KeyboardInterrupt):
            # patch to force a KeyboardInterrupt
            with caplog.at_level(logging.DEBUG):
                # Capture the logging to make sure 'aborted' is output
                early = self.runner.invoke(
                    yes_no_prompt,
                    ["Testing..."],
                    input="",
                    standalone_mode=False,
                )

                assert early.return_value == False
                assert "aborted" in caplog.text

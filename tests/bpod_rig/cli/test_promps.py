import logging
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from bpod_rig.cli.prompts import prompt_for_path_cli_runner, yes_no_prompt_cli_runner


class TestCliIO:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.exists_path = self.temp_path / "exists"
        self.exists_path.mkdir(parents=True)
        self.temp_file = self.temp_path.joinpath("test.txt")
        self.temp_file.write_text("Test")
        # For some reason tempfile.NamedTemporaryFile does not work here
        self.runner = CliRunner()

        yield  # test runs here

        self.temp_file.unlink()
        self.temp_dir.cleanup()

    def test_yes_no_prompt(self, caplog):
        y1 = self.runner.invoke(
            yes_no_prompt_cli_runner, ["Testing..."], input="Y", standalone_mode=False
        )
        assert y1.return_value
        assert y1.exit_code == 0
        assert "Testing..." in y1.output

        y2 = self.runner.invoke(
            yes_no_prompt_cli_runner, ["Testing..."], input="y", standalone_mode=False
        )
        assert y1.return_value
        assert y2.exit_code == 0
        assert "Testing..." in y2.output

        n1 = self.runner.invoke(
            yes_no_prompt_cli_runner, ["Testing..."], input="N", standalone_mode=False
        )
        assert not n1.return_value
        assert n1.exit_code == 0
        assert "Testing..." in n1.output

        n2 = self.runner.invoke(
            yes_no_prompt_cli_runner, ["Testing..."], input="n", standalone_mode=False
        )
        assert not n2.return_value
        assert n2.exit_code == 0
        assert "Testing..." in n2.output

        garbage = self.runner.invoke(
            yes_no_prompt_cli_runner,
            ["Testing..."],
            input="asdfasdf",
            standalone_mode=False,
        )
        assert "invalid" in garbage.output

        with patch(
            "bpod_rig.IO.cli_io.yes_no_prompt_cli_runner", side_effect=KeyboardInterrupt
        ) and caplog.at_level(logging.DEBUG):
            # patch to force a KeyboardInterrupt
            # Capture the logging to make sure 'aborted' is output
            early = self.runner.invoke(
                yes_no_prompt_cli_runner,
                ["Testing..."],
                input="",
                standalone_mode=False,
            )

            assert early.return_value is None
            assert "aborted" in caplog.text

    def test_prompt_for_path(self, caplog):

        exists = self.runner.invoke(
            prompt_for_path_cli_runner,
            ["Testing..."],
            input=f"{self.exists_path}",
            standalone_mode=False,
        )
        assert exists.exit_code == 0
        assert "Testing..." in exists.output
        assert exists.return_value == self.exists_path
        assert isinstance(exists.return_value, Path)

        dne = self.runner.invoke(
            prompt_for_path_cli_runner,
            ["Testing..."],
            input=f"{self.temp_file}",
            standalone_mode=False,
        )

        assert dne.exit_code == 0
        assert "Testing..." in dne.output
        assert "is a file" in dne.output

        with patch(
            "bpod_rig.IO.cli_io.prompt_for_path_cli_runner",
            side_effect=KeyboardInterrupt,
        ) and caplog.at_level(logging.DEBUG):
            # patch to force a KeyboardInterrupt
            # Capture the logging to make sure 'aborted' is output
            early = self.runner.invoke(
                prompt_for_path_cli_runner,
                ["Testing..."],
                input="",
                standalone_mode=False,
            )

            assert early.return_value is None
            assert "aborted" in caplog.text

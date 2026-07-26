import logging
import tempfile
from collections.abc import Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from bpod_rig.cli.prompts import app as prompt_app


class TestCliIO:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> Generator[None, None, None]:
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

    def test_yes_no_prompt(self, caplog: pytest.LogCaptureFixture) -> None:
        y1 = self.runner.invoke(
            prompt_app,
            ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
            input="Y\n",
        )

        assert y1.exit_code == 0
        assert "Testing..." in y1.output

        y2 = self.runner.invoke(
            prompt_app,
            ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
            input="y\n",
        )
        # assert y1.return_value
        assert y2.exit_code == 0
        assert "Testing..." in y2.output

        n1 = self.runner.invoke(
            prompt_app,
            ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
            input="N\n",
        )
        # assert not n1.return_value
        assert n1.exit_code == 0
        assert "Testing..." in n1.output

        n2 = self.runner.invoke(
            prompt_app,
            ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
            input="n\n",
        )
        # assert not n2.return_value
        assert n2.exit_code == 0
        assert "Testing..." in n2.output

        garbage = self.runner.invoke(
            prompt_app,
            ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
            input="asdfasdf\n",
        )
        assert "invalid" in garbage.output

        with patch(
            "bpod_rig.IO.cli_io.prompt_app", side_effect=KeyboardInterrupt
        ) and caplog.at_level(logging.DEBUG):
            # patch to force a KeyboardInterrupt
            # Capture the logging to make sure 'aborted' is output
            self.runner.invoke(
                prompt_app,
                ["yes-no-prompt-cli-runner", "--prompt", "Testing..."],
                input="",
                standalone_mode=False,
            )

            # assert early.return_value is None
            assert "aborted" in caplog.text

    def test_prompt_for_path(self, caplog: pytest.LogCaptureFixture) -> None:

        exists = self.runner.invoke(
            prompt_app,
            ["prompt-for-path-cli-runner", "--prompt", "Testing..."],
            input=f"{self.exists_path}\n",
            standalone_mode=False,
        )
        assert exists.exit_code == 0
        assert "Testing..." in exists.output
        # assert exists.return_value == self.exists_path
        # assert isinstance(exists.return_value, Path)

        dne = self.runner.invoke(
            prompt_app,
            ["prompt-for-path-cli-runner", "--prompt", "Testing..."],
            input=f"{self.temp_file}\n",
            standalone_mode=False,
        )

        assert dne.exit_code == 0
        assert "Testing..." in dne.output
        assert "Directory was requested but a file was provided" in dne.output

        with patch(
            "bpod_rig.IO.cli_io.prompt_app",
            side_effect=KeyboardInterrupt,
        ) and caplog.at_level(logging.DEBUG):
            # patch to force a KeyboardInterrupt
            # Capture the logging to make sure 'aborted' is output
            self.runner.invoke(
                prompt_app,
                ["prompt-for-path-cli-runner", "--prompt", "Testing..."],
                input="\n",
            )

            # assert early.return_value is None
            assert "aborted" in caplog.text

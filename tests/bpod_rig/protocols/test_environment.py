"""Tests for protocol execution environment."""

from pathlib import Path

import pytest

from bpod_rig.protocols.environment import (
    load_protocol_function,
    run_protocol_async,
)


@pytest.fixture
def temp_protocol_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a temporary directory with a simple test protocol."""
    protocol_dir = tmp_path_factory.mktemp("test_protocol")
    protocol_file = protocol_dir / "test_protocol.py"
    protocol_file.write_text(
        """
import sys
from pathlib import Path
from unittest.mock import MagicMock
import bpod_rig

# Mock bpod_core.bpod module if not installed
try:
    from bpod_core.bpod import Bpod
except ImportError:
    sys.modules['bpod_core'] = MagicMock()
    sys.modules['bpod_core.bpod'] = MagicMock()

# Try import a util func
try:
    from .util import helper_function
    helper_function()
    print("Imported with relative import")
except ImportError:
    print("Failed to import with relative import")



def test_protocol(bpod):
    '''Test protocol function that prints working directory and args.'''
    # Print current working directory to verify it's set correctly
    print(f"CWD: {Path.cwd()}")
    
    # Print arguments passed
    print(f"Args: {sys.argv[1:]}")
    
    # Protocol runs successfully
"""
    )
    util_file = protocol_dir / "util.py"
    util_file.write_text(
        """
def helper_function():
    return "Helper function output"
"""
    )
    return protocol_file


@pytest.fixture
def failing_protocol_path(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create a protocol that fails."""
    protocol_dir = tmp_path_factory.mktemp("failing_protocols")
    protocol_file = protocol_dir / "failing_protocol.py"
    protocol_file.write_text(
        """
import sys
def failing_protocol(bpod_session):
    print("About to fail...")
    sys.exit(1)
"""
    )
    return protocol_file


@pytest.fixture
def session_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Create an independent temporary working directory."""
    return tmp_path_factory.mktemp("work_dir")


class TestLoadProtocolFunction:
    def test_invalid_protocol_name(self, temp_protocol_path: Path):
        """Test error when protocol function name doesn't match file name."""
        # Create a protocol file with a mismatched function name
        mismatched_protocol = temp_protocol_path.parent / "mismatched_protocol.py"
        mismatched_protocol.write_text(
            """
def wrong_name(bpod):
    pass
"""
        )

        with pytest.raises(
            AttributeError, match="Protocol function 'mismatched_protocol' not found"
        ):
            load_protocol_function(mismatched_protocol)

    def test_nonexistent_protocol_file(self):
        """Test error when protocol file doesn't exist."""
        with pytest.raises(FileNotFoundError, match="Protocol file not found"):
            load_protocol_function(Path("/nonexistent/protocol.py"))

    def test_valid_protocol_function(self, temp_protocol_path: Path):
        """Test successful loading of a valid protocol function."""
        protocol_function = load_protocol_function(temp_protocol_path)
        assert callable(protocol_function), (
            "Loaded protocol function should be callable"
        )


class TestRunProtocolAsync:
    def test_run_protocol_async(self, temp_protocol_path: Path, session_dir: Path):
        """Test asynchronous protocol execution."""
        protocol_path = temp_protocol_path

        process = run_protocol_async(
            protocol_path=protocol_path, session_dir=session_dir
        )

        # Wait for completion
        stdout, stderr = process.communicate(timeout=5)

        # Print stderr if test fails for debugging
        if process.returncode != 0:
            print(f"STDERR: {stderr}")
            print(f"STDOUT: {stdout}")

        assert process.returncode == 0, f"Process failed with stderr: {stderr}"
        assert f"CWD: {protocol_path.parent}" in stdout
        # assert "Imported with relative import" in stdout

    def test_run_protocol_async_with_args(
        self, temp_protocol_path: Path, session_dir: Path
    ):
        """Test async execution with arguments."""
        protocol_path = temp_protocol_path

        process = run_protocol_async(
            protocol_path=protocol_path,
            session_dir=session_dir,
            protocol_args=["--some-param", "test_arg"],
        )

        stdout, stderr = process.communicate(timeout=5)

        # Print stderr if test fails for debugging
        if process.returncode != 0:
            print(f"STDERR: {stderr}")
            print(f"STDOUT: {stdout}")

        assert process.returncode == 0, f"Process failed with stderr: {stderr}"
        assert "Args: ['--some-param', 'test_arg']" in stdout

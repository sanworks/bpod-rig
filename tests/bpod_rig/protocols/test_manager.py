"""Test loading and finding protocol."""

from collections.abc import Generator
from pathlib import Path

import pytest

from bpod_rig.protocols.manager import ProtocolManager


def create_test_protocols_folder(root_path: Path):
    """Initialize test environment with protocol directory structure.

    Creates the following structure:
    protocol_folder/
        Protocol_unique1/
            Protocol_unique1.py
        Protocol_unique2/
            Protocol_unique2.py
        Protocol_invalid1_x/
            Protocol_invalid1.py
        subfolderA/
            Protocol_matching1/
                Protocol_matching1.py
            Protocol_matching2/
                Protocol_matching2.py
        subfolderB/
            Protocol_matching1/
                Protocol_matching1.py
            Protocol_matching2/
                Protocol_matching2.py
            Protocol_unique3/
                Protocol_unique3.py
    """
    protocol_folder = root_path / "protocols"
    protocol_folder.mkdir(parents=True, exist_ok=True)

    def create_protocol_file(*path: str) -> Path:
        protocol_name = path[-1]
        dir_path = protocol_folder.joinpath(*path[:-1])
        dir_path.mkdir(parents=True, exist_ok=True)

        protocol_file = dir_path / f"{protocol_name}.py"
        protocol_file.write_text("def protocol(bpod_session):\n    pass\n")
        return protocol_file

    # Create Protocol_unique1
    create_protocol_file("Protocol_unique1", "Protocol_unique1")
    create_protocol_file("Protocol_unique2", "Protocol_unique2")
    create_protocol_file("Protocol_invalid1_x", "Protocol_invalid1")

    # Create subfolderA protocols
    create_protocol_file("subfolderA", "Protocol_matching1", "Protocol_matching1")
    create_protocol_file("subfolderA", "Protocol_matching2", "Protocol_matching2")

    # Create subfolderB protocols
    create_protocol_file("subfolderB", "Protocol_matching1", "Protocol_matching1")
    create_protocol_file("subfolderB", "Protocol_matching2", "Protocol_matching2")
    create_protocol_file("subfolderB", "Protocol_unique3", "Protocol_unique3")


@pytest.fixture(scope="function")
def protocol_folder(
    tmp_path_factory: pytest.TempPathFactory,
) -> Generator[Path, None, None]:
    """Setup test environment once for all tests."""
    root_path = tmp_path_factory.mktemp("protocol_manager_tests")
    create_test_protocols_folder(root_path)
    yield root_path / "protocols"
    # Cleanup happens automatically with tmp_path_factory


class TestFindProtocolFile:
    """Test suite for finding protocol files."""

    def test_basic_find(self, protocol_folder):
        """Test finding a unique protocol at the root level."""
        expected_path = protocol_folder / "Protocol_unique1" / "Protocol_unique1.py"

        manager = ProtocolManager(protocol_folder)
        result_path = manager.find_protocol_file("Protocol_unique1")

        assert result_path == expected_path

    def test_no_match_fail(self, protocol_folder):
        """Test that an error is raised when no match is found."""
        manager = ProtocolManager(protocol_folder)
        with pytest.raises(
            FileNotFoundError, match="Protocol 'Protocol_noMatch' not found"
        ):
            manager.find_protocol_file("Protocol_noMatch")

    def test_invalid_match_fail(self, protocol_folder):
        """Test that an error is raised when a file matches but is invalid."""
        manager = ProtocolManager(protocol_folder)
        with pytest.raises(
            FileNotFoundError, match="Protocol 'Protocol_invalid1' not found"
        ):
            manager.find_protocol_file("Protocol_invalid1")

    def test_subfolder_find(self, protocol_folder):
        """Test finding a protocol in a subfolder."""
        expected_path = (
            protocol_folder / "subfolderB" / "Protocol_unique3" / "Protocol_unique3.py"
        )

        manager = ProtocolManager(protocol_folder)
        result_path = manager.find_protocol_file("Protocol_unique3")

        assert result_path == expected_path

    def test_ambiguous_match_unix(self, protocol_folder):
        """Test with a UNIX-style path to resolve ambiguity."""
        expected_path = (
            protocol_folder
            / "subfolderA"
            / "Protocol_matching1"
            / "Protocol_matching1.py"
        )

        manager = ProtocolManager(protocol_folder)
        result_path = manager.find_protocol_file("subfolderA/Protocol_matching1")

        assert result_path == expected_path

    def test_ambiguous_match_win(self, protocol_folder):
        """Test with a Windows-style path to resolve ambiguity."""
        expected_path = (
            protocol_folder
            / "subfolderA"
            / "Protocol_matching1"
            / "Protocol_matching1.py"
        )

        manager = ProtocolManager(protocol_folder)
        result_path = manager.find_protocol_file(r"subfolderA\Protocol_matching1")

        assert result_path == expected_path

    def test_ambiguous_match_subfolder(self, protocol_folder):
        """Test with a subfolder path that has multiple matches."""
        expected_path = (
            protocol_folder
            / "subfolderA"
            / "Protocol_matching2"
            / "Protocol_matching2.py"
        )

        manager = ProtocolManager(protocol_folder)
        result_path = manager.find_protocol_file("subfolderA/Protocol_matching2")

        assert result_path == expected_path

    def test_ambiguous_match_fail(self, protocol_folder):
        """Test that an error is raised when there are multiple matches."""
        manager = ProtocolManager(protocol_folder)
        with pytest.raises(
            ValueError, match="Multiple protocols found.*Protocol_matching1"
        ):
            manager.find_protocol_file("Protocol_matching1")

    def test_subfolder_ambiguous_match_fail(self, protocol_folder):
        """Test that an error is raised for multiple matches across subfolders."""
        manager = ProtocolManager(protocol_folder)
        with pytest.raises(
            ValueError, match="Multiple protocols found.*Protocol_matching2"
        ):
            manager.find_protocol_file("Protocol_matching2")


class TestProtocolManager:
    def test_initialization(self, protocol_folder):
        """Test that the ProtocolManager initializes without error."""
        manager = ProtocolManager(protocol_folder)
        assert manager.protocol_dir == protocol_folder

    def test_nonexistent_directory(self):
        """Test that initializing with a nonexistent directory raises an error."""
        non_existent_path = Path("/path/does/not/exist")
        with pytest.raises(
            FileNotFoundError, match="Protocol directory .* does not exist."
        ):
            ProtocolManager(non_existent_path)

    def test_load_protocols(self, protocol_folder):
        manager = ProtocolManager(protocol_folder)
        assert len(manager.protocols) == 7

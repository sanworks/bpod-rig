"""Find and manage protocol files in the Bpod protocol directory."""

from pathlib import Path


class ProtocolManager:
    """Class to manage protocols and their associated files."""

    protocols: set[Path]

    def __init__(self, protocol_dir: Path):
        if not protocol_dir.exists():
            raise FileNotFoundError(
                f"Protocol directory {protocol_dir} does not exist."
            )
        self.protocol_dir = protocol_dir
        self.load_protocols()

    def load_protocols(self):
        """Load protocols from the protocol directory."""
        # Expect protocols to be in a subfolder with the same name as the protocol file
        self.protocols = set()
        for protocol_file in self.protocol_dir.glob("**/*/*.py"):
            if protocol_file.stem == protocol_file.parent.name:
                self.protocols.add(protocol_file.absolute())

    def find_protocol_file(self, protocol_name: str) -> Path:
        r"""Find a protocol file in the protocol directory.

        Searches for a protocol file matching the given name. The protocol file
        should be located in a directory structure like:
            protocol_dir/[subfolder]/protocol_name/protocol_name.py

        If the protocol_name includes path separators (/ or \), they are used
        to narrow the search to a specific subfolder.

        Parameters
        ----------
        protocol_name : str
            Name of the protocol to find. Can include subfolder
            path (e.g., 'subfolderA/Protocol_name' or 'subfolderA\\Protocol_name')

        Returns
        -------
        Path to the protocol file

        Raises
        ------
            FileNotFoundError: If no matching protocol is found
            ValueError: If multiple matching protocols are found (ambiguous)

        Examples
        --------
            >>> manager = ProtocolManager(Path("/protocols"))
            >>> manager.find_protocol_file("MyProtocol")
            Path("/protocols/MyProtocol/MyProtocol.py")
            >>> manager.find_protocol_file("subfolder/MyProtocol")
            Path("/protocols/subfolder/MyProtocol/MyProtocol.py")
        """
        # Normalize path separators to use forward slashes
        protocol_name_normalized = protocol_name.replace("\\", "/")

        # Split into path components
        protocol_basename = protocol_name_normalized.split("/")[-1]
        matches = []
        for protocol_file in self.protocols:
            if protocol_file.match(
                f"*/{protocol_name_normalized}/{protocol_basename}.py"
            ):
                matches.append(protocol_file)

        if len(matches) == 0:
            raise FileNotFoundError(
                f"Protocol '{protocol_name}' not found in {self.protocol_dir}"
            )
        if len(matches) > 1:
            match_paths = "\n  ".join(str(m) for m in matches)
            raise ValueError(
                f"Multiple protocols found matching '{protocol_name}':\n"
                f"      {match_paths}\n"
                f"Please provide a more specific path ",
                f"(e.g., 'subfolder/{protocol_name}')",
            )
        return matches[0]

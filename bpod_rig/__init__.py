import importlib.metadata

from .protocols.session import get_session

__version__ = importlib.metadata.version("bpod-rig")

__all__ = ["get_session"]

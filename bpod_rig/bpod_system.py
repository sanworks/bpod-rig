"""BpodSystem class to provide parameter access in a protocol"""

from __future__ import annotations
import logging
import warnings
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Callable

from bpod_core.bpod import Bpod, BpodError, RemoteBpod
from serial import SerialException

from bpod_rig.config.system_settings import SystemSettings
from bpod_rig.utils import get_func_params

class BpodSystem:
    def __init__(self, *args, **kwargs):
        self.logger = logging.getLogger(__name__)
        self._args = args
        self._kwargs = kwargs

        self.bpod: Bpod | None = None
        self.system_settings: SystemSettings | None = None
        self.session_params: dict | None = None
        self.gui_handles: None = None

        self.session_dir: Path | None = None

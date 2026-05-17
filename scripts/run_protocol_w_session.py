import logging
from logging.config import dictConfig
from typing import cast
import time

from bpod_rig.log import get_log_config, BpodLogger
from bpod_rig.session import BpodSession

DEBUG=True

# Set up logging here
logging_config = get_log_config(DEBUG)
dictConfig(logging_config)
logging.setLoggerClass(BpodLogger)
logger: BpodLogger = cast(BpodLogger, logging.getLogger(__name__))

from bpod_rig.examples.protocols.light_2afc_protocol import example_light_2afc_protocol, example_light_2afc_protocol_bpodprotocol

with BpodSession() as bps:
    bps.set_protocol(example_light_2afc_protocol.protocol)
    print(bps.protocol.name)
    bps.set_protocol(example_light_2afc_protocol_bpodprotocol.Light2AFCProtocol)
    print(bps.protocol.name)

"""Openworld Ocean Palace Security Esplanade"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Ocean Palace Security Esplanade"""

    loc_id = ctenums.LocID.OCEAN_PALACE_SECURITY_ESPLANADE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Security Esplanade Event.
        - Modify PCs to have the same arbitrary functions and modify calls.
        """

        # Copying Crono because the rest have linked functions which will break.
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 7)
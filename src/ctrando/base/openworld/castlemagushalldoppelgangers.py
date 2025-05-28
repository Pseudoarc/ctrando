"""Openworld Castle Magus Hall of Doppelgangers"""

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
    """EventMod for Castle Magus Hall of Doppelgangers"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_DOPPLEGANGER_CORRIDOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Hall of Doppelgangers for an Open World.
        - TODO: Get crazy and add some special fights for Magus (Schala) and
                Ayla (Kino)
        """

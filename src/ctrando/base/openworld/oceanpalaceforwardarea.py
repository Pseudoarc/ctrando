"""Openworld Ocean Forward Area"""

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
    """EventMod for Ocean Forward Area"""

    loc_id = ctenums.LocID.OCEAN_PALACE_FORWARD_AREA

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Forward Area Event.
        - Add Magus to the location
        """

        # Copying Crono because the rest have linked functions which will break.
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 7)

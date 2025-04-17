"""Openworld Blackbird Right Port"""

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
    """EventMod for Blackbird Barracks"""
    loc_id = ctenums.LocID.BLACKBIRD_RIGHT_PORT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Blackbird Barracks for an Open World.
        - Add Crono and Magus to the map.
        """
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 6)
        owu.insert_pc_object(script, ctenums.CharID.CRONO, 1, 1)
        owu.add_exploremode_to_partyfollows(script)

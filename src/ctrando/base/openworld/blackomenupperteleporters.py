"""Openworld Black Omen Upper Teleporters"""
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
    """EventMod for Black Omen Upper Teleporters"""
    loc_id = ctenums.LocID.BLACK_OMEN_UPPER_TELEPORTERS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen Upper Teleporters for an Open World.
        - Restore Exploremode after warping in.
        """
        owu.add_exploremode_to_partyfollows(script)
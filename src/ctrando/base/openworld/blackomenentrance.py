"""Openworld Black Omen Entrance"""
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
    """EventMod for Black Omen Entrance"""
    loc_id = ctenums.LocID.BLACK_OMEN_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen Entrance for an Open World.
        - Add exploremode after partyfollows: leave epoch, open door, nu catapult
        """

        # Fix partyfollows
        owu.add_exploremode_to_partyfollows(script)

"""Openworld Black Omen Elder Spawn"""
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
    """EventMod for Black Omen Elder Spawn"""

    loc_id = ctenums.LocID.BLACK_OMEN_ELDER_SPAWN

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen Elder Spawn for an Open World.
        - Restore Exploremode after boss fight.
        """
        owu.add_exploremode_to_partyfollows(script)

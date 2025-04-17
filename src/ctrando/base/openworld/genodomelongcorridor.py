"""Openworld Geno Dome Long Corridor"""

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
    """EventMod for Geno Dome Long Corridor"""
    loc_id = ctenums.LocID.GENO_DOME_LONG_CORRIDOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Long Corridor for an Open World.
        - Normalize power tab pickup
        """
        owu.update_add_item(
            script,
            script.get_function_start(8, FID.ACTIVATE)
        )
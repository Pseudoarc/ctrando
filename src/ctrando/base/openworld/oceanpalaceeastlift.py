"""Openworld Ocean Palace Eastern Access Lift"""

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
    """EventMod for Ocean Palace Eastern Access Lift"""
    loc_id = ctenums.LocID.OCEAN_PALACE_EASTERN_ACCESS_LIFT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ocean Palace Eastern Access Lift for an Open World.
        - Modify magic tab pickup.
        """

        owu.update_add_item(script, script.get_function_start(8, FID.ACTIVATE))
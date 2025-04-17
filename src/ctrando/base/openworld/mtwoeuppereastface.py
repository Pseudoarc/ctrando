"""Openworld Mt. Woe Upper East Face"""

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
    """EventMod for Mt. Woe Upper East Face"""
    loc_id = ctenums.LocID.MT_WOE_UPPER_EASTERN_FACE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Mt. Woe Upper East Face for an Open World.
        - Modify magic tab pickup.
        """

        owu.update_add_item(script, script.get_function_start(9, FID.ACTIVATE))
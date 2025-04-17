"""Openworld Kajar Magic Lab"""

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
    """EventMod for Kajar Magic Lab"""

    loc_id = ctenums.LocID.KAJAR_MAGIC_LAB

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Kajar Magic Lab for an Open World.
        - Normalize magic and speed tab pickups
        """

        owu.update_add_item(script, script.get_function_start(8, FID.ACTIVATE))

        pos = script.find_exact_command(
            EC.add_item(ctenums.ItemID.MAGIC_TAB),
            script.get_function_start(0x11, FID.ACTIVATE)
        )
        owu.update_add_item(script, pos)

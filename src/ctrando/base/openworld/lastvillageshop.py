"""Openworld Last Village Shop"""

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
    """EventMod for Last Village Shop"""

    loc_id = ctenums.LocID.LAST_VILLAGE_SHOP

    @classmethod
    def modify(cls, script: Event):
        """
        Last Village Shop Lab for an Open World.
        - Normalize magic tab pickup
        - Always use Shop 9
        """
        owu.update_add_item(script, script.get_function_start(0xA, FID.ACTIVATE))

        # Remove shop conditional
        pos = script.get_function_start(8, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xD2), pos)
        script.delete_jump_block(pos)

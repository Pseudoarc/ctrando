"""Openworld Northern Ruins Basement"""

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
    """EventMod for Northern Ruins Basement"""
    loc_id = ctenums.LocID.NORTHERN_RUINS_BASEMENT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Basement for an Open World.
        - Reorder mem set and add item
        """

        pos = script.get_function_start(8, FID.ACTIVATE)
        item_str_ind = owu.add_default_treasure_string(script)

        for _ in range(2):

            pos, cmd = script.find_command([0xCA], pos)
            item_id = cmd.args[0]

            script.data[pos:pos+2] = EC.add_item_memory(0x7F0200).to_bytearray()
            script.insert_commands(
                EC.assign_val_to_mem(item_id, 0x7F0200, 1)
                .to_bytearray(), pos
            )
            pos, _ = script.find_command([0x4F], pos)
            script.delete_commands(pos)

            pos, _ = script.find_command([0xC1], pos)
            script.data[pos+1] = item_str_ind



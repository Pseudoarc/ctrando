"""Openworld Enhasa Balthasar Study"""

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
    """EventMod for Enhasa Balthasar Study"""

    loc_id = ctenums.LocID.ENHASA_NU_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Enhasa Balthasar Study for an Open World.
        - Normalize magic and speed tab pickups
        """

        item_str_id = owu.add_default_treasure_string(script)

        pos = script.find_exact_command(
            EC.add_item(ctenums.ItemID.MAGIC_TAB),
            script.get_function_start(8, FID.ACTIVATE),
        )
        script.delete_commands(pos, 2)

        pos, _ = script.find_command([0xBB], pos)
        script.data[pos + 1] = item_str_id

        script.insert_commands(
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.MAGIC_TAB, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .get_bytearray(),
            pos,
        )

        pos = script.find_exact_command(EC.generic_command(0xEE), pos)
        script.insert_commands(
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.SPEED_TAB, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(item_str_id))
            .get_bytearray(),
            pos,
        )

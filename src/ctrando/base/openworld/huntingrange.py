"""Openworld Hunting Range"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Hunting Range"""

    loc_id = ctenums.LocID.HUNTING_RANGE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Hunting Range for an Open World.
        - Update Nu's Reward (vanilla Third Eye)
        """
        for obj_id in (4, 5, 6):
            pos = script.get_object_start(obj_id)
            pos = script.find_exact_command(
                EC.if_flag(memory.Flags.HUNTING_RANGE_NU_REWARD), pos
            )
            pos, _ = script.find_command([0xBB], pos)

            new_block = (
                EF()
                .add(EC.assign_val_to_mem(ctenums.ItemID.THIRD_EYE, 0x7F0200, 1))
                .add(EC.add_item_memory(0x7F0200))
                .add(EC.auto_text_box(
                    script.add_py_string(
                        "You plenty strong!{linebreak+0}"
                        "Take!{null}"
                    )
                )).add(EC.auto_text_box(owu.add_default_treasure_string(script)))
            )
            script.insert_commands(
                new_block.get_bytearray(), pos
            )

            pos += len(new_block)
            script.delete_commands(pos, 2)
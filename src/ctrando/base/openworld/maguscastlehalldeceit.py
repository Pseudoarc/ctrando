"""Openworld Castle Magus Hall of Deceit"""

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
    """EventMod for Castle Magus Hall of Deceit"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_HALL_DECEIT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Hall of Deceit for an Open World.
        - Add exploremode on after ghost kids fight.
        - Fix script chest
        """

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0xA, FID.ACTIVATE)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # Ghost kid chest
        pos = script.get_function_start(9, FID.ACTIVATE)
        script.delete_commands(pos, 1 )  # exploremode off
        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.BARRIER))
        script.delete_commands(pos, 3)
        ins_block = (
            EF().add(EC.assign_val_to_mem(ctenums.ItemID.BARRIER, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_GHOST_KIDS_CHEST))
            .add(EC.auto_text_box(owu.add_default_treasure_string(script)))
        )
        script.insert_commands(
            ins_block.get_bytearray(), pos
        )
        pos += len(ins_block)
        script.delete_commands(pos, 1)  # extra set flag

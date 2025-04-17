"""Openworld Denadoro Masa Cave Exterior"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Denadoro Masa Cave Exterior"""
    loc_id = ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Denadoro Masa Cave Exterior event.
        - Change gold rock so that it (1) is not locked behind masa upgrade.
        - Unlike jets, require Frog to catch the rock (no change needed).
        - Shorten the cutscene.
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xCD))
        script.delete_jump_block(pos)
        script.delete_commands(pos, 1)  # Check for Masa Upgraded

        pos = script.get_function_start(4, FID.ARBITRARY_3)

        for __ in range(3):
            pos, _ = script.find_command([0xBB], pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 8).to_bytearray()

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.GOLD_ROCK))
        ins_block = (
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.GOLD_ROCK, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(owu.add_default_treasure_string(script)))
        )
        script.insert_commands(
            ins_block.get_bytearray(), pos
        )
        pos += len(ins_block)
        script.delete_commands(pos, 1)

        pos, _ = script.find_command([0xBB], pos+2)

        script.delete_commands(pos, 1)
        pos = script.find_exact_command(EC.generic_command(0xAD, 0x40))
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.call_pc_function(2, FID.ARBITRARY_2, 5, FS.HALT),
            script.get_function_start(0xD, FID.TOUCH)
        ) + 3
        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, 0x7F0240, 1))
            .add_if(
                EC.if_mem_op_value(0x7F0240, OP.GREATER_THAN, 6),
                EF().add(EC.pause(3))
            ).get_bytearray(), pos
        )


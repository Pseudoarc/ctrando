"""Openworld Magic Cave Interior"""

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
    """EventMod for Magic Cave Interior"""
    loc_id = ctenums.LocID.MAGIC_CAVE_INTERIOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Magic Cave Interior for an Open World.
        - Block the exit to the Magic Cave entrance if Frog has not opened it.
        - Remove the "You too can learn magic"
        - update sealed chest
        """

        # Add cave wall over the exit if the mountain isn't split.
        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(
            EF().add_if(
                EC.if_not_flag(memory.Flags.OW_MAGIC_CAVE_OPEN),
                EF().add(EC.copy_tiles(
                    0xB, 0x14, 0xE, 0x17,
                    0x4, 0x12, True, True, False,
                    copy_props=True,
                    wait_vblank=True))
            ).get_bytearray(), pos
        )


        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.MAGIC_CAVE_FIRST_BATTLE)
        ) + len(EC.set_flag(memory.Flags.MAGIC_CAVE_FIRST_BATTLE))

        new_block = (
            EF().add(EC.party_follow())
            .add(EC.set_explore_mode(True))
        )
        script.insert_commands(new_block.get_bytearray(), pos)

        pos += len(new_block)
        del_end = script.find_exact_command(EC.party_follow(), pos) + 1
        script.delete_commands_range(pos, del_end)

        # sealed chest
        pos = script.get_function_start(0x19, FID.ACTIVATE)
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE))


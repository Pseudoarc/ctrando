"""Openworld Giant's Claw Last Tyrano"""

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
    """EventMod for Giant's Claw Last Tyrano"""
    loc_id = ctenums.LocID.GIANTS_CLAW_TYRANO

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Giant's Claw Last Tyrano for an Open World.
        - Put a Key Item on the Rainbow Shell.
        - Do not trigger the cutscene after interacting with the shell.
        """
        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_3, 4, FS.HALT),
            script.get_function_start(1, FID.STARTUP)
        )
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.call_pc_function(2, FID.ARBITRARY_4, 3, FS.HALT),
            pos
        )
        script.delete_commands(pos, 1)

        got_item_str = owu.add_default_treasure_string(script)
        block = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.OBTAINED_GIANTS_CLAW_KEY),
                owu.get_add_item_block_function(ctenums.ItemID.RAINBOW_SHELL, None, got_item_str)
                .add(EC.set_flag(memory.Flags.OBTAINED_GIANTS_CLAW_KEY))
            )
        )
        script.insert_commands(block.get_bytearray(), pos)
        pos = script.find_exact_command(EC.party_follow(), pos) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos, _ = script.find_command([0xDF], pos)
        repl_cmd = EC.change_location(
            ctenums.LocID.OW_MIDDLE_AGES,
            0x78, 0x4A, Facing.DOWN, 0, True
        )
        script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()
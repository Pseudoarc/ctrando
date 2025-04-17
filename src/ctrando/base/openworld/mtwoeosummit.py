"""Openworld Mt. Woe Summit"""

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
    """EventMod for Mt. Woe Summit"""
    loc_id = ctenums.LocID.MT_WOE_SUMMIT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Mt. Woe Summit for an Open World.
        - Give Magus the same Arb0 as everyone else so that he doesn't go flying
          off the screen.
        - Rework the intro scene to allow for one-character parties
        - Modify the post-battle scene to give a KI and return to the overworld.
        - Don't let the ice crystal respawn after the boss is defeated.
        - Remove pre-fight text.
        """

        # Fix Magus's Arb0
        script.link_function(7, FID.ARBITRARY_0, 1, FID.ARBITRARY_0)

        # PC Arb2 (non-Crono) have set 0x7F0216 to 1 on completion, and the script
        # will hang until the variable is set.  We'll remove both the call to Arb1
        # because it's just dialog and also the hang until 0x7F0216 is set.
        pos = script.get_function_start(9, FID.ARBITRARY_0)
        pos = script.find_exact_command(
            EC.call_pc_function(2, FID.ARBITRARY_2, 6, FS.CONT), pos)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0), pos)
        script.delete_jump_block(pos)

        # Remove dialogue before the battle.
        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_1, 6, FS.HALT),
            script.get_function_start(0, FID.ARBITRARY_0)
        )
        script.delete_commands(pos, 1)

        # The post-battle scene is in Obj08 (Melchior), activate.
        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_3, 6, FS.HALT),
            script.get_function_start(8, FID.ACTIVATE)
        )

        new_block = (
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.RUBY_KNIFE,
                                          0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(
                script.add_py_string(
                    "{line break}Got 1 {item}!{line break}"
                    "{itemdesc}{null}"
                )
            )).add(EC.set_flag(memory.Flags.MT_WOE_BOSS_DEFEATED))
            .add(EC.darken(6))
            .add(EC.fade_screen())
            .add(EC.change_location(ctenums.LocID.OW_DARK_AGES,
                                    0x35, 0x3B, Facing.DOWN,
                                    0, True
                                    ))
            .add(EC.return_cmd())
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)

        # This is technically in the touch function.
        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        # Remove the ice crystal if the boss is defeated.
        pos = script.get_function_start(9, FID.STARTUP)
        script.insert_commands(
            EF()
            .add_if(
                EC.if_flag(memory.Flags.MT_WOE_BOSS_DEFEATED),
                EF().add(EC.remove_object(9))
                .add(EC.return_cmd()).add(EC.end_cmd())
            ).get_bytearray(), pos
        )
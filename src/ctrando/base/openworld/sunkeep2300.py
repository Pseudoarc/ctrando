"""Openworld Sun Keep (2300AD)"""

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
    """EventMod for Sun Keep (2300AD)"""
    loc_id = ctenums.LocID.SUN_KEEP_2300

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Keep (2300AD) for an Open World.
        - Change draw conditions for Moon Stone to use rando flags.
        """

        moonstone_obj = 8
        new_hide_condition = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.MOONSTONE_PLACED_PREHISTORY),
                EF().add(EC.remove_object(moonstone_obj))
            ).add_if(
                EC.if_flag(memory.Flags.MOONSTONE_COLLECTED_2300),
                EF().add(EC.remove_object(moonstone_obj))
            )
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F013A, OP.LESS_THAN, 0x20),
            script.get_function_start(moonstone_obj, FID.STARTUP)
        )

        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        script.insert_commands(
            new_hide_condition.get_bytearray(), pos
        )

        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        end, _ = script.find_command([0x88], pos)
        script.delete_commands_range(pos, end)

        # Remove some special case dialogue for Lucca
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020E, OP.EQUALS, 1),
            script.get_function_start(moonstone_obj, FID.ACTIVATE)
        )
        script.delete_jump_block(pos)

        # Delete a block that triggers PC2's function instead of PC1 if PC1 is Crono.
        # Instead we'll give Crono a function that can be called so that one-person
        # parties aren't weird.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020C, OP.EQUALS, 0),
            pos
        )
        script.delete_jump_block(pos)

        # Here's that function for Crono.
        script.set_function(
            1, FID.ARBITRARY_1,
            EF().add(EC.play_animation(3))
            .add(EC.auto_text_box(
                script.add_py_string(
                    "{Crono} thinks {Lucca} should handle this.{null}")
            )).add(EC.play_animation(0))
            .add(EC.return_cmd())
        )

        # Disable the blank object for noticing the missing stone.
        blank_obj = 9
        script.set_function(
            blank_obj,
            FID.STARTUP,
            EF().add(EC.remove_object(blank_obj)).add(EC.return_cmd()).add(EC.end_cmd()),
        )

        pos = script.get_function_start(8, FID.ACTIVATE)
        pos = script.find_exact_command(EC.darken(8), pos)
        script.delete_commands(pos, 2)

        pos, _ = script.find_command([0xDF], pos)
        script.insert_commands(
            EF().add(EC.darken(8)).add(EC.fade_screen()).get_bytearray(),
            pos
        )
        owu.update_add_item(script, script.get_function_start(8, FID.ACTIVATE))


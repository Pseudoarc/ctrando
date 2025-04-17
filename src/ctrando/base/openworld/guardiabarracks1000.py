"""Update Guardia Barracks 1000 for an open world."""
from typing import Optional

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Throneroom 1000"""
    loc_id = ctenums.LocID.GUARDIA_BARRACKS_1000

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Modify Guardia Throneroom 1000 script.
        """
        cls.modify_guard_activation(script)
        cls.update_pc_arbs(script)

    @classmethod
    def modify_guard_activation(cls, script: locationevent.LocationEvent):
        """
        Activate guards based on flags instead of storyline.
        Call PC arbs with through pc_id instead of object_id.
        """
        pos: Optional[int]

        # Object 8 has the touch trigger to get the guards going
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x33),
            script.get_function_start(8, FID.TOUCH)
        )

        # Replace the storyline trigger with flags.
        # If defeated Dtank and has not yet escaped from prison.
        new_cmd = EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK)
        script.replace_jump_cmd(pos, new_cmd)
        pos += len(new_cmd)

        new_cmd = EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON)
        script.replace_jump_cmd(pos, new_cmd)

        # One guard only appears for the chase.  Change the conditions for
        # removing him.
        pos = script.get_function_start(0xA, FID.STARTUP)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x8A),
                                        pos)
        script.delete_jump_block(pos)
        script.insert_commands(
            EF().add_if_else(
                EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                EF(),
                EF().add(EC.set_own_drawing_status(False))
            ).get_bytearray(), pos)

        # When that guard disappears, Pierre the lawyer appears instead
        pos = script.get_function_start(0xB, FID.STARTUP)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x8A),
                                        pos)

        script.replace_jump_cmd(
            pos,
            EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK)
        )
        pos += len(EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK))
        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                EF().add(EC.set_own_drawing_status(False))
            ).get_bytearray(), pos
        )

        # Remove all if storyline < 0x30 checks with dead dtank & not escaped
        while True:
            pos = script.find_exact_command_opt(
                EC.if_storyline_counter_lt(0x30), pos
            )

            if pos is None:
                break

            script.replace_jump_cmd(
                pos, EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK)
            )
            cmd = locationevent.get_command(script.data, pos)
            jump_bytes = cmd.args[-1]

            pos += len(cmd)
            ins_block = (
                EF()
                .add_if(
                    EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                    EF().add(EC.jump_forward(jump_bytes))
                )
            )
            script.insert_commands(ins_block.get_bytearray(), pos)

    @classmethod
    def update_pc_arbs(cls, script: locationevent.LocationEvent):
        """
        Give everyone the same arbs (link?)
        """
        waiting = script.get_function(0, FID.ARBITRARY_0)
        surprise = script.get_function(1, FID.ARBITRARY_1)

        for obj_id in range(1, 1+7):
            script.set_function(obj_id, FID.ARBITRARY_0, waiting)
            script.set_function(obj_id, FID.ARBITRARY_1, surprise)

        pos: Optional[int]
        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_0, 5, FS.CONT),
            script.get_function_start(8, FID.TOUCH)
        )

        new_block = (
            EF()
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_1, 4, FS.HALT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 4, FS.HALT))
        )

        script.data[pos: pos+len(new_block)] = new_block.get_bytearray()

        new_str_id = script.add_py_string(
            "{pc2}: This doesn't look good!{null}"
        )
        new_block = (
            EF()
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 4, FS.HALT))
            .add(EC.auto_text_box(new_str_id))
        )

        new_block_b = new_block.get_bytearray()

        while True:
            pos = script.find_exact_command_opt(
                EC.call_obj_function(3, FID.ARBITRARY_0, 5, FS.CONT)
            )
            if pos is None:
                break

            script.data[pos:pos+len(new_block_b)] = new_block_b

"""Openworld Forest Maze"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Forest Maze"""
    loc_id = ctenums.LocID.FOREST_MAZE
    kino_obj = 0x13
    kino_aux_obj = 0x14
    temp_facing_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Mystic Forest Maze Event.
         - Update Kino so that he locks the maze without Ayla or backdoor access.
        """

        # Kino is obj 0x13 and an extra object is in 0x14.  The extra object just
        # calls Kino's touch function.

        # The trigger for these objects is Storyline < 0x7B.
        # Change the trigger to Kino leaving forest maze
        for obj_id in (cls.kino_obj, cls.kino_aux_obj):
            pos = script.get_object_start(obj_id)
            pos = script.find_exact_command(EC.if_storyline_counter_lt(0x7B), pos)

            script.replace_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.KINO_LEFT_FOREST_MAZE))

        # Make Kino not walkthrough
        pos = script.get_object_start(cls.kino_obj)
        pos = script.find_exact_command(EC.set_move_properties(True, True))
        script.delete_commands(pos, 1)

        kino_leave_block = (
            EF().add(EC.set_move_speed(0x80))
            .add(EC.set_move_properties(True, True))
            .add(EC.set_own_facing('down'))
            .add(EC.vector_move(270, 0x2, True))
            .add(EC.vector_move(90, 0x2, True))
            .add(EC.set_move_speed(0x20))
            .add(EC.move_sprite(0xC, 0x2))
            .add(EC.move_sprite(0xA, 0x0))
            .add(EC.set_own_drawing_status(False))
            .add(EC.set_flag(memory.Flags.KINO_LEFT_FOREST_MAZE))
            .add(EC.remove_object(cls.kino_aux_obj))
        )
        # Now change Kino's activate/touch function
        kino_activate = (
            EF().add(EC.get_pc_facing(0, cls.temp_facing_addr))
            .add_if(
                # If you interact from the right, then you've back-doored the maze,
                # so make Kino leave.
                EC.if_mem_op_value(cls.temp_facing_addr, OP.EQUALS, Facing.LEFT),
                EF().add(EC.set_explore_mode(False))
                .append(kino_leave_block)
                .add(EC.party_follow())
                .add(EC.set_explore_mode(True))
                .jump_to_label(EC.jump_forward(), 'end')
            )
            .add_if(
                # If Ayla is active, then play whatever scene to make Kino leave
                EC.if_pc_active(ctenums.CharID.AYLA),
                EF().add(EC.move_party(0x89, 0x88, 0x89, 0x86, 0x89, 0x84))
                .add(EC.call_obj_function(6, FID.ARBITRARY_0, 6, FS.CONT))
                .jump_to_label(EC.jump_forward(), 'end')
            ).add(EC.set_explore_mode(False))
            .add(EC.set_own_facing('left'))
            .add(EC.move_party(0x8B, 0x86, 0x8A, 0x85, 0x8A, 0x87))
            .add(EC.auto_text_box(
                script.add_py_string(
                    "KINO: Danger! Need Chief {ayla} to enter! {null}"
                )
            ))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
            .set_label('end')
            .add(EC.return_cmd())
        )
        script.set_function(cls.kino_obj, FID.ACTIVATE, kino_activate)

        ayla_arb_0 =(
            EF().add(EC.set_explore_mode(False))
            .add(EC.move_sprite(0xB, 0x6)).add(EC.set_own_facing('right'))
            .add(EC.call_obj_function(cls.kino_obj, FID.ARBITRARY_0, 6, FS.HALT ))
            .add(EC.loop_animation(0x3E, 1))
            .add(EC.play_sound(0x81))
            .add(EC.call_obj_function(cls.kino_obj, FID.ARBITRARY_2, 6, FS.HALT))
            .add(EC.pause(1))
            .add(EC.call_obj_function(cls.kino_obj, FID.ARBITRARY_5, 6, FS.HALT))
            .add(EC.remove_object(cls.kino_obj))
            .add(EC.remove_object(cls.kino_aux_obj))
            .add(EC.set_flag(memory.Flags.KINO_LEFT_FOREST_MAZE))
            .add(EC.return_cmd())
        )

        script.set_function(6, FID.ARBITRARY_0, ayla_arb_0)
        pos, _ = script.find_command(
            [0xC2], script.get_function_start(cls.kino_obj, FID.ARBITRARY_5))
        script.delete_commands(pos, 1)
        pos = script.find_exact_command(EC.move_sprite(0xA, 0x0), pos)
        script.insert_commands(
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )

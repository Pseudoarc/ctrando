"""Openworld Last Village Commons"""

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
    """EventMod for Last Village Commons"""
    loc_id = ctenums.LocID.LAST_VILLAGE_COMMONS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Last Village Commons for an Open World.
        - Give Crono and Magus the animation functions for being captured.
        - Shorten the capture scene significantly, both dialogue and animations.
        - Put NPCs (notably plant lady, Alfador) in their post-Blackbird states.
        """

        cls.modify_capture_scene(script)
        cls.add_pc_functions(script)
        cls.display_npcs_always(script)

    @classmethod
    def add_pc_functions(cls, script: Event):
        """
        Give Crono and Magus the animations to get captured.
        """

        for obj_id in (1, 7):
            pos = script.find_exact_command(
                EC.set_controllable_infinite(),
                script.get_object_start(obj_id)
            )
            script.insert_commands(
                EC.set_move_destination(True, False).to_bytearray(),
                pos
            )

        # Crono is before Marle so he needs actual copies.
        script.set_function(1, FID.TOUCH, EF().add(EC.return_cmd()))
        arb0 = script.get_function(2, FID.ARBITRARY_0)
        arb1 = script.get_function(2, FID.ARBITRARY_1)
        arb2 = script.get_function(2, FID.ARBITRARY_2)
        arb3 = script.get_function(2, FID.ARBITRARY_3)

        script.set_function(1, FID.ARBITRARY_0, arb0)
        script.set_function(1, FID.ARBITRARY_1, arb1)
        script.set_function(1, FID.ARBITRARY_2, arb2)
        script.set_function(1, FID.ARBITRARY_3, arb3)

        script.link_function(7, FID.TOUCH, 2, FID.TOUCH)
        script.link_function(7, FID.ARBITRARY_0, 2, FID.ARBITRARY_0)
        script.link_function(7, FID.ARBITRARY_1, 2, FID.ARBITRARY_1)
        script.link_function(7, FID.ARBITRARY_2, 2, FID.ARBITRARY_2)
        script.link_function(7, FID.ARBITRARY_3, 2, FID.ARBITRARY_3)

    @classmethod
    def modify_capture_scene(cls, script: Event):
        """
        Modify the scene where the party is taken to the blackbird.
        - Change the trigger from storyline to flag.
        - Add a decision box to avoid getting forced in on accident.
        - Remove all of the scene except for Dalton blasting the party and the
          fadeout after.
        - Skip the special purpose area and go straight to the Blackbird Cell
        """

        # Update draw/show conditions on Dalton and his crew
        enemy_obj_ids = range(0x11, 0x19)
        for obj_id in enemy_obj_ids:
            pos, _ = script.find_command(
                [0x18], script.get_object_start(obj_id)
            )
            script.replace_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD)
            )

        # The main scene kicks off with the old man in object 08, activate.
        # But this immediately calls out to obj00, Arb0.

        # Change this activation command
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xD2),
            script.get_function_start(8, FID.ACTIVATE)
        )
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD)
        )

        new_block = (
            EF()
            .add_if_else(
                EC.if_flag(memory.Flags.HAS_ALGETTY_PORTAL),
                EF()
                .add(EC.decision_box(
                    script.add_py_string(
                        "Get Captured by Dalton?{line break}"
                        "   Yes.{line break}"
                        "   No.{null}"
                    ), 1, 2
                )).add_if_else(
                    EC.if_result_equals(1),
                    EF().add(EC.assign_val_to_mem(0, memory.Memory.BLACKBIRD_LEFT_WING_CUTSCENE_COUNTER, 1))
                    .add(EC.call_obj_function(
                        0, FID.ARBITRARY_0, 1, FS.CONT))
                    .add(EC.return_cmd()),
                    EF().add(EC.set_explore_mode(True))
                    .add(EC.return_cmd())
                ),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("Algetty Portal Required.{null}")
                ))
                .add(EC.set_explore_mode(True))
                .add(EC.return_cmd())
            )
        )
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 4)
        script.insert_commands(new_block.get_bytearray(), pos)

        # Now we briefly go to Obj00, Arb0.  Remove the storyline setting.
        pos = script.get_function_start(0, FID.ARBITRARY_0)
        pos = script.find_exact_command(EC.set_storyline_counter(0xCF), pos)
        script.delete_commands(pos, 1)

        # After calling out to Dalton's activate, we change location.  We'll
        # skip the special purpose area (dialog only) and go to jail.
        pos, cmd = script.find_command([0xE1], pos)
        # Change Location copied from special purpose area.
        script.data[pos:pos+len(cmd)] = bytes.fromhex("E173031708")

        # Now it's Dalton (0x11), activate.
        pos = script.get_function_start(0x11, FID.ACTIVATE)
        pos = script.find_exact_command(EC.play_animation(9), pos) + 2
        end = script.find_exact_command(EC.auto_text_box(0x2C), pos) + 2
        script.delete_commands_range(pos, end)

    @classmethod
    def display_npcs_always(cls, script: Event):
        """
        Some NPCs don't show until after the Blackbird, but we'll put them in always
        """

        plant_lady_obj, plant_obj = 0x19, 0x1A
        for obj_id in (plant_lady_obj, plant_obj):
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.LESS_THAN, 0xD2),
                script.get_object_start(obj_id))
            script.delete_jump_block(pos)

        # modify plant lady
        pos = script.get_function_start(plant_lady_obj, FID.ACTIVATE)
        pos, _ = script.find_command([0xC0], pos)
        end = script.find_exact_command(EC.if_result_equals(2)) + 3  # after cmd.
        script.delete_commands_range(pos, end)

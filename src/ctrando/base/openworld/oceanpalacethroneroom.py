"""Openworld Ocean Palace Throne Room"""

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


# This needs to change because we'll just be thrown into a cutscene.


class EventMod(locationevent.LocEventMod):
    """EventMod for Ocean Palace Throne Room"""
    loc_id = ctenums.LocID.OCEAN_PALACE_THRONE
    room_status_addr = 0x7F0210

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Throne Room Event.
        - Add a ruby knife lock on the hallway Nu.
        - Remove dialog.
        - Make Magus playable during this event.
        - Normalize PC arbitrary functions
        """

        cls.modify_room_status(script)
        cls.modify_nu(script)
        cls.fix_magus_startup(script)
        cls.modify_pc_arbs(script)
        cls.modify_ruby_knife_scene(script)

    @classmethod
    def modify_room_status(cls, script: Event):
        """
        Remove mid-dungeon cutscenes from the startup.
        """

        # 0x7F0210 is used for scene status
        # If 0x7F00DB == 1, set 0x7F0210 to 4
        #  - This is something about one of the endings
        # If Storyline in [0xCA, 0xCC), set 0x7F0210 to 3
        #  - These storyline values are set during cutscenes during the Ocean Palace
        #  - This should be after Crono os killed (I know spoilers, sorry)
        # If Storyline in [0xC6, 0xCA), set 0x7F0210  to 2
        #  - This is meant to catch 0xC9 after defeating twin golems.
        #  - This is the one status we actually want.
        # If Storyline in [0xC3, 0xC6), set 0x7F0210 to 1
        #  - This is for another cutscene
        # If Storyline < 0xC3, set 0x7F0210 to 0
        #  - This is for the first cutscene "Raise the Mammon M's power to the limit"

        # Rewrite to set 4 in an ending and 3 otherwise.

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xCC))
        end = script.find_exact_command(
            EC.if_mem_op_value(cls.room_status_addr, OP.GREATER_THAN, 2))

        script.delete_commands_range(pos, end)

        # This may change if we decide to actually have a fake Lavos fight and
        # subsequent return to the throneroom.  For now just force status 2.
        script.insert_commands(
            EC.assign_val_to_mem(2, cls.room_status_addr, 1)
            .to_bytearray(), pos
        )

    @classmethod
    def modify_nu(cls, script: Event):
        """
        Make the Nu into a ruby knife check for the next scene.
        """
        nu_obj = 0x18
        pos = script.get_function_start(nu_obj, FID.ACTIVATE)

        script.insert_commands(
            EF().add_if_else(
                EC.if_has_item(ctenums.ItemID.RUBY_KNIFE),
                EF(),  # Proceed to the usual Nu jump away function
                EF().add(EC.set_own_facing('down'))
                .add(EC.play_animation(1))
                # .add(EC.auto_text_box(
                #     script.add_py_string(
                #         "The ruby knife is required to stop{linebreak+0}"
                #        "the Mammon Machine, nu...{null}"
                #    )
                #))
                .add(EC.play_animation(0))
                .add(EC.return_cmd())
            ).get_bytearray(), pos
        )

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give everyone the animation to release the ruby knife.  Update calls.
        """

        # Crono's Arb0 - Arb2 are scrollscreen commands that don't even involve him.
        # They are only used in the throneroom scenes that we ignore.  Then Arb3
        # and Arb4 are used for the animation.

        # Just overwrite everyone's Arb3 and Arb4 with these commands.
        # The arb3 (a vectormove) is usd by everyone at some point, and the arb4
        # is only performed by the lead PC.

        arb1 = (
            EF().add(EC.set_own_facing_pc(0)).add(EC.return_cmd())
        )

        arb3 = (
            EF().add(EC.vector_move(270, 4, False))
            .add(EC.return_cmd())
        )

        static_anim_dict: dict[ctenums.CharID, int] = {
            ctenums.CharID.CRONO: 0x93,
            ctenums.CharID.MARLE: 204,
            ctenums.CharID.LUCCA: 103,  # 79 # 71, 81
            ctenums.CharID.ROBO: 106,
            ctenums.CharID.FROG: 122,
            ctenums.CharID.AYLA: 87,
            ctenums.CharID.MAGUS: 58  # 226, 241, 243, 243
        }

        for obj_id in range(2, 8):
            pc_id = ctenums.CharID(obj_id - 1)
            arb4 = (
                EF().add(EC.static_animation(static_anim_dict[pc_id]))
                .add(EC.pause(0.5))
                .set_label('inf_loop')
                .add(EC.play_animation(0x22))
                .jump_to_label(EC.jump_back(), 'inf_loop')
            )

            script.set_function(obj_id, FID.ARBITRARY_3, arb3)
            script.set_function(obj_id, FID.ARBITRARY_4, arb4)

        # Crono and Magus need new Arb2
        arb2 = (
            EF()
            .add(EC.vector_move(270, 4, True))
            .add(EC.return_cmd())
        )
        script.set_function(ctenums.CharID.CRONO+1, FID.ARBITRARY_2, arb2)
        script.set_function(ctenums.CharID.MAGUS+1, FID.ARBITRARY_2, arb2)

        # remove dialog-only functions
        pos = script.get_function_start(0xB, FID.STARTUP)
        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_0, 4, FS.HALT)
        )
        script.delete_commands(pos, 2)

        # Now update calls from obj01 to pc00
        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_3, 4, FS.HALT)
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_3, 4, FS.HALT)
        script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_4, 6, FS.CONT))
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_4, 6, FS.CONT)
        script.data[pos:pos + len(repl_cmd)] = repl_cmd.to_bytearray()



    @classmethod
    def fix_magus_startup(cls, script: Event):
        """
        Magus's object exists but is not playable for this scene.  Fix it.
        """

        pos = script.get_function_start(7, FID.STARTUP)

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.room_status_addr, OP.LESS_THAN, 3),
            pos
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.room_status_addr, OP.EQUALS, 2),
                EF().add(EC.set_controllable_infinite())
                .add(EC.end_cmd())
            ).get_bytearray(), pos
        )

    @classmethod
    def modify_ruby_knife_scene(cls, script: Event):
        """
        Modify the scene that plays when the Ruby Knife is used on the Mammon M.
        - Remove dialog
        - Move directly to destroying Zeal, not the unwinnable Lavos fight.
        Note: The scene is also modified slightly by modify_pc_arbs.
        """

        # Remove some dialog that is outside the main scene function
        knife_obj, schala_obj, queen_obj, prophet_obj = 9, 0xC, 0xD, 0xE
        owu.remove_dialog_from_function(script, knife_obj, FID.ARBITRARY_0,
                                        max_num_replacements=2)
        owu.remove_dialog_from_function(script, schala_obj, FID.ARBITRARY_6,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, schala_obj, FID.ARBITRARY_8,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, schala_obj, FID.ARBITRARY_9,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, queen_obj, FID.ARBITRARY_2,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, queen_obj, FID.ARBITRARY_3,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, prophet_obj, FID.ARBITRARY_3,
                                        max_num_replacements=1)
        owu.remove_dialog_from_function(script, prophet_obj, FID.ARBITRARY_4,
                                        max_num_replacements=1)

        # Don't remove the Ruby Knife from inventory
        pos = script.get_function_start(knife_obj, FID.ARBITRARY_0)
        script.find_exact_command(EC.remove_item(ctenums.ItemID.RUBY_KNIFE))
        script.delete_commands(pos, 1)

        # The scene takes place in Obj0B, Startup
        # Everything is OK except for some long pauses at the end and the transition
        # to the Lavos fight.

        # Delete all the PC text responding to the knife transforming
        pos = script.get_function_start(0xB, FID.STARTUP)
        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_1, 4, FS.HALT),  pos
        )
        script.delete_commands(pos, 2)

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.FROG), pos
        )
        end = script.find_exact_command(
            EC.generic_command(0xC2, 0x22), pos
        ) + 2
        script.delete_commands_range(pos, end)

        # Reduce pauses
        pos = script.find_exact_command(EC.generic_command(0xAD, 0x30), pos)
        script.data[pos+1] = 8

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x60), pos)
        script.data[pos+1] = 0x20

        # Now copy the cutscene outtro from another part of this script.
        pos = script.find_exact_command(
            EC.generic_command(0xEB, 0x30, 0),
            pos
        )
        end = script.find_exact_command(EC.return_cmd(), pos)
        exit_func = EF.from_bytearray(script.data[pos:end])
        script.delete_commands_range(pos, end)

        new_block = (
            EF().add(EC.set_flag(memory.Flags.ZEAL_HAS_FALLEN))
            .add(EC.set_flag(memory.Flags.HAS_ALGETTY_PORTAL))
            .add(EC.reset_flag(memory.Flags.OCEAN_PALACE_PLATFORM_DOWN))
            # Only set Last Village flag.
            # .add(EC.assign_val_to_mem(0x1E, 0x7F01F7, 1))
            .add(EC.set_flag(memory.Flags.OW_OMEN_DARKAGES))
            .add(EC.decision_box(
                script.add_py_string("Fight Lavos?{line break}"
                                     "   No{line break}"
                                     "   Yes{null}"),
                1, 2
            )).add(EC.darken(6)).add(EC.fade_screen())
            .add_if_else(
                EC.if_result_equals(1),
                EF().add(EC.change_location(ctenums.LocID.LAST_VILLAGE_EMPTY_HUT,
                                            0x18, 0x18, Facing.DOWN, )),
                exit_func
            )
        )
        script.insert_commands(
           new_block.get_bytearray(), pos
        )
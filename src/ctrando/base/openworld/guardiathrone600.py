"""Openworld Guardia Throneroom 600"""
from typing import Optional

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Throneroom 600"""
    loc_id = ctenums.LocID.GUARDIA_THRONEROOM_600

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Throneroom 600 Event.
        - Update PC startups to set coordinates upon returning from manoria
        - Replace storyline triggers with flag checking/setting
        """

        # Sad frog objects.  Dummying instead of removing to not mess with
        # object order.
        script.dummy_object_out(0xB)   # Sad Frog
        script.dummy_object_out(0xC)   # Sad Frog scene
        script.dummy_object_out(0x10)  # Soldiers at entrance scene

        cls.update_pc_startups(script)
        cls.change_storyline_triggers(script)
        cls.modify_manoria_return_scene(script)
        cls.modify_shell_turn_in(script)
        cls.fix_partyfollows(script)

    @classmethod
    def update_pc_startups(cls, script: Event):
        """
        PC startups need to set coordinates upon being returned from Manoria.
        The vanilla startups set coordinates for the rainbow shell scene, but
        this is no longer needed.
        """

        def make_startup(char_id: ctenums.CharID) -> EF:

            coord_block = (
                EF().add_if(
                    EC.if_mem_op_value(0x7F021A, OP.EQUALS, char_id),
                    EF().add(EC.set_object_coordinates_tile(0x1E, 0x1F))
                    .jump_to_label(EC.jump_forward(), f"end{char_id}")
                )
                .add_if(
                    EC.if_mem_op_value(0x7F021C, OP.EQUALS, char_id),
                    EF().add(EC.set_object_coordinates_tile(0x20, 0x1F))
                    .jump_to_label(EC.jump_forward(), f"end{char_id}")
                ).set_label(f"end{char_id}")
            )

            ret_fn = (
                EF().add(EC.load_pc_in_party(char_id))
                .add_if(
                    EC.if_flag(memory.Flags.MANORIA_BOSS_DEFEATED),
                    EF().add_if(
                        EC.if_not_flag(
                            memory.Flags.MANORIA_RETURN_SCENE_COMPLETE
                        ),
                        coord_block
                    )
                ).add(EC.return_cmd()).add(EC.set_controllable_infinite())
            )

            return ret_fn

        for ind in range(7):
            char_id = ctenums.CharID(ind)
            obj_id = 1 + ind
            script.set_function(obj_id, FID.STARTUP, make_startup(char_id))

    @classmethod
    def change_storyline_triggers(cls, script: Event):
        """
        Change storyline checks to flag checks.
        - 0x15 <-> has defeated the Nagaettes at Cathedral
        - 0x1B <-> has defeated manoria boss
        - 0x1C <-> has watched the cathedral return scene
        """

        repl_dict: dict[int, memory.Flags] = {
            0x15: memory.Flags.MANORIA_SANCTUARY_NAGAETTE_BATTLE,
            0x1B: memory.Flags.MANORIA_BOSS_DEFEATED,
            0x1C: memory.Flags.MANORIA_RETURN_SCENE_COMPLETE
        }

        pos: Optional[int]
        pos = script.get_object_start(0)
        while True:
            pos, cmd = script.find_command_opt(
                [
                    0x18,  # if storyline lt
                    # 0x12,  # if mem op value
                 ], pos
            )

            if pos is None:
                break

            if cmd.command == 0x18:
                storyline_val = cmd.args[0]
                if storyline_val in repl_dict:
                    repl_cmd = EC.if_not_flag(repl_dict[storyline_val])
                    script.replace_jump_cmd(pos, repl_cmd)
                else:
                    pos += len(cmd)

            # print(f'{pos:04X}: {cmd}')

    @classmethod
    def modify_manoria_return_scene(cls, script: Event):
        """
        Modify the scene that plays upon returning to the castle from Manoria.
        - Remove most dialog.
        - Remove frog-specific calls.
        - Set a flag instead of set the storyline.
        """

        # for ind, string in enumerate(script.strings):
        #     py_string = ctstrings.CTString.ct_bytes_to_ascii(string)
        #     print(f"{ind:02X}: {py_string}")

        # input()
        new_str = script.add_py_string(
            "Where did Princess Nadia disappear? {line break}"
            "She may still be there!{null}"
        )

        new_scene = (
            EF().add(EC.set_own_drawing_status(False))
            .add(EC.set_explore_mode(False))
            .add(EC.script_speed(1))
            .add(EC.call_obj_function(0x13, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.call_obj_function(0x15, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.pause(1))
            .add(EC.call_obj_function(0x14, FID.ARBITRARY_2, 4, FS.SYNC))
            .add(EC.call_obj_function(0x13, FID.ARBITRARY_2, 4, FS.SYNC))
            .add(EC.call_obj_function(0x15, FID.ARBITRARY_2, 4, FS.SYNC))
            .add(EC.pause(2))
            .add(EC.auto_text_box(new_str))
            .add(EC.set_flag(memory.Flags.MANORIA_RETURN_SCENE_COMPLETE))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
        )

        pos = script.find_exact_command(
            EC.set_own_drawing_status(False),
            script.get_object_start(0x12)
        )
        end = script.find_exact_command(EC.end_cmd(), pos)

        script.insert_commands(new_scene.get_bytearray(), pos)
        script.delete_commands_range(pos + len(new_scene),
                                     end + len(new_scene))

    @classmethod
    def modify_shell_turn_in(cls, script: Event):
        """
        Move the shell turn-in from a special-cased startup to part of the
        King's activate function.  Also set some flags to adjust the quest.
        """

        # In vanilla, you are warped from Giant's Claw to the castle, and the
        # scene is triggered in the startup.  Now, we need it to be triggered
        # by activating the king object.

        king_obj = 0x13
        scene_obj = 0x08

        scene_st = script.find_exact_command(
            EC.set_explore_mode(False),
            script.get_function_start(scene_obj, FID.STARTUP)
        )

        # Remove some extra dialog bits
        del_st, _ = script.find_command([0xC2], scene_st)
        del_end_cmd = EC.call_obj_function(0x13, FID.ARBITRARY_3,
                                           4, FS.HALT)
        del_end = script.find_exact_command(del_end_cmd, del_st)

        script.delete_commands_range(del_st, del_end)

        pos = del_st

        # I get it, you want me to ...
        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 1)

        # Leene: For the sake of...
        pos, _ = script.find_command([0xC2], pos)
        script.delete_commands(pos, 1)

        # Done! I shall ... (keep)
        pos, cmd = script.find_command([0xC2], pos)
        str_id = cmd.args[0]

        del_st, _ = script.find_command([0xC2], pos + 2)
        del_end = script.find_exact_command(
            EC.set_flag(memory.Flags.GUARDIA_TREASURY_EXISTS),
            del_st
        )

        script.delete_commands_range(del_st, del_end)
        scene_end = del_st + 3  # len of set flag cmd

        scene = EF.from_bytearray(script.data[scene_st: scene_end])
        scene.add(EC.assign_val_to_mem(0, 0x7F020E, 1))
        scene.add(EC.party_follow())
        scene.add(EC.set_explore_mode(True))
        scene.add(EC.return_cmd())

        str_id = 0x3D
        scene = (
            EF().add(EC.set_explore_mode(False))
            # .add(EC.call_obj_function(0x13, FID.ARBITRARY_3, 3, FS.HALT))
            .add(EC.static_animation(0x3E)).add(EC.pause(1))
            .add(EC.call_obj_function(0x14, FID.ARBITRARY_3, 4, FS.HALT))
            # .add(EC.call_obj_function(0x13, FID.ARBITRARY_4, 4, FS.HALT))
            .add(EC.play_animation(0x3)).add(EC.pause(1))
            .add(EC.text_box(str_id, False))
            .add(EC.reset_animation())
            .add(EC.set_flag(memory.Flags.GUARDIA_TREASURY_EXISTS))
            # Allow immediate access to the Yakra XIII Fight
            .add(EC.assign_val_to_mem(
                0x10, memory.Memory.KINGS_TRIAL_PROGRESS_COUNTER, 1))
            # Don't trigger the Gnasher battle.
            .add(EC.set_flag(memory.Flags.GUARDIA_BASEMENT_GNASHERS_BATTLE))
            # .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
        )

        script.set_function(
            scene_obj, FID.STARTUP,
            EF().add(EC.return_cmd()).add(EC.end_cmd())
        )
        script.set_function(scene_obj, FID.ACTIVATE, scene)

        ins_pos = script.get_function_start(king_obj, FID.ACTIVATE)
        ins_block = (
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.RAINBOW_SHELL),
                EF().add_if_else(
                    EC.if_flag(memory.Flags.GUARDIA_TREASURY_EXISTS),
                    EF().add(EC.auto_text_box(str_id)),
                    scene
                )
                .add(EC.return_cmd())
            )
        )

        script.insert_commands(ins_block.get_bytearray(), ins_pos)

    @classmethod
    def fix_partyfollows(cls, script: Event):
        """
        Insert an exploremore on after partyfollows for 1 member teams.
        """

        # Chef scene
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_object_start(0xF)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

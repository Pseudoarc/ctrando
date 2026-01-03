"""Update Guardia Throneroom 1000 for an open world."""
from typing import Optional

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.base import openworldutils as owu

# Arbs
# PCs are called with arbs: 0 (weird), 1, 2, 3, 4, 5,
#  - Arb0 is some sort of waiting routine.
# So anything Arb 6+ is cutscene-specific.  We should update these.
#  - Arb6: Brandish weapon (when escaping from prison)
#  - Arb7: Fist Pump

# Flags
# 0x7F00A1 & 40 - Ask King 600 to guard shell (basement appears)
# 0x7F00A2 & 01 - Go to barracks while escaping
# 0x7F00A2 & 02 - Ask castle chef 1000 about jerky
# 0x7F00A2 & 04 - Set while escaping "no choice but to break through"
# 0x7F00A2 & 08 - Set when leaving the castle while escaping
# 0x7F00A2 & 10 - Set during escape.
# 0x7F00A2 & 20 - Chancellor asks Marle to see king (indirectly killed queen)
# 0x7F00A7 & 02 - Marle and King argue
# 0x7F00A7 & 04 - Tried to give the king jerky
# 0x7F00A7 & 08 - Chancellor suggests giving king jerky
# 0x7F00A7 & 20 - Talked to the king (in chamber) without jerky
# 0x7F00A7 & 40 - Melchior going to the rainbow shell.
# 0x7F00A7 & 80 - Rescue chancellor from the Yakra key box

# Notes:
# - PC Startup objects have logic for placing the characters.  Don't touch.
# - Except for Marle and Lucca, who have extra logic for Crono's prison break.
# - Object 08 seems to be only for the trial.  Should be removable.
# - Object 09 is for plot stuff.  Should be removable.
# - Object 0A is Nadia.  Removable.
# - Object 0F has to do with escaping after Crono's trial.  Removable.
# - Object 10 triggers Crono's imprisonment
# - Object 12 triggers during the escape


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Throneroom 1000"""
    loc_id = ctenums.LocID.GUARDIA_THRONEROOM_1000

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Modify Guardia Throneroom 1000 script.
        """
        # for ind, string in enumerate(script.strings):
        #     print(f'{ind}: {ctstrings.CTString.ct_bytes_to_ascii(string)}')
        # input()

        cls.remove_castle_blockers(script)
        cls.remove_extra_npcs(script)

        cls.fix_marle_lucca_loads(script)
        cls.update_pc_arbs(script)
        cls.alter_escape_sequence(script)
        cls.unlock_front_door(script)
        cls.modify_prison_tower_guards(script)
        cls.modify_throneroom_guards(script)
        cls.update_other_castle_guards(script)
        cls.accelerate_melchior(script)
        cls.modify_king_object(script)
        cls.add_trial_activation(script)

    @classmethod
    def update_pc_arbs(
            cls, script: locationevent.LocationEvent,
            reassign_dict: Optional[dict[ctenums.CharID, ctenums.CharID]]
            = None):
        """
        Unify the arbitrary functions for PC animation.
        - Arb0 through Arb5 are OK as-is
        - Arb6 will become weapon brandishing
        - Arb7 will become a fist pump
        """

        if reassign_dict is None:
            reassign_dict = {char_id: char_id for char_id in ctenums.CharID}

        pc_obj_st = 1
        # Magus has no arb5.  To be safe, fill it in empty.
        script.set_function(pc_obj_st + ctenums.CharID.MAGUS,
                            FID.ARBITRARY_5, EF().add(EC.return_cmd()))

        # The sounds and animations may depend on the pc in the future
        arb_6 = (  # Brandish Weapon (orig Lucca)
            EF()
            .add(EC.play_sound(0x52))
            .add(EC.play_animation(0x0C, True))
            .add(EC.static_animation(0x35))
            .add(EC.return_cmd())
        )

        arb_7 = (  # Fist pump for (orig Crono)
            EF()
            .add(EC.play_animation(0x0B))
            .add(EC.pause(1))
            .add(EC.static_animation(0x6D))
            .add(EC.return_cmd())
        )

        arb_8 = (  # Animation reset
            EF().add(EC.generic_command(0xAE)).add(EC.return_cmd())
        )

        for obj_id in range(1, 1+7):
            script.set_function(obj_id, FID.ARBITRARY_6, arb_6)
            script.set_function(obj_id, FID.ARBITRARY_7, arb_7)
            script.set_function(obj_id, FID.ARBITRARY_8, arb_8)

    @classmethod
    def alter_escape_sequence(cls, script: locationevent.LocationEvent):
        """
        Just kick the party back to the present overworld after the trial.
        """
        # Set animations:
        #   - Everyone has Arb1 for being surprised (good)
        #   - Lucca uses Arb6 for brandishing her gun
        #     - All other PC Arb6 uses are for various scenes we are deleting
        #       so it should be OK to write a brandishing animation for all.
        #   - Crono uses ArbC as a multi-purpose animation depending on the
        #     value of 0x7F021A

        script.dummy_object_out(0xF)   # trigger for Nadia to come out.
        script.dummy_object_out(0x12)  # One trigger for "They're Escaping!"
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0212, OP.GREATER_OR_EQUAL, 0x19, 1))
        script.delete_jump_block(pos)

        # Re-use Obj 11 which is originally used for this part of the escape.
        y_coord = 0x7F0214

        def make_restore_block(pc_id_addr: int,
                               restore_active: bool):
            block = EF()

            if restore_active:
                add_cmd = EC.add_pc_to_active
            else:
                add_cmd = EC.add_pc_to_reserve
            for pc_id in range(6):
                block.add_if(
                    EC.if_mem_op_value(pc_id_addr, OP.EQUALS, pc_id, 1),
                    EF().add(add_cmd(pc_id))
                    .jump_to_label(EC.jump_forward(), f'end{pc_id_addr}')
                )
            block.add(add_cmd(6)).set_label(f'end{pc_id_addr}')
            return block

        # restore_part = (
        #     EF().add_if(
        #         EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC2,
        #                            OP.LESS_OR_EQUAL, 6, 1),
        #         make_restore_block(memory.Memory.CRONO_TRIAL_PC2, True)
        #     ).add_if(
        #         EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC3,
        #                            OP.LESS_OR_EQUAL, 6, 1),
        #         make_restore_block(memory.Memory.CRONO_TRIAL_PC3, False)
        #     )
        # )

        restore_part = (
            EF().add_if(
                EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC2,
                                   OP.LESS_OR_EQUAL, 6, 1),
                make_restore_block(memory.Memory.CRONO_TRIAL_PC2, True)
            ).add_if(
                EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC3,
                                   OP.LESS_OR_EQUAL, 6, 1),
                make_restore_block(memory.Memory.CRONO_TRIAL_PC3, True)
            )
        )

        escape_part = (
            EF()
            .add(EC.call_obj_function(0, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_1, 4, FS.HALT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 4, FS.HALT))
            .add(EC.call_obj_function(0x19, FID.ARBITRARY_6, 5, FS.HALT))
            .add(EC.call_obj_function(0x1A, FID.ARBITRARY_6, 5, FS.HALT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_6, 4, FS.HALT))
            .add(EC.pause(1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_7, 4, FS.HALT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_8, 4, FS.HALT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_8, 4, FS.HALT))
            .add(EC.move_party(0xD, 0x35, 0xD, 0x35, 0xD, 0x35))
            .add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1))
            .add(EC.set_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON))
            # TODO: If other charlocking, restore the charlock byte.
            .add(EC.assign_val_to_mem(0, memory.Memory.CHARLOCK, 1))
            # Remove remaining prison fights
            .add(EC.set_flag(memory.Flags.PRISON_TORTURE_DECEDENT_BATTLE))
            .add(EC.set_flag(memory.Flags.PRISON_STAIRS_GUARD_NW_OUT))
            .add(EC.set_flag(memory.Flags.PRISON_STAIRS_GUARD_SE_OUT))
            .add(EC.set_flag(memory.Flags.PRISON_STAIRS_GUARD_SW_OUT))
            .add(EC.set_flag(memory.Flags.PRISON_CATWALKS_GUARDS_BATTLE))
            .add(EC.set_flag(memory.Flags.PRISON_OMNICRONE_BATTLE))
            .add(EC.set_flag(memory.Flags.PRISON_DECEDENT_BATTLE_NW))
            .add(EC.set_flag(memory.Flags.PRISON_DECEDENT_BATTLE_SE))
            .add(EC.set_flag(memory.Flags.PRISON_STORAGE_GUARD_BATTLE))
            .add(EC.remove_pc_from_active_party(ctenums.CharID.LUCCA))
            .append(restore_part)
            .add(EC.darken(0x1))
            .add(EC.change_location(ctenums.LocID.OW_PRESENT,
                                    0x23, 0x1A, 0, 1, False))
            .add(EC.return_cmd())
        )

        escape_func = (
            EF()
            .add(EC.return_cmd())
            .add_if(
                EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                EF().add(EC.end_cmd())
            )
            .add_if(
                EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK),
                EF()
                .set_label('loop_start')
                .add_if(
                    EC.if_mem_op_value(y_coord, OP.GREATER_THAN, 0x26, 1),
                    escape_part
                )
                .jump_to_label(EC.jump_back(), 'loop_start')
            )
            .add(EC.return_cmd())
        )

        script.set_function(0x11, FID.STARTUP, escape_func)
        script.set_function(0x11, FID.TOUCH, EF())

    @classmethod
    def remove_castle_blockers(cls, script: locationevent.LocationEvent):
        """
        Remove the various ways the game keeps you from accessing the castle.
        - Making the player explore the fair at the start.
        - Making the trial sequence start after returning from 600
        - "Terrorists!" after Crono's trial ends
        """

        # The trial is triggered by Object 0x10's startup.  It just looks at
        # the storyline values and decides whether to kick you out to explore
        # the fair or begin the trial sequence.
        script.dummy_object_out(8)
        script.dummy_object_out(9)
        script.dummy_object_out(0x10)

    @classmethod
    def remove_extra_npcs(cls, script: locationevent.LocationEvent):
        """
        Remove extra soldiers who are spawned during the escape.
        Remove Princess Nadia
        """
        script.dummy_object_out(0xA)
        script.dummy_object_out(0xB)  # chancellor
        script.dummy_object_out(0x1F)
        script.dummy_object_out(0x20)

    @classmethod
    def unlock_front_door(cls, script: locationevent.LocationEvent):
        """
        Unlock the front door of the throneroom.
        """
        lock_condition = EC.if_storyline_counter_lt(0x4E)
        pos = script.get_function_start(0x21, FID.ACTIVATE)

        for _ in range(2):
            pos = script.find_exact_command(lock_condition, pos)
            script.delete_jump_block(pos)

    @classmethod
    def modify_prison_tower_guards(cls, script: locationevent.LocationEvent):
        """
        Put soldiers in front of the prison tower before Crono's trial is done
        and during the King's trial.
        """

        # The guards are in objects 0x19 and 0x1A.  They are practically
        # identical except for dialog.
        guard_objs = (0x19, 0x1A)

        new_text_id = script.add_py_string(
            "Test{null}"
        )

        for obj_id in guard_objs:
            start = script.find_exact_command(
                EC.if_flag(memory.Flags.GUARDIA_TREASURY_EXISTS),
                script.get_function_start(obj_id, FID.STARTUP)
            )

            pos, cmd = script.find_command([0x8B, 0x8D], start)
            pos, cmd2 = script.find_command([0x8B, 0x8D], pos + len(cmd))
            script.insert_commands(
                EF().add_if_else(
                    EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK),
                    EF(),
                    EF().add(cmd)
                ).get_bytearray(), pos + len(cmd2)
            )

            pos = script.find_exact_command(EC.if_storyline_counter_lt(0x51),
                                            pos)
            script.delete_jump_block(pos)

            # Next conditional in activate
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x30), pos
            )

            text_cmd1 = locationevent.get_command(script.data, pos + 3)
            text_id1 = text_cmd1.args[-1]

            _, text_cmd2 = script.find_command([0xBB], pos + 3 + 2)
            text_id2 = text_cmd2.args[-1]

            script.delete_jump_block(pos)
            script.delete_commands(pos, 1)

            new_block = (
                EF()
                .add_if(
                    EC.if_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                    EF().add(EC.auto_text_box(text_id2)).add(EC.return_cmd())
                )
                .add_if_else(
                    EC.if_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK),
                    EF().add(EC.auto_text_box(text_id1)).add(EC.return_cmd()),
                    EF().add(EC.auto_text_box(new_text_id))
                )
            )
            script.insert_commands(new_block.get_bytearray(), pos)

            # remove the conditional that blocks the prison tower during king's trial.
            # It will be blocked before Crono's trial is complete still.
            script.delete_jump_block(start)

    @classmethod
    def fix_marle_lucca_loads(cls, script: locationevent.LocationEvent):
        """
        Remove the conditional loading of Marle and Lucca.
        """
        for obj_id in (2, 3):
            start = script.get_function_start(obj_id, FID.STARTUP)

            script.delete_jump_block(start)
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x8A), start)
            script.delete_jump_block(pos)

    @classmethod
    def accelerate_melchior(cls, script: locationevent.LocationEvent):
        """
        Remove dialogue from party members.  Increase Melchior walk speed.
        """

        melchior_obj = 0xC
        start = script.get_function_start(melchior_obj, FID.ARBITRARY_0)
        script.insert_commands(
            EC.set_move_speed(0x40).to_bytearray(),
            start
        )

        start = script.get_function_start(melchior_obj, FID.ARBITRARY_1)
        script.delete_commands(start, 1)  # Remove a slower set_speed

    @classmethod
    def modify_king_object(cls, script: locationevent.LocationEvent):
        """
        Less dialog.  Delete Marle + King arguing and related flags.
        """

        king_obj = 0xD
        start = script.get_object_start(king_obj)

        # We're allowing access to the throneroom during the king's trial.
        # Let's at least hide the king.
        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.GUARDIA_TREASURY_EXISTS),
                EF().add_if(
                    EC.if_not_flag(memory.Flags.KINGS_TRIAL_COMPLETE),
                    EF().add(EC.remove_object(king_obj))
                    .add(EC.return_cmd()).add(EC.end_cmd())
                )
            ).get_bytearray(), start
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F00A7, OP.BITWISE_AND_NONZERO, 0x02, 1),
            start)
        script.delete_jump_block(pos)

        cmd = EC.call_obj_function(0, FID.ARBITRARY_0, 4, FS.HALT)
        pos = script.find_exact_command(cmd, pos) + len(cmd)

        script.data[pos+1] //= 2  # halve a pause command
        pos += 4  # Skipping two commands

        # Delete character responses to king
        for _ in range(5):
            script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE), pos
        )

        # Delete everyone's 'Melchior!' text
        for _ in range(5):
            script.delete_jump_block(pos)

        # Now alter the activate function to remove the big argument scene
        str_ind = 52  # Precomputed "What do you want?" string index

        start = script.find_exact_command(
            EC.call_obj_function(0, FID.ARBITRARY_0, 4, FS.HALT),
            pos)

        end = script.find_exact_command(EC.party_follow(), start) + 1

        script.insert_commands(EC.auto_text_box(str_ind).to_bytearray(), start)
        start += 2
        end += 2
        script.delete_commands_range(start, end)

    @classmethod
    def update_other_castle_guards(cls, script: locationevent.LocationEvent):
        """
        Update guards not involved in the escape sequence.
        """

        guard_objs = (0x13, 0x14, 0x15, 0x16)

        for obj_id in guard_objs:
            pos = script.get_object_start(obj_id)
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x51), pos)
            script.delete_jump_block(pos)

            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x30), pos)
            script.replace_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.HAS_DEFEATED_DRAGON_TANK)
            )

    @classmethod
    def add_trial_activation(cls, script: locationevent.LocationEvent):
        """
        Re-use a guard object to add the trial activation (similar to jets)
        """

        guard_obj = 0x13

        text_id = script.add_py_string(
            "Turn yourself in? {line break}"
            "   Yes{line break}"
            "   No{null}"
        )

        startup = (
            EF().add_if_else(
                EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
                EF().add(EC.load_npc(ctenums.NpcID.CRONOS_MOM))
                .add(EC.set_object_coordinates_tile(0x1D, 0x33)),
                EF().add(EC.remove_object(guard_obj))
            )
            .add(EC.return_cmd()).add(EC.end_cmd())
        )

        # startup = (
        #     EF().add_if_else(
        #         EC.if_not_flag(memory.Flags.HAS_ESCAPED_GUARDIA_PRISON),
        #         EF().add(EC.load_pc_always(ctenums.CharID.LUCCA))
        #         .add(EC.set_object_coordinates_tile(0x1D, 0x33)),
        #         EF().add(EC.remove_object(guard_obj))
        #     )
        #     .add(EC.return_cmd()).add(EC.end_cmd())
        # )

        def make_remove_block(pc_id_addr: int,
                              pc_id_copy_addr: int):
            block = EF()
            block.add(EC.assign_mem_to_mem(pc_id_addr, 0x7F0222, 1))
            for pc_id in range(7):
                block.add_if(
                    EC.if_mem_op_value(0x7F0222, OP.EQUALS, pc_id, 1),
                    EF().add(EC.remove_pc_from_active_party(pc_id))
                    .jump_to_label(EC.jump_forward(), f'end{pc_id_addr}')
                )

            block.set_label(f'end{pc_id_addr}')
            block.add(EC.assign_mem_to_mem(0x7F0222, pc_id_copy_addr, 1))
            return block

        activate = (
            EF()
            .add_if_else(
                EC.if_pc_active(ctenums.CharID.LUCCA),
                EF()
                .add(EC.decision_box(text_id, 1, 2))
                .add_if(
                    EC.if_result_equals(1),
                    EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1,
                                                  0x7F0222, 1))
                    .add_if(
                        EC.if_mem_op_value(0x7F0222, OP.EQUALS, ctenums.CharID.LUCCA),
                        EF().add(EC.auto_text_box(
                            script.add_py_string("Lucca can't go to prison!{null}")
                        )).add(EC.return_cmd())
                    )
                    .add(EC.assign_mem_to_mem(0x7F0222,
                                              memory.Memory.CRONO_TRIAL_PC1, 1))
                    .append(make_remove_block(memory.Memory.ACTIVE_PC2,
                                              memory.Memory.CRONO_TRIAL_PC2))
                    .append(make_remove_block(memory.Memory.ACTIVE_PC3,
                                              memory.Memory.CRONO_TRIAL_PC3))
                    # There are so many object-specific functions in the trial.
                    # We're just going to charlock everyone to avoid it.
                    # TODO: If we have LoC-ish charlocking this needs to change.
                    .add(EC.assign_val_to_mem(0xFE, memory.Memory.CHARLOCK, 1))
                    .add(EC.change_location(0x1C, 8, 9, 0, 3, False))
                ),
                EF().add(EC.auto_text_box(
                    script.add_py_string("Bring Lucca in case they try to{line break}"
                                         "execute you.{null}")
                ))
            )
        )

        # activate = (
        #     EF().add(EC.decision_box(text_id, 1, 2))
        #     .add_if(
        #         EC.if_result_equals(1),
        #         EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1,
        #                                       0x7F0222, 1))
        #         .add(EC.assign_mem_to_mem(0x7F0222,
        #                                   memory.Memory.CRONO_TRIAL_PC1, 1))
        #         .append(make_remove_block(memory.Memory.ACTIVE_PC2,
        #                                   memory.Memory.CRONO_TRIAL_PC2))
        #         .append(make_remove_block(memory.Memory.ACTIVE_PC3,
        #                                   memory.Memory.CRONO_TRIAL_PC3))
        #         # There are so many object-specific functions in the trial.
        #         # We're just going to charlock everyone to avoid it.
        #         # TODO: If we have LoC-ish charlocking this needs to change.
        #         .add(EC.assign_val_to_mem(0xFE, memory.Memory.CHARLOCK, 1))
        #         .add(EC.change_location(0x1C, 8, 9, 0, 3, False))
        #     )
        # )

        script.set_function(guard_obj, FID.STARTUP, startup)
        script.set_function(guard_obj, FID.ACTIVATE, activate)
        script.set_function(guard_obj, FID.TOUCH,
                            EF().add(EC.return_cmd()))

    @classmethod
    def modify_throneroom_guards(cls, script: locationevent.LocationEvent):
        """
        Do not make the guards block the throneroom during the trial.
        Do not make the guards block the exit when the shell item is taken.
        """
        guard_objs = (0x15, 0x16)
        for obj_id in guard_objs:
            pos = script.find_exact_command(
                EC.if_flag(memory.Flags.GUARDIA_TREASURY_EXISTS),
                script.get_object_start(obj_id)
            )
            script.delete_jump_block(pos)

        # These are guards who are only spawned during the trial.
        blocker_guard_objs = (0x1D, 0x1E)
        for obj_id in blocker_guard_objs:
            pos = script.get_object_start(obj_id)
            script.delete_commands(pos, 1)

            pos = script.get_function_start(obj_id, FID.TOUCH)
            script.insert_commands(
                EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1)
                .to_bytearray(), pos
            )

            script.set_function(
                obj_id, FID.ACTIVATE,
                EF().add(EC.return_cmd())
            )

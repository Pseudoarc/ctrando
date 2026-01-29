"""Openworld Zenan Bridge 600AD"""
from typing import Optional

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


# Zenan Bridge Notes:
# - Two flags can alter basic the behavior of this location.
#   1) 0x7F0057 & 02 -- Cyrus and Glenn talk about becoming knights
#   2) 0x7F0057 & 04 -- Zombor scene played during attract mode.
# - The flag 0x7F00A9 & 10 is set when the chef gives the jerky and is used
#   here to signal that the battle can begin.

# Object Layout
# - Object 00: Just takes care of music
# - Object 01: Some basic control flow
#   - Keep the party from moving down the bridge until the jerky is turned in
#   - Trigger the battles.
# - Object 02: Just play a sound during some pre-battle scenes
# - Object 03 - 09: PC Objects
#   - Some special casing for the attract mode scene
#   - Arbs defined for Crono, Marle, Lucca, Robo
#     - Crono Arb0 is a battle pose, Arb1 is called when the party tries to go
#       on the bridge too early.
#     - Everyone else arb0 taunts ozzie after 2nd battle, arb1 after first
#       battle, and arb2 before Zombor.
# - Object 0A: Ozzie
# - Object 0B, 0C: Zombor top/bottom
# - Object 0D: Knight Captain
# - Object 0E - 12, 15-17: Various knights
# - Object 14, 18-1C: Skeleton enemies.  Some decedent, some deceased
#   - Probably some difference between zombor parts and actual enemies.
# - Object 1D: Cyrus
# - Object 1E: Glenn


class EventMod(locationevent.LocEventMod):
    """EventMod for Zenan Bridge 600AD"""
    loc_id = ctenums.LocID.ZENAN_BRIDGE_600

    @classmethod
    def modify(cls, script: Event):
        """
        Update The Zenan Bridge 600AD Event.
        - Make the guard captain turn-in just be having the jerky.
        - Replace storyline conditions with flag conditions.
        - Set the new overworld flags upon defeating Zombor.
        """

        # print('ZENAN STRINGS END')
        # from ctrando.strings import ctstrings
        # for ind, ct_string in enumerate(script.strings):
        #     py_string = ctstrings.CTString.ct_bytes_to_ascii(ct_string)
        #     print(f"{ind:02X}: {py_string}")
        #
        # input('ZENAN STRINGS END')

        
        cls.modify_startup_music(script)
        # cls.delete_unused_objects(script)
        cls.modify_pc_arbs(script)
        cls.modify_bridge_battles(script)
        cls.modify_captain_activation(script)
        cls.modify_storyline_triggers(script)
        cls.modify_ozzie(script)

    @classmethod
    def modify_startup_music(cls, script: Event):
        """
        Change the conditions for the music to match the flags instead of
        storyline triggers.
        """

        # Delete block that controls the music.
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CHEF_GIVES_JERKY)
        )
        end_cmd = EC.play_song(0xC)
        end_pos = script.find_exact_command(end_cmd) + len(end_cmd)
        script.delete_commands_range(pos, end_pos)

        new_music_block = (
            EF().add_if(
                EC.if_flag(memory.Flags.OW_ZENAN_COMPLETE),
                EF().add(EC.play_song(2))
                .jump_to_label(EC.jump_forward(), 'end')
            )
            .add_if(
                EC.if_flag(memory.Flags.OW_ZENAN_STARTED),
                EF().add(EC.play_song(0x45))
                .jump_to_label(EC.jump_forward(), 'end')
            )
            .add(EC.play_song(0xC))
            .set_label('end')
        )
        script.insert_commands(new_music_block.get_bytearray(), pos)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Update all PC objects to have the same function for their arbs.
        """

        # Arb0: Called to return the party if they venture too far before their
        #       Jerky is turned in.
        arb_0 = (
            EF().add(EC.set_move_speed(0x40))
            .add(EC.move_sprite(0x37, 8))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )

        # Arb1: Called by PC02 to taunt ozzie before Zombor.  Anim depends
        # on PC

        # Arb2: Turn right to face Zombor and assume a battle pose.
        arb_2 = (
            EF().add(EC.set_own_facing('right'))
            .add(EC.play_animation(0x21))
            .add(EC.return_cmd())
        )

        for obj_id in range(3, 0xA):
            pc_id = ctenums.CharID(obj_id - 3)
            script.set_function(obj_id, FID.ARBITRARY_0, arb_0)
            script.set_function(obj_id, FID.ARBITRARY_1, get_pc_arb1(pc_id))
            script.set_function(obj_id, FID.ARBITRARY_2, arb_2)

    @classmethod
    def modify_bridge_battles(cls, script: Event):
        """
        Rewrite object 01 to remove dialog and call the proper pc arbs.
        """
        prevent_access_func = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.OW_ZENAN_STARTED),
                EF().add_if(
                    # if x-coord == 0x33
                    EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x33),
                    EF().add(EC.set_explore_mode(False))
                    .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 6,
                                              FS.HALT))
                    .add(EC.call_pc_function(0, FID.ARBITRARY_0, 6,
                                             FS.HALT))
                )
            )
        )

        got_item_id = owu.add_default_treasure_string(script)

        boss_fight_block = (
            EF().add(EC.remove_object(0x11)).add(EC.remove_object(0x12))
            .add(EC.generic_command(0xE7, 0, 1))  # scroll screen
            .add(EC.move_party(0x86, 8, 0x88, 7, 0x89, 0xA))
            .add(EC.text_box(0x26, False))
            .add(EC.call_pc_function(1, FID.ARBITRARY_1, 6, FS.HALT))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_4, 6, FS.HALT))
            .add(EC.generic_command(0xE7, 4, 1))
            .add(EC.call_obj_function(0x19, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.generic_command(0xAD, 9))  # pause
            .add(EC.call_obj_function(2, FID.TOUCH, 6, FS.CONT))
            .add(EC.call_obj_function(0x1C, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_2, 5, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_2, 5, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_2, 5, FS.CONT))
            .add(EC.generic_command(0xBA))  # Pause 1
            .add(EC.call_obj_function(0x1A, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.generic_command(0xBA))  # Pause 1
            .add(EC.call_obj_function(0x1B, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.generic_command(0xAD, 0x30))
            .add(EC.remove_object(2))
            .add(EC.play_sound(0xBE))
            .add(EC.generic_command(0xAD, 0x28))
            .add(EC.call_obj_function(0xB, FID.TOUCH, 6, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.TOUCH, 6, FS.CONT))
            .add(EC.generic_command(0xAD, 0x28))
            .add(EC.play_song(0x29))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_5, 6, FS.HALT))
            .add(EC.remove_object(0xA))
            .add(EC.move_party(0x84, 0x86, 0x83, 0x88, 0x84, 0x8B))
            .add(EC.generic_command(0xD8, 0x83, 0xC0))
            .add(EC.set_flag(memory.Flags.OW_ZENAN_COMPLETE))
            .add(EC.assign_val_to_mem(ctenums.ItemID.GOLD_HELM, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(got_item_id))
            .append(owu.get_increment_quest_complete())
            .add(EC.play_song(0xC))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))
        )

        first_fight_func = (
            EF().add(EC.set_flag(memory.Flags.ZENAN_BATTLE_1))
            .add(EC.generic_command(0xE7, 0x1E, 0x01))  # Scroll
            .add(EC.call_obj_function(0x13, FID.TOUCH, 6, FS.CONT))
            .add(EC.call_obj_function(0x15, FID.ARBITRARY_1, 6, FS.CONT))
            .add(EC.generic_command(0xBC))  # pause
            .add(EC.call_obj_function(0x14, FID.TOUCH, 6, FS.CONT))
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.generic_command(0xBD))  # pause
            .add(EC.call_obj_function(0x15, FID.ARBITRARY_2, 6, FS.CONT))
            .add(EC.call_obj_function(0x16, FID.ARBITRARY_1, 6, FS.CONT))
            .add(EC.call_obj_function(0x17, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.generic_command(0xBC))  # pause
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 6, FS.HALT))
            .add(EC.move_party(0xA8, 0x08, 0xAA, 0xA, 0xAA, 0x7))
            .add(EC.generic_command(0xD8, 0x81, 0xC0))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_2, 6, FS.CONT))
        )

        second_fight_func = (
            EF().add(EC.set_flag(memory.Flags.ZENAN_BATTLE_2))
            .add(EC.generic_command(0xE7, 0xE, 0x01))  # Scroll
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_1, 6, FS.HALT))
            .add(EC.move_party(0x95, 0x08, 0x96, 0x89, 0x97, 0x87))
            .add(EC.generic_command(0xD8, 0x81, 0xC0))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_3, 6, FS.CONT))
        )

        fight_func = (
            EF().add_if_else(
                EC.if_flag(memory.Flags.ZENAN_BATTLE_1),
                EF().add_if_else(
                    # If 2nd battle, then check for boss
                    EC.if_flag(memory.Flags.ZENAN_BATTLE_2),
                    EF().add_if(
                        EC.if_not_flag(memory.Flags.OW_ZENAN_COMPLETE),
                        EF().add_if(
                            EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0xB),
                            boss_fight_block
                        )
                    ),
                    # Else check for 2nd battle
                    EF().add_if(
                        EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x17),
                        second_fight_func
                    )
                ),
                EF().add_if(
                    EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x2A),
                    first_fight_func
                )
            )
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CHEF_GIVES_JERKY),
            script.get_function_start(1, FID.STARTUP)
        )
        script.delete_jump_block(pos)  # prevent_access_func
        script.delete_jump_block(pos)  # boss + fight 2
        script.delete_jump_block(pos)  # first fight

        script.insert_commands(fight_func.get_bytearray(), pos)
        script.insert_commands(prevent_access_func.get_bytearray(), pos)

    @classmethod
    def modify_captain_activation(cls, script: Event):
        """
        - Modify the guard captain to take the jerky instead of checking their
          chef flag.
        - Set the OW flag for Zenan
        - Move the item check to after the boss battle
        """
        captain_obj = 0xD
        pos = script.get_function_start(captain_obj, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_flagdata(memory.FlagData(0x7F00A9, 0x10)),  # chef jerky
            pos
        )

        # Now pointing at if storyline < 57
        repl_cmd = EC.if_not_flag(memory.Flags.OW_ZENAN_STARTED)
        script.replace_jump_cmd(
            pos, repl_cmd
        )
        pos += len(repl_cmd)
        repl_cmd = EC.if_has_item(ctenums.ItemID.JERKY)
        script.replace_jump_cmd(pos, repl_cmd)

        # Delete the item check from the guard captain
        del_pos = script.find_exact_command(
            EC.if_flag(memory.Flags.ZENAN_CAPTAIN_ITEM, pos)
        )
        script.delete_commands(del_pos, 1)

        block = EF().add(EC.set_flag(memory.Flags.OW_ZENAN_STARTED))

        str_pos = script.find_exact_command(EC.auto_text_box(0x19), pos)
        script.data[str_pos+1] = 2

        ins_pos = script.find_exact_command(EC.jump_forward(), pos)
        script.insert_commands(block.get_bytearray(), ins_pos)

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x5A),
                                        ins_pos)
        script.delete_jump_block(pos)

        pos = script.find_exact_command(EC.set_bit(0x7F00A9, 0x04))

        new_block = (
            EF().add_if(
                EC.if_flag(memory.Flags.OW_ZENAN_COMPLETE),
                EF().add(EC.auto_text_box(0x19))
                .jump_to_label(EC.jump_forward(), 'end')
            ).add_if(
                EC.if_flag(memory.Flags.OW_ZENAN_STARTED),
                EF().add(EC.auto_text_box(0x17))
                .jump_to_label(EC.jump_forward(), 'end')
            ).add(EC.auto_text_box(2))
            .set_label('end')
        )

        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 2)

        # Shorten some of the intro dialog
        pos = script.get_function_start(0x15, FID.ARBITRARY_0)
        pos = script.find_exact_command(EC.set_storyline_counter(0x57), pos)
        script.delete_commands(pos, 4)

    @classmethod
    def modify_ozzie(cls, script: Event):
        """
        Modify Ozzie's object:
        - Draw status depending on flags and not storyline.
        - Fix some of his arbs to add exploremode on after partyfollow
        - Remove some dialogue.
        """

        ozzie_obj = 0xA
        pos = script.get_function_start(ozzie_obj, FID.ARBITRARY_2)

        for _ in range(2):
            pos = script.find_exact_command(EC.party_follow(), pos) + 1
            script.insert_commands(
                EC.set_explore_mode(True).to_bytearray(), pos)
            pos += 2  # len of exploremode

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        Also remove some checks that are essentially storyline checks.
          - Chef Jerky check
        """

        storyline_flag_dict: dict[int, Optional[memory.Flags]] = {
            0x57: memory.Flags.OW_ZENAN_STARTED,
            0x5A: memory.Flags.OW_ZENAN_COMPLETE,
            0x8A: memory.Flags.OW_ZENAN_COMPLETE,
            0x8D: memory.Flags.OW_ZENAN_COMPLETE,
            0xA8: None
        }

        owu.storyline_to_flag(script, storyline_flag_dict)

        pos: Optional[int] = script.get_object_start(0)
        while True:
            pos = script.find_exact_command_opt(
                EC.if_flag(memory.Flags.CHEF_GIVES_JERKY),
                pos
            )

            if pos is None:
                break

            script.delete_commands(pos, 1)

    # This might not be needed b/c they never load actual graphics.
    # @classmethod
    # def delete_unused_objects(cls, script: Event):
    #     '''Delete Cyrus/Glenn cutscene objects'''
    #     script.remove_object(0x1E)  # Glenn
    #     script.remove_object(0x1D)  # Cyrus


# Provide this as a function so that DC can reassign arbs properly.
def get_pc_arb1(pc_id: ctenums.CharID) -> EF:
    """Gets the pre-zombor PC taunt animation function"""
    ret_fn = EF()
    if pc_id == ctenums.CharID.MARLE:
        (ret_fn.add(EC.static_animation(0xC4))
         .add(EC.pause(0.5))
         .add(EC.static_animation(0xC5))
         .add(EC.return_cmd())
         )
    elif pc_id == ctenums.CharID.LUCCA:
        (ret_fn.add(EC.play_animation(0x13))
         .add(EC.pause(0.5))
         .add(EC.static_animation(0x74))
         .add(EC.return_cmd())
         )
    else:
        (ret_fn.add(EC.play_animation(3))
         .add(EC.pause(0.5))
         .add(EC.return_cmd())
         )

    return ret_fn            

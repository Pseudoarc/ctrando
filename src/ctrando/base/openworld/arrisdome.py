"""Openworld Arris Dome"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome"""
    loc_id = ctenums.LocID.ARRIS_DOME

    doan_obj = 0xE
    doan_reward_obj = 0xF

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Event.
        - Replace storyine triggers with flags (much dialogue)
        - Remove first entry cutscene
        - Modify Doan's reward condition
        """

        cls.remove_intro_scenes(script)
        cls.modify_doan_reward(script)

    @classmethod
    def remove_intro_scenes(cls, script: Event):
        """
        - Remove the scenes that plays when you first enter the Arris Dome:
          1) The scene where Doan is surprised that people crossed the lab
          2) The scene when the party first climbs down the ladder
        - Fix the initial animations that are reset by scene #1
        """

        # Get rid of the entry cutscene (#1 in docstring)
        pos = script.get_object_start(cls.doan_obj)
        del_st = script.find_exact_command(
            EC.return_cmd(), pos
        ) + 1
        cmd = get_command(script.data, del_st)  # check storyline < 0x33
        del_end = del_st + cmd.args[-1] + len(cmd) - 1

        cmd = get_command(script.data, del_end)  # check storyline < 0x37 (unused)
        del_end += cmd.args[-1] + len(cmd) - 1
        del_end += 2  # trailing goto
        script.delete_commands_range(del_st, del_end)

        # Get rid of the ladder down scene (#2 in docstring)
        pos = script.get_function_start(cls.doan_reward_obj, FID.TOUCH)
        script.delete_jump_block(pos)

        sitting_npc_ids = [
            cls.doan_obj, 0x10, 0x11, 0x13, 0x14, 0x15, 0x16, 0x17,
        ]

        for obj_id in sitting_npc_ids:
            pos = script.get_object_start(obj_id)
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x34), pos
            )
            end = script.find_exact_command(EC.return_cmd(), pos)
            script.delete_commands_range(pos, end)

            if obj_id != cls.doan_obj:
                pos = script.find_exact_command(
                    EC.if_storyline_counter_lt(0x34), pos
                )
                script.delete_jump_block(pos)

    @classmethod
    def modify_doan_reward(cls, script: Event):
        """
        Modify Doan to give a reward for bringing the seed after Guardian.
        Modifies the Doan reward function and the ladder touch object.
        """

        # The main modification comes to the ladder touch object

        # input(script.get_function(cls.doan_reward_obj, FID.TOUCH))

        reward_block = (
            EF().add(EC.set_explore_mode(False))
            .add(EC.play_song(0))
            .add(EC.assign_val_to_mem(1, 0x7F020C, 1))
            # These are functions that block the object from doing anything
            # while 0x7F020C has a value of 1.
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.move_party(0x30, 0xC, 0x2F, 0xD, 0x31, 0xD))
            .add(EC.call_pc_function(0, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_4, 4, FS.CONT))
        )

        for ind in range(7):
            reward_block.add(EC.set_object_facing(ind+1, 'up'))

        (
            reward_block.add(EC.call_obj_function(cls.doan_obj, FID.ARBITRARY_1,
                                                  4, FS.HALT))
            .add(EC.call_obj_function(cls.doan_obj, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.play_sound(8))
            .add(EC.auto_text_box(0x32))
            .add(EC.assign_val_to_mem(ctenums.ItemID.BIKE_KEY, 0x7F0200, 1))
            .add(EC.add_item(ctenums.ItemID.BIKE_KEY))
            .add(EC.auto_text_box(
                script.add_py_string('{line break}Got 1 {item}!{line break}'
                                     '{itemdesc}{null}')
            ))
            .add(EC.set_flag(memory.Flags.OBTAINED_DOAN_ITEM))
            .add(EC.assign_val_to_mem(0, 0x7F020C, 1))
            .add(EC.party_follow())
            .add(EC.set_explore_mode(True))
        )

        new_touch_function = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.OBTAINED_DOAN_ITEM),
                EF().add_if(
                    EC.if_flag(memory.Flags.GUARDIAN_DEFEATED),
                    EF().add_if(
                        EC.if_has_item(ctenums.ItemID.SEED),
                        reward_block
                    )
                )
            ).add(EC.return_cmd())
        )

        script.set_function(cls.doan_reward_obj, FID.TOUCH, new_touch_function)

        # temp = script.get_function(cls.doan_obj, FID.ACTIVATE)
        # input(temp)
        new_doan_activate_function = (
            EF().add_if_else(
                EC.if_not_flag(memory.Flags.OBTAINED_DOAN_ITEM),
                EF().add_if_else(
                    EC.if_flag(memory.Flags.GUARDIAN_DEFEATED),
                    EF().add_if_else(
                        EC.if_has_item(ctenums.ItemID.SEED),
                        EF().add(EC.move_party(0x2F, 0xD, 0x2E, 0xE, 0x30, 0xE))
                        .add(EC.call_obj_function(0xF, 2, 4, FS.SYNC))  # Why sync?
                        .add(EC.return_cmd()),
                        EF().add(EC.auto_text_box(
                            script.add_py_string(
                                'DOAN: Are you sure there was no food?{line break}'\
                                'Not even a Seed?{null}')
                        ))
                    ),
                    # Can't clear the robots
                    EF().add(EC.auto_text_box(0xB))
                ),
                # Take care and stay healthy
                EF().add(EC.auto_text_box(0x34))
            ).add(EC.return_cmd())
        )
        script.set_function(cls.doan_obj, FID.ACTIVATE, new_doan_activate_function)

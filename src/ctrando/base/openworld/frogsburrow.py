"""Openworld Frog's Burrow"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
from ctrando.strings import ctstrings

# Event Notes:
# 1) 0x7F0210 is used to help determine something about the state of the room.
#    - A value of 4 means that Magus has been defeated.
#    - A value of 3 means that Frog has been recruited
#    - A value of 2 means that the hilt has been obtained
#    - A value of 1 means that we've shown the medal to Frog
#    - A value of 0 means that nothing has happened.

# 2) 0x7F00FF is used to keep track of the cutscene when frog receives Masa.
#    - It looks like 0x20 is set for the first return to the burrow and 0x40 is
#      set for the second return to the burrow during the scene.
#    - The 0x80 bit seems to be used for whether Frog is blocking the chest

# 3) 0x7F00F3 is used to control a cutscene too.
#    - The 0x03 bits are set depending on which chars are present
#    - 0x10 is used to determine whether Frog has been shown the medal I think

# We basically have to rewrite the core logic.
# 1) In Obj00 startup:
#    - Use 0x7F0210 to determine if Medal is present
#    - Use 0x7F0212 to determine if Masa is present
#    - Use 0x7F0214 to determine the status of the room
# 2) Room status determined as follows:
#    - Status 0: No progress, sad Frog on front of box (skip falling scene)
#    - Status 1: Has shown medal but no recruit: Sad Frog in middle of room.
#    - Status 2: Frog Has been recruited: Do nothing with Frog.


# noinspection DuplicatedCode
_char_objs: dict[ctenums.CharID, int] = {
    ctenums.CharID.CRONO: 1,
    ctenums.CharID.MARLE: 2,
    ctenums.CharID.LUCCA: 3,
    ctenums.CharID.FROG: 4,
    ctenums.CharID.ROBO: 5,
    ctenums.CharID.AYLA: 6,
    ctenums.CharID.MAGUS: 7
}


class EventMod(locationevent.LocEventMod):
    """EventMod for Frog's Burrow"""
    loc_id = ctenums.LocID.FROGS_BURROW

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Frog's Burrow Event.
        - Rewrite the Obj00 startup to depend on obtained items.
        """

        # for ind, string in enumerate(script.strings):
        #     py_str = ctstrings.CTString.ct_bytes_to_ascii(string)
        #     print(f'{ind:02X}: {py_str}')
        # input()
        cls.write_new_obj00(script)
        cls.modify_pc_objects(script)
        cls.remove_falling_recruit(script)
        cls.modify_burrow_left_chest(script)
        cls.modify_blue_sparkle(script)

    @classmethod
    def modify_pc_objects(cls, script: Event):
        """
        Remove all special casing from the startup.
        """
        for pc_id in ctenums.CharID:
            obj_id = _char_objs[pc_id]
            script.set_function(
                obj_id, FID.STARTUP,
                EF().add(EC.load_pc_in_party(pc_id))
                .add(EC.return_cmd())
                .add(EC.set_controllable_infinite())
                .add(EC.end_cmd())
            )

        script.set_function(_char_objs[ctenums.CharID.FROG], FID.ACTIVATE,
                            EF().add(EC.return_cmd()))

    @classmethod
    def write_new_obj00(cls, script: Event):
        """
        Rewrite the object 00 startup
        - Determine whether KIs are present
        - Determine quest status
        """

        del_st = script.find_exact_command(
            EC.assign_val_to_mem(4, 0x7F0210, 1))
        del_end = script.find_exact_command(EC.return_cmd(), del_st)

        script.delete_commands_range(del_st, del_end)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.HAS_SHOWN_MEDAL))
            .add(EC.play_song(0x1E)).get_bytearray(), del_st
        )

        # Determining whether to show open pot or closed.
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x69),
                                        del_st)
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.OBTAINED_BURROW_LEFT_ITEM))

        pos += len(EC.if_not_flag(memory.Flags.OBTAINED_BURROW_LEFT_ITEM))
        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.HAS_SHOWN_MEDAL),
                EF().add(EC.call_obj_function(9, FID.ARBITRARY_0, 5, FS.CONT))
            ).get_bytearray(), pos
        )

    @classmethod
    def remove_falling_recruit(cls, script: Event):
        """
        Remove the coordinate check that makes a recruit fall from the top.
        """
        pos = script.find_exact_command(EC.return_cmd())
        script.insert_commands(EC.remove_object(8).to_bytearray(), pos)

    @classmethod
    def modify_burrow_left_chest(cls, script: Event):
        """
        Modify the activation of the left burrow chest.
        - Remove lock (rely on recruit moving)
        - Shorten the scene by removing dialog/animations.
        """

        left_chest_obj = 0xA
        script.set_function(
            left_chest_obj, FID.STARTUP,
            EF().add_if_else(
                EC.if_flag(memory.Flags.HAS_SHOWN_MEDAL),
                EF().add(EC.set_object_coordinates_pixels(0x28, 0x70)),
                EF().add(EC.set_object_coordinates_auto(0x30, 0x40))
            )
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        script.set_function(
            left_chest_obj, FID.ACTIVATE,
            EF().add_if(
                EC.if_flag(memory.Flags.OBTAINED_BURROW_LEFT_ITEM),
                EF().add(EC.return_cmd())
            )
            .add(EC.set_explore_mode(False))
            .add(EC.call_obj_function(9, FID.ARBITRARY_0, 6, FS.CONT))
            .add(EC.play_sound(0x65))
            .add(EC.generic_command(0xE5,
                                    0, 0xF, 0, 0xF, 2, 6, 0x71))  # copy tiles
            .add(EC.play_song(0)).add(EC.pause(0.25))
            .add(EC.generic_command(0xEB, 0, 0))
            .add(EC.generic_command(0xEB, 0x20, 0xFF))  # song volume
            .add(EC.play_song(0x10))
            .add(EC.move_party(1, 9, 2, 0xA, 3, 9))
            .add(EC.remove_object(9))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 3, FS.HALT))
            .add(EC.generic_command(0xEB, 0x20, 0))  # song volume
            .add(EC.pause(0.563))
            .add(EC.play_song(0))
            .add(EC.generic_command(0xEB, 0x10, 0xFF))  # song volume
            .add(EC.play_song(0x1E))
            .add(EC.remove_object(0xB))
            .add(EC.assign_val_to_mem(ctenums.ItemID.BENT_HILT, 0x7F0200, 1))
            .add(EC.add_item(ctenums.ItemID.BENT_HILT))
            .add(
                EC.auto_text_box(
                    script.add_py_string('{line break}Got 1 {item}!{line break}'
                                         '{itemdesc}{null}'))
            )
            .add(EC.set_flag(memory.Flags.OBTAINED_BURROW_LEFT_ITEM))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))
        )

    @classmethod
    def modify_blue_sparkle(cls, script: Event):
        """
        Change the appear/disappear conditions for the sparkle.
        """

        sparkle_obj = 0x9
        script.set_function(
            sparkle_obj, FID.STARTUP,
            EF().add(EC.load_npc(0x71))
            .add(EC.script_speed(0x18))
            .add(EC.set_own_drawing_status(False))
            .add(EC.return_cmd()).add(EC.end_cmd())
        )

        script.set_function(
            sparkle_obj, FID.ARBITRARY_1,
            EF().add(EC.set_object_coordinates_pixels(0x4F, 0x98))
            .add(EC.generic_command(0x84, 0))
            .add(EC.set_own_drawing_status(True))
            .add(EC.return_cmd())
        )

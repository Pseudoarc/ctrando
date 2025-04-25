"""Openworld Denadoro Mts Cave of Masamune"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Facing
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Denadoro Mts Cave of Masamune"""
    loc_id = ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE
    _pc_obj_dict: dict[ctenums.CharID, int] = {
        ctenums.CharID.CRONO: 1, ctenums.CharID.MARLE: 2,
        ctenums.CharID.LUCCA: 3, ctenums.CharID.ROBO: 5,
        ctenums.CharID.FROG: 4, ctenums.CharID.AYLA: 6,
        ctenums.CharID.MAGUS: 7
    }
    
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Denadoro Mts Cave of Masamune.
        - Set Flags instead of storyline.
        - Give all PCs the right arbs for the Masa & Mune scenes
        - Remove dialog from the various Masa & Mune scenes
        """
        cls.modify_storyline_triggers(script)
        cls.modify_pc_arbs(script)
        cls.modify_cutscenes(script)
        cls.add_save_warp(script)

    @classmethod
    def add_save_warp(cls, script: Event):
        """Saying no to being here for the Masamune returns to the save point."""
        pos = script.find_exact_command(EC.play_sound(0x51),
                                        script.get_function_start(0xD, FID.ARBITRARY_0))
        warp_block = (
            EF().add(EC.pause(1.0))
            .add(EC.darken(0x1))
            .add(EC.fade_screen())
            .add(EC.change_location(ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR,
                                    0x03, 0x04, Facing.DOWN, 0, True))
        )
        script.insert_commands(warp_block.get_bytearray(), pos)

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """Replace storyline < 0x60 with not having the KI"""
        key_flag = memory.Flags.OBTAINED_DENADORO_KEY
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x60))
        script.replace_jump_cmd(pos, EC.if_not_flag(key_flag))

        pos = script.find_exact_command(
            EC.set_storyline_counter(0x60),
            script.get_function_start(0xA, FID.TOUCH)
        )
        script.replace_command_at_pos(pos, EC.set_flag(key_flag))

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """Give non-plot PCs their missing arb functions."""
        missing_pcs = [ctenums.CharID.FROG, ctenums.CharID.AYLA,
                       ctenums.CharID.MAGUS]

        arb_1 = EF().add(EC.return_cmd())
        arb_2 = (
            EF().add(EC.play_animation(9)).add(EC.pause(0.5)).
            add(EC.play_animation(0x22)).add(EC.return_cmd())
        )

        for pc_id in missing_pcs:
            obj_id = cls._pc_obj_dict[pc_id]
            script.set_function(obj_id, FID.ARBITRARY_1, arb_1)
            script.set_function(obj_id, FID.ARBITRARY_2, arb_2)

    @classmethod
    def modify_cutscenes(cls, script: Event):
        """Remove dialog and animations from the Masa & Mune scenes."""
        cls.modify_pre_battle_scene(script)
        cls.modify_between_battle_scene(script)
        cls.modify_post_battle_scene(script)
        cls.modify_item_collection_scene(script)

    @classmethod
    def modify_pre_battle_scene(cls, script: Event):
        """Remove dialog from the scene before the split Masa, Mune fight."""

        # Scene is in Object 0C startup.
        # This is Masa's (kid) object.  It is turned off until the player says
        # they are there for the sword.  Then the scene proceeds in the
        # startup.

        # Mune's dialog is in his arbs (Obj 0D)
        mune_obj = 0xD
        pos = script.get_function_start(mune_obj, FID.ARBITRARY_1)

        for _ in range(2):
            pos, __ = script.find_command([0xBB], pos)
            script.data[pos:pos+2] = \
                EC.generic_command(0xAD, 0x08).to_bytearray()

        # Most of the scene is done back in Obj 0C
        pos = script.get_function_start(0xC, FID.STARTUP)
        pos, _ = script.find_command([0xBB], pos)  # What is it Mune
        script.data[pos:pos+2] = EC.generic_command(0xAD, 0x08).to_bytearray()
        pos, _ = script.find_command([0xBB], pos + 2)  # Not again
        script.data[pos:pos+2] = EC.generic_command(0xAD, 0x08).to_bytearray()
        pos, _ = script.find_command([0xBB], pos + 2)

        script.delete_commands(pos, 1)
        pos += 3  # Skipping over a call obj func
        script.delete_commands(pos, 9)  # Spin and text

        pos, _ = script.find_command([0xBB], pos)
        script.data[pos:pos+2] = EC.generic_command(0xAD, 0x08).to_bytearray()

    @classmethod
    def modify_between_battle_scene(cls, script: Event):
        """Remove dialog from the scene between the split and joined fight."""

        # Control passes from the Masa kid object (0xC) to the Masa enemy
        # object (0x12) (with a detour to obj 08 for the battle)

        # Mune's dialog is in his arbs (Obj 13 for enemy version)
        pos = script.get_function_start(0x13, FID.ARBITRARY_3)
        for _ in range(3):
            pos, __ = script.find_command([0xBB], pos)
            script.data[pos:pos+2] = \
                EC.generic_command(0xAD, 0x08).to_bytearray()

        # Everything else is back to Obj 12
        pos = script.get_function_start(0x12, FID.STARTUP)
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 8)

    @classmethod
    def modify_post_battle_scene(cls, script: Event):
        """Remove dialog from the scene after the joined fight."""

        # Control passes to a new Masa kid object (0xE)
        pos = script.get_function_start(0xE, FID.STARTUP)
        del_pos = script.find_exact_command(
            EC.call_obj_function(0xF, FID.ARBITRARY_0, 4, FS.HALT),
            pos)
        del_end = script.find_exact_command(EC.remove_object(0xB), del_pos)
        script.delete_commands_range(del_pos, del_end)

        # Mune's dialog is in his new kid object (0xF)

    @classmethod
    def modify_item_collection_scene(cls, script: Event):
        """Replace 'Broken Masamune' text.  Speed up sprite movement."""

        pos = script.get_function_start(0xA, FID.TOUCH)

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0x28), pos
        )
        script.data[pos+1] = 0x10  # shorten the pause as the sparkle descends

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.ROBO), pos
        )
        end, _ = script.find_command([0xBB], pos)
        script.delete_commands_range(pos, end)

        # pos now points to the item text command

        # Change the text
        new_str_id = script.add_py_string(
            "{line break}Got 1 {item}!{line break}{itemdesc}{null}"
        )
        script.data[pos+1] = new_str_id
        script.delete_commands(pos+2, 2)  # Deleting storyline and add item

        # Delete the old add item command so that the order is always set
        # item memory, add item, display text.
        script.insert_commands(
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.BENT_SWORD, 0x7F0200, 1))
            .add(EC.add_item(ctenums.ItemID.BENT_SWORD))
            .get_bytearray(),
            pos
        )

        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0x30), pos  # Big 3s pause
        )
        script.data[pos+1] = 0x10  # shorten the pause after getting the item

        # Make that sparkle a bit faster.
        pos = script.find_exact_command(
            EC.set_move_speed(8),
            script.get_function_start(0x10, FID.ARBITRARY_0)
        )
        script.data[pos+1] = 0x20

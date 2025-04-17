"""Openworld Castle Magus Throne of Strength"""

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
# Slash is in 0xB, Slash + Sword is in 0xC

class EventMod(locationevent.LocEventMod):
    """EventMod for Castle Magus Throne of Strength"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_SLASH

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Throne of Strength for an Open World.
        - Fix exploremodes.
        - Remove some dialogue around the slash fight.
        - Change slash to go straight into the +sword fight.
        - Modify Slasher pickup to follow usual pattern
        """
        cls.modify_pre_slash_battle(script)
        cls.modify_slash_battle(script)

        pos = script.get_function_start(0xA, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

    @classmethod
    def modify_pre_slash_battle(cls, script: Event):
        """
        Modify the 5x Decedent battle before Slash.
        - Remove dialogue and frog-specific sound/anims.
        - Add an exploremode on after.
        """

        pos, cmd = script.find_command([0xD8],
                                       script.get_function_start(9, FID.ACTIVATE))
        pos += len(cmd)
        script.data[pos: pos+2] = EC.generic_command(0xAD, 0x04).to_bytearray()

        pos = script.find_exact_command(EC.play_sound(0x6E), pos)
        script.delete_commands(pos, 2)

        pos = script.find_exact_command(EC.party_follow(), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

    @classmethod
    def modify_slash_battle(cls, script: Event):
        """
        Modify the Slash battle.
        - Replace Slash with the Sword version.
        - Remove the first part of the slash fight.
        - Inline The Slash Sword functions into the script.
        - Remove dialogue of course.
        """
        pos, _ = script.find_command([0x83],
                                     script.get_object_start(0xB))
        script.data[pos+1] = ctenums.EnemyID.SLASH_SWORD | 0x80

        find_cmd = EC.generic_command(0x75, 0xC//2)
        pos = script.find_exact_command(
            find_cmd,
            script.get_function_start(0xB, FID.ACTIVATE)
        ) + len(find_cmd)

        del_end, _ = script.find_command([0xD9], pos)  # move party
        script.delete_commands_range(pos, del_end)

        pos, _ = script.find_command([0xD8], pos)  # Battle
        script.delete_commands(pos, 2)

        for _ in range(2):
            pos, __ = script.find_command([0xBB],  pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 0x4).to_bytearray()
            pos += 2

        # Delete the object switcheroo and a textbox.
        pos = script.find_exact_command(
            EC.set_object_drawing_status(0xC, True), pos)
        script.delete_commands(pos, 3)

        slash_fns: dict[FID, EF] = {
            FID.ARBITRARY_0: script.get_function(0xC, FID.ARBITRARY_0),
            FID.ARBITRARY_1: script.get_function(0xC, FID.ARBITRARY_1),
            FID.ARBITRARY_2: script.get_function(0xC, FID.ARBITRARY_2)
        }

        for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2):
            pos = script.find_exact_command(
                EC.call_obj_function(0xC, fid, 4, FS.HALT), pos
            )
            script.delete_commands(pos, 1)
            slash_fns[fid].delete_at_index(-1)  # Remove return
            script.insert_commands(slash_fns[fid].get_bytearray(), pos)

        pos = script.find_exact_command(
            EC.set_object_drawing_status(0xC, False), pos
        )
        script.delete_commands(pos, 1)
        script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)

        pos = script.find_exact_command(EC.party_follow(), pos) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # This is the animation command for Slash at the start.
        # In vanilla, he's spinning around when he makes his entry, but sword Slash
        # doesn't have this animation!  So we change it to a less cool one.
        pos = script.get_function_start(0xB, FID.ARBITRARY_0)
        script.data[pos+1] = 1

        # Remove the enemy load from the now-unused slash object.
        script.set_function(0xC, FID.STARTUP,
                            EF().add(EC.return_cmd()).add(EC.end_cmd()))



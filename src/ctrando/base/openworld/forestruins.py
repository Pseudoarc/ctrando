"""Change Forest Ruins for open world."""
from typing import Optional

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.common.memory import Flags
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Forest Ruins"""
    loc_id = ctenums.LocID.FOREST_RUINS

    @classmethod
    def modify(cls, script: Event):
        """
        Update Forest Ruins
        - Replace storyline check with flag check
        - Shorten pyramid cutscene
        - Split the pyramid chests
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xAB))
        owu.modify_if_not_charge(script, pos, 0x7F0220)

        cls.shorten_pyramid_cutscene(script)
        cls.split_pyramid_chests(script)

    @classmethod
    def shorten_pyramid_cutscene(cls, script: Event):
        """
        Remove PC dialog and Nu dialog after the pyramid opens.
        """

        pos: Optional[int]

        # The pyramid cutscene is in Crono (Obj01, Arb0)
        pos, end = script.get_function_bounds(1, FID.ARBITRARY_0)

        pos = script.find_exact_command(
            EC.call_pc_function(1, FID.ARBITRARY_2, 6, FS.HALT), pos, end
        )
        script.delete_commands(pos)

        # Fix the partyfollow for single member parties
        pos = script.find_exact_command(EC.party_follow(), pos, end) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos = script.get_function_start(0x15, FID.ACTIVATE)
        while True:
            pos, _ = script.find_command_opt([0xBB],  # Auto text
                                             pos)
            if pos is None:
                break
            script.delete_commands(pos, 1)

    @classmethod
    def split_pyramid_chests(cls, script: Event):
        """Make the pyramid chests separate?"""

        # TODO: Decide whether to split the chests or to give a Nu hint
        left_chest_obj = 0x13
        right_chest_obj = 0x14

        # Don't hide the right chest when the left is obtained
        start, end = script.get_function_bounds(left_chest_obj, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.set_object_drawing_status(right_chest_obj, False), start, end
        )
        script.delete_commands(pos, 1)

        # Change the hide trigger to be the (new) right chest flag
        pos = script.get_object_start(right_chest_obj)
        pos = script.find_exact_command(
            EC.if_flag(Flags.PYRAMID_LEFT_CHEST), pos
        )
        script.replace_jump_cmd(pos, EC.if_flag(Flags.PYRAMID_RIGHT_CHEST))

        # Don't hide the left chest when the right is obtained
        pos = script.find_exact_command(
            EC.set_object_drawing_status(left_chest_obj, False), pos
        )
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.set_flag(Flags.PYRAMID_LEFT_CHEST), pos
        )
        script.delete_commands(pos, 1)
        script.insert_commands(
            EC.set_flag(Flags.PYRAMID_RIGHT_CHEST).to_bytearray(), pos
        )

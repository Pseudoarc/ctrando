"""Openworld Heckran Cave Passageways"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Heckran Cave Passageways"""
    loc_id = ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Heckran Cave Passageways for an Open World.
        - Remove storyline setting after Heckran and replace with a flag.
        - Remove post-Heckran dialogue.
        - Update sealed chest.
        - Update Epoch location with vortex use.
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x51))
        script.replace_jump_cmd(pos, EC.if_not_flag(memory.Flags.HECKRAN_DEFEATED))

        # Remove post-Heckran dialogue and storyline
        pos, cmd = script.find_command([0xD9], pos)
        pos += len(cmd)
        pos, _ = script.find_command([0xD9], pos)

        del_end = script.find_exact_command(
            EC.set_storyline_counter(0x51), pos
        ) + 2

        script.delete_commands_range(pos, del_end)
        script.insert_commands(
            EC.set_flag(memory.Flags.HECKRAN_DEFEATED).to_bytearray(), pos
        )
        pos = script.find_exact_command(EC.party_follow(), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos = script.get_object_start(0xD)
        script.replace_jump_cmd(pos, EC.if_not_flag(memory.Flags.HECKRAN_DEFEATED))

        # Remove Heckran's death speech and add quest counter
        start, end = script.get_function_bounds(0xD, FID.TOUCH)
        for _ in range (2):
            pos, __ = script.find_command([0xBB], pos)
            script.delete_commands(pos, 1)

        # Sealed chest.
        pos = script.get_function_start(0xC, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xA5))
        owu.modify_if_not_charge(script, pos, 0x7F0220)

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.WALL_RING), pos)
        owu.update_add_item(script, pos)

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.DASH_RING),  pos)
        owu.update_add_item(script, pos)

        # Epoch
        pos, _ = script.find_command([0xE0], script.get_function_start(3, FID.ACTIVATE))
        script.insert_commands(
            owu.get_epoch_set_block(
                ctenums.LocID.OW_PRESENT, 0x158, 0x138
            ).get_bytearray(), pos
        )
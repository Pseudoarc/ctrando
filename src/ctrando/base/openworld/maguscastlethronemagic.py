"""Openworld Castle Magus Throne of Magic"""

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

class EventMod(locationevent.LocEventMod):
    """EventMod for Castle Magus Throne of Magic"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_FLEA

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Throne of Magic for an Open World.
        - Remove dialogue before/after the fight.
        - Add exploremode on after the fight.
        - Make the magic tab a fast tab.
        """
        cls.modify_flea_scenes(script)


        start, end = script.get_function_bounds(0xD, FID.ACTIVATE)
        owu.remove_item_pause(script, start, end)

    @classmethod
    def modify_flea_scenes(cls, script: Event):
        """
        Remove dialogue and extra animations before the battle.
        """

        pos = script.find_exact_command(
            EC.play_sound(0x6E),
            script.get_object_start(0xC)
        )
        script.delete_commands(pos, 1)

        for _ in range(4):
            pos, __ = script.find_command([0xC1, 0xC2, 0xBB], pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 0x04).to_bytearray()

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE), pos
        )

        del_end = script.find_exact_command(EC.play_song(0x29), pos)
        script.delete_commands_range(pos, del_end)

        pos = script.find_exact_command(EC.end_cmd(), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
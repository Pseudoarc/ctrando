"""Openworld Castle Magus Entrance"""

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
    """EventMod for Castle Magus Entrance"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Entrance for an Open World.
        - Set the flags for visiting Flea's and Slash's room
        - Remove dialogue from the Ozzie battle
        - Fix a missing exploremode when warping into this location.
        """

        # Set room visiting flags
        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.MAGUS_CASTLE_VISITED_SLASH_ROOM))
            .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_VISITED_FLEA_ROOM))
            .get_bytearray(), pos
        )

        # Remove Ozzie battle dialogue
        pos = script.get_object_start(0xA)
        for _ in range(3):
            pos, __ = script.find_command([0xC1,0xC2], pos)
            script.data[pos:pos+2] = EC.generic_command(0xAD, 0x4).to_bytearray()

        # Insert Exploremode
        pos = script.find_exact_command(EC.party_follow(),
                                        script.get_object_start(9))
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # Give Magus shortcut
        pos = script.find_exact_command(
            EC.call_pc_function(0, FID.ARBITRARY_3, 4, FS.SYNC),
            script.get_function_start(0xA, FID.STARTUP)
        )

        new_block = (
            EF()
            .add_if(
                EC.if_pc_active(ctenums.CharID.MAGUS),
                EF().add(EC.decision_box(
                    script.add_py_string(
                        "{magus}: I know a shortcut. Where to?{line break}"
                        "   Hall of Aggression (normal){line break}"
                        "   Grand Stairway{null}"
                    ), 1, 2
                ))
            )
        )

        script.insert_commands(new_block.get_bytearray(), pos)
        flag_cmd = EC.set_flag(memory.Flags.USING_SAVE_POINT_WARP)

        pos = script.find_exact_command(flag_cmd, pos + len(new_block)) + len(flag_cmd)
        change_block = (
            EF().add_if(
                EC.if_result_equals(2),
                EF()
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_LEFT_GUILLOTINES))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_WELCOME_GUILLOTINES))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_FASTER_GUILLOTINES))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_LEFT_PITS))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_LEFT_HALL_AGGRESSION))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_LEFT_HALL_APPREHENSION))
                .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_DEFEATED))
                .add(EC.change_location(
                    ctenums.LocID.MAGUS_CASTLE_GRAND_STAIRWAY,
                    0x3D, 0x9, Facing.LEFT, 2, False
                ))
            )
        )
        script.insert_commands(change_block.get_bytearray(), pos)


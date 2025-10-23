"""Openworld Castle Magus Grand Stairway"""

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
    """EventMod for Castle Magus Grand Stairway"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_GRAND_STAIRWAY

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Grand Stairway for an Open World.
        - Fix exploremode after warping in
        - Give Ayla and Magus warp-in fading.
        - Add Magus shortcut
        """

        # set exploremode on warp in
        pos = script.find_exact_command(
            EC.party_follow(), script.get_object_start(8)) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # add fade-in to startup
        for char_id in (ctenums.CharID.MAGUS, ctenums.CharID.AYLA):
            obj_id = char_id+1
            pos = script.find_exact_command(
                EC.return_cmd(), script.get_object_start(obj_id))
            script.insert_commands(
                EF()
                .add_if(
                    EC.if_flag(memory.Flags.USING_SAVE_POINT_WARP),
                    EF().add(get_command(bytes.fromhex("88401FFF01"))),
                )
                .get_bytearray(),
                pos,
            )

        # Give Magus shortcut
        pos = script.find_exact_command(
            EC.call_pc_function(0, FID.ARBITRARY_0, 4, FS.SYNC),
            script.get_function_start(0x8, FID.STARTUP)
        )

        new_block = (
            EF()
            .add_if(
                EC.if_pc_recruited(ctenums.CharID.MAGUS),
                EF().add(EC.decision_box(
                    script.add_py_string(
                        "{magus} knows a shortcut. Where to?{line break}"
                        "   Throne of Defense (normal){line break}"
                        "   Castle Entrance{null}"
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
                .add(EC.change_location(
                    ctenums.LocID.MAGUS_CASTLE_ENTRANCE,
                    0xB, 0xA, Facing.DOWN, 0, False
                ))
            )
        )
        script.insert_commands(change_block.get_bytearray(), pos)

        func = script.get_function(8, FID.STARTUP)
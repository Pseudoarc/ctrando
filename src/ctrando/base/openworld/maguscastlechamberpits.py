"""Openworld Castle Magus Chamber of Pits"""

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
    """EventMod for Castle Magus Chamber of Pits"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_PITS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Chamber of Pits for an Open World.
        - Fix exploremode on entry from the teleporter and after Ozzie.
        - Give Magus and Ayla animations for falling.
        - Fix startups for Ayla and Magus so that they can fade in if teleporting in.
        """

        pos = script.find_exact_command(EC.party_follow(),
                                        script.get_object_start(8))
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos = script.find_exact_command(
            EC.party_follow(), script.get_object_start(9)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        for char_id in (ctenums.CharID.AYLA, ctenums.CharID.MAGUS):
            obj_id = char_id + 1
            for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2,
                        FID.ARBITRARY_3):
                script.link_function(obj_id, fid, 1, fid)

            pos = script.find_exact_command(
                EC.return_cmd(), script.get_object_start(obj_id)
            )
            script.insert_commands(
                EF().add_if(
                    EC.if_flag(memory.Flags.USING_SAVE_POINT_WARP),
                    EF().add(get_command(bytes.fromhex('88401FFF01')))
                ).get_bytearray(), pos
            )


"""Openworld Castle Magus Dungeon"""

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
    """EventMod for Castle Magus Dungeon"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_DUNGEON

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Dungeon for an Open World.
        - Fix exploremode after falling a second time
        - Make the magic tab a fast tab.
        """

        # Exploremode if falling a second time.
        pos = script.find_exact_command(
            EC.end_cmd(),
            script.get_object_start(0x10)
        )
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # Fast tab
        pos, end = script.get_function_bounds(8, FID.ACTIVATE)
        owu.remove_item_pause(script, pos, end)

        # Link Ayla and Magus to Crono's functions.
        for char_id in (ctenums.CharID.AYLA, ctenums.CharID.MAGUS):
            obj_id = char_id + 1
            for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2,
                        FID.ARBITRARY_3):
                script.link_function(obj_id, fid, 1, fid)
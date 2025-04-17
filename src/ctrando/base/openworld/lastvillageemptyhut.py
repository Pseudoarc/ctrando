"""Openworld Last Village Empty Hut"""

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
    """EventMod for Last Village Empty Hut"""
    loc_id = ctenums.LocID.LAST_VILLAGE_EMPTY_HUT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Last Village Empty Hut for an Open World.
        - Add a portal to return to pre-fall Dark Ages
        """
        change_loc_cmd = EC.change_location(
            ctenums.LocID.ALGETTY_ENTRANCE, 0x36, 0x2F,
                                             Facing.DOWN,0, False
        )

        portal_screen_x, portal_screen_y = 0x97, 0x48
        portal_map_x, portal_map_y = 0x198, 0x170
        anim_fid, return_fid = FID.ARBITRARY_2, FID.ARBITRARY_3
        pc_obj_start_id = 1

        closed_portal_id = owu.insert_portal_complete(
            script,
            portal_screen_x, portal_screen_y,
            portal_map_x, portal_map_y,
            anim_fid, return_fid, pc_obj_start_id, change_loc_cmd,
            memory.Flags.HAS_ALGETTY_PORTAL
        )

        # pos = script.get_function_start(closed_portal_id, FID.STARTUP)
        # script.insert_commands(
        #     EF()
        #     .add_if(
        #         EC.if_not_flag(memory.Flags.ZEAL_HAS_FALLEN),
        #         EF().add(EC.return_cmd()).add(EC.end_cmd()),
        #     )
        #     .get_bytearray(),
        #     pos,
        # )
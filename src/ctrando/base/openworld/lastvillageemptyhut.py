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

        pos = script.get_object_start(0)
        temp_addr, count_addr = 0x7F0230, 0x7F0232
        count_fn = owu.get_count_pcs_func(temp_addr, count_addr)
        script.insert_commands(count_fn.get_bytearray(), pos)

        # Fix exploremode/partyfollow
        pos = script.get_function_start(0xB, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0214, OP.LESS_THAN, 3),
            pos
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_mem(0x7F0214, OP.LESS_THAN, count_addr)
        )
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0xB, FID.ACTIVATE)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
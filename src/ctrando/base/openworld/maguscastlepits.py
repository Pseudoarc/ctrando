"""Openworld Castle Magus Pits"""

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
    """EventMod for Castle Magus Pits"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_PITS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Pits for an Open World.
        - Add a sparkle to revisit pits area.
        """

        obj_id = script.append_empty_object()
        script.set_function(
            obj_id, FID.STARTUP,
            EF()
            .add(EC.load_npc(ctenums.NpcID.SAVE_POINT))
            .add(EC.set_object_coordinates_tile(0x3C, 0x10))
            .add(EC.generic_command(0x8E, 0x3B))  # Sprite priority
            .add(EC.set_solidity_properties(False, False))
            .add_if(
                EC.if_not_flag(memory.Flags.MAGUS_CASTLE_OZZIE_DEFEATED),
                EF().add(EC.set_own_drawing_status(False))
            )
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        # print(EC.change_location(
        #         ctenums.LocID.MAGUS_CASTLE_DUNGEON, 0xF, 0x10,
        #         facing=Facing.DOWN,
        #         unk=0, wait_vblank=False
        #     )
        # )
        loc_cmd = get_command(bytes.fromhex("E0D7030F10"))
        # input()

        script.set_function(obj_id, FID.ACTIVATE, EF())
        script.set_function(
            obj_id, FID.TOUCH,
            EF()
            .add(EC.set_explore_mode(False))
            .add(EC.play_sound(0xB))
            .add(EC.call_pc_function(2, FID.ARBITRARY_3, 2, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_3, 2, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 2, FS.HALT))
            # .add(EC.darken(0xC0))
            .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_FALLING_IN_PIT))
            .add(EC.assign_val_to_mem(1, 0x7F00D0, 1))
            # .add(EC.pause(1.25))
            .add(loc_cmd)
            .add(EC.return_cmd())
            # .add(EC.change_location(
            #     ctenums.LocID.MAGUS_CASTLE_DUNGEON, 0xF, 0x10,
            #     facing=Facing.DOWN,
            #     unk=0, wait_vblank=True
            # ))
        )
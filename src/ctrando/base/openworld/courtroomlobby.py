"""Openworld Courtroom Lobby"""

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
    """EventMod for Courtroom Lobby"""
    loc_id = ctenums.LocID.COURTROOM_LOBBY

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Courtroom Lobby for an Open World.
        - Now that the Yakra fight is immediately triggered, set some weird memory
          so that the screen wipe works.
        """

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE),
            script.get_function_start(8, FID.ACTIVATE)
        )
        script.wrap_jump_cmd(
            pos,
            EC.if_has_item(ctenums.ItemID.PRISMSHARD)
        )

        pos = script.find_exact_command(
            EC.call_obj_function(2, FID.ARBITRARY_1, 3, FS.HALT),  # Marle knows a way in
            pos
        )

        script.insert_commands(
            EF().add(EC.assign_val_to_mem(1, memory.Memory.KEEPSONG,1))
            .add(get_command(bytes.fromhex('EC880101')))  # Song State
            .add(EC.play_song(0x23))
            .add(EC.assign_val_to_mem(0, 0x7E0350, 1))
            .get_bytearray(), pos
        )



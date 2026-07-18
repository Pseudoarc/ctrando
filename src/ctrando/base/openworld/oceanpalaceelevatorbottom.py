"""Openworld Ocean Palace Elevator Bottom"""

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
    """EventMod for Ocean Palace Elevator Top"""

    loc_id = ctenums.LocID.OCEAN_PALACE_WESTERN_ACCESS_LIFT
    room_status_addr = 0x7F0214

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Elevator Bottom.
        - Only play sound effect if coming from the battles
        """

        pos = script.find_exact_command(
            EC.play_sound(0x6D)
        )

        # If we came from top, cancel the keepsong that was keeping the elevator sound
        # Otherwise, play the elevator sound that is not played on the battl map
        new_block = (
            EF()
            .add_if_else(
                EC.if_mem_op_value(0x7F0212, OP.EQUALS,
                                    ctenums.LocID.OCEAN_PALACE_EASTERN_ACCESS_LIFT, 2),
                EF().add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1)),
                EF().add(EC.play_sound(0x6D))
            )
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 1)

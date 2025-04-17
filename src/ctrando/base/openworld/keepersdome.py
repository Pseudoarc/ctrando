"""Openworld Keeper's Dome"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Keeper's Dome"""
    loc_id = ctenums.LocID.KEEPERS_DOME
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Keeper's Dome Event.
        - Have the sealed door be open if coming from the corridor.
        - Put the scene in the later (after charge) storyline state
        - Replace the storyline check on the sealed door with a flag check
        """
        pos = script.get_object_start(0)
        script.insert_commands(
            EF()
            .add(EC.set_flag(memory.Flags.NU_ENTERED_KEEPERS_HANGAR))
            .add(EC.assign_mem_to_mem(memory.Memory.PREVIOUS_LOCATION_LO,
                                          0x7F0220, 2))
            .add_if(
                EC.if_mem_op_value(0x7F0220, OP.EQUALS,
                                   ctenums.LocID.KEEPERS_DOME_CORRIDOR, 2),
                EF().add(EC.assign_val_to_mem(1, 0x7F0210, 1))
            ).get_bytearray(), pos
        )


        pos = script.get_function_start(0, FID.ACTIVATE)
        script.delete_jump_block(pos)

        pos = script.get_function_start(0xD, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xAB), pos)
        owu.modify_if_not_charge(script, pos, 0x7F0222)


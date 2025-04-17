"""Openworld Keeper's Dome Hangar"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Keeper's Dome Hangar"""
    loc_id = ctenums.LocID.KEEPERS_DOME_HANGAR
    temp_epoch_status = 0x7F0220
    temp_addr = 0x7F0222
    num_pcs_addr = 0x7F0224

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Keeper's Dome Hangar Event.
        - Remove the Nu intro scene when the team goes to the back of the Epoch
        - Remove storyline setings
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.NU_ENTERED_KEEPERS_HANGAR))
            .add(EC.set_flag(memory.Flags.VIEWED_NAME_EPOCH_SCENE))
            .add(EC.set_flag(memory.Flags.VIEWED_EPOCH_FIRST_FLIGHT_SCENE))
            .append(owu.get_count_pcs_func(cls.temp_addr, cls.num_pcs_addr))
            .get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xAE),
            script.get_function_start(0xF, FID.ACTIVATE)
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT),
            script.get_function_start(0x10, FID.ARBITRARY_1)
        )
        end = script.find_exact_command(
            EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0x1F7, 2))
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EF().add(EC.assign_mem_to_mem(memory.Memory.EPOCH_STATUS, 0x7F0220, 1))
            .add(EC.set_reset_bits(0x7F0220, 0xD0, True))
            .add(EC.set_reset_bits(0x7F0220, 0xFC, False))
            .add(EC.add_mem(cls.num_pcs_addr, cls.temp_epoch_status))
            .add(EC.assign_mem_to_mem(0x7F0220, memory.Memory.EPOCH_STATUS, 1))
            .get_bytearray(), pos
        )
"""Openworld End of Time Epoch Hangar"""
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
    """EventMod for End of Time Epoch Hangar"""

    loc_id = ctenums.LocID.END_OF_TIME_EPOCH

    # The vanilla script already records
    pc1_addr = 0x7F020E
    pc2_addr = 0x7F0210
    pc3_addr = 0x7F0212

    @classmethod
    def modify(cls, script: Event):
        """
        Modify End of Time Epoch Hangar for an Open World.
        - Correctly set Number of PCs upon boarding.
        """

        temp_epoch_status_addr = 0x7F021C

        cmd = EC.assign_mem_to_mem(memory.Memory.EPOCH_STATUS, temp_epoch_status_addr, 1)
        pos = script.find_exact_command(
            cmd, script.get_function_start(9, FID.STARTUP)
        )

        pos += len (cmd)
        script.delete_commands(pos, 1)  # set bits

        func = (
            EF()
            .add(EC.set_reset_bits(temp_epoch_status_addr, 0x03, False))
            .add(EC.set_reset_bits(temp_epoch_status_addr, 0x51, True))
            .add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.LESS_THAN, 8),
                EF().add(EC.increment_mem(temp_epoch_status_addr, 1))
            )
            .add_if(
                EC.if_mem_op_value(cls.pc3_addr, OP.LESS_THAN, 8),
                EF().add(EC.increment_mem(temp_epoch_status_addr, 1))
            )
        )
        script.insert_commands(func.get_bytearray(), pos)

        print(script.get_function(9, FID.STARTUP))
        input()



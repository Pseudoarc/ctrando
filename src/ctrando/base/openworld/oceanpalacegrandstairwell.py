"""Openworld Ocean Grand Stairwell"""

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
    """EventMod for Ocean Grand Stairwell"""
    loc_id = ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL
    temp_hp_addr = 0x7F021C

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace B3 Landing Event.
        - Add Magus to the location
        - Remove Masa
        """

        # Copying Crono because the rest have linked functions which will break.
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 7)

        # Remove Masa
        pos = script.get_object_start(0x22)
        script.delete_jump_block(pos)

        cls.modify_pc_arbs(script)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give everyone a function for losing HP to the fireballs.
        Change the call from crono's object to first PC.
        Call AFTER Magus is added.
        """

        for obj_id in range(2, 8):
            pc_id = ctenums.CharID(obj_id-1)
            hp_lo_byte = 0x7E2603 + 0x50*pc_id

            # HP subtracting function
            func = (
                EF().add(EC.play_animation(9))
                .add(EC.assign_mem_to_mem(hp_lo_byte, cls.temp_hp_addr, 2))
                .add_if_else(
                    EC.if_mem_op_value(cls.temp_hp_addr, OP.GREATER_THAN, 0xA,
                                       num_bytes=2),
                    EF().add(EC.sub(cls.temp_hp_addr, 0xA, 2)),
                    EF().add(EC.assign_val_to_mem(1, cls.temp_hp_addr, 2))
                ).add(EC.assign_mem_to_mem(cls.temp_hp_addr, hp_lo_byte, 2))
                .add(EC.pause(2))
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_1, func)

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_1, 1, FS.HALT),
            script.get_function_start(0xB, FID.ARBITRARY_1)
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.HALT)
        script.data[pos: pos+len(repl_cmd)] = repl_cmd.to_bytearray()
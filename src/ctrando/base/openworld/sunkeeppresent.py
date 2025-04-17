"""Openworld Sun Keep (1000AD)"""

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
    """EventMod for Sun Keep (1000AD)"""
    loc_id = ctenums.LocID.SUN_KEEP_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Keep (1000AD) for an Open World.
        - Change draw conditions for Moon Stone to use rando flags.
        - Remove all of the quest where the moonstone goes missing.
        """

        moonstone_obj = 8
        new_hide_condition = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.MOONSTONE_PLACED_PREHISTORY),
                EF().add(EC.remove_object(moonstone_obj))
            )
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F013A, OP.LESS_THAN, 0x20),
            script.get_function_start(moonstone_obj, FID.STARTUP)
        )

        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        script.insert_commands(
            new_hide_condition.get_bytearray(), pos
        )

        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        end, _ = script.find_command([9], pos)
        script.delete_commands_range(pos, end)

        blank_obj = 9
        script.set_function(
            blank_obj, FID.STARTUP,
            EF().add(EC.remove_object(blank_obj))
            .add(EC.return_cmd()).add(EC.end_cmd())
        )
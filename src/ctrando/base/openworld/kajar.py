"""Openworld Kajar"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Kajar"""
    loc_id = ctenums.LocID.KAJAR

    @classmethod
    def modify(cls, script: Event):
        """
        - Hide Magus during the cutscene
        - Modify Nu shop condition from storyline to charged pendant
        """

        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_function_start(7, FID.STARTUP)
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(0x7F021E, OP.GREATER_THAN, 0),
                EF().add(EC.set_own_drawing_status(False))
            ).get_bytearray(), pos
        )

        # Nu shop:
        #  - Give the bonus shop when you have a charged pendant.
        #  - Don't have the "Is this Schala's pendant?" prompt

        pos = script.get_function_start(9, FID.ARBITRARY_0)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xA5))

        owu.modify_if_not_charge(script, pos, 0x7F0224)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CAN_ACCESS_KAJAR_NU_SPECIAL_SHOP_UNUSED)
        )
        script.delete_commands(pos, 1)

        pos, _ = script.find_command([0xC0], pos)
        end = script.find_exact_command(EC.generic_command(0xAD, 4), pos)
        script.delete_commands_range(pos, end)

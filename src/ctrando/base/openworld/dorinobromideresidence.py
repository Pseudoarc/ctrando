"""Openworld Dorino Bromide Residence Face"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Dorino Bromide Residence Face"""
    loc_id = ctenums.LocID.DORINO_PERVERT_RESIDENCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Dorino Bromide Residence Face Event.
        - Update Magic Tab
        - Change tab to be obtained just by having bromide
        """


        pos = script.get_function_start(0xC, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0214, OP.GREATER_THAN, 0),
            pos
        )
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.OBTAINED_NAGAETTE_BROMIDE)
        )
        owu.update_add_item(script, pos)


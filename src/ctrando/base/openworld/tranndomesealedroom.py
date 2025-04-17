"""Openworld Trann Dome Sealed Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Trann Dome Sealed Room"""
    loc_id = ctenums.LocID.TRANN_DOME_SEALED_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Trann Dome Sealed Room Event.
        - Remove pause from floor item.
        """
        pos = script.get_function_start(8, FID.ACTIVATE)
        pf_pos = script.find_exact_command(EC.party_follow(), pos)
        script.delete_commands(pf_pos, 1)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pf_pos)

        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

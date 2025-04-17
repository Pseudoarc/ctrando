"""Openworld Denadoro Mts West Face"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Denadoro Mts West Face"""
    loc_id = ctenums.LocID.DENADORO_WEST_FACE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Denadoro Mts West Face Event.
        - Update Speed Tab pickup.
        """

        pos = script.get_function_start(0x9, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

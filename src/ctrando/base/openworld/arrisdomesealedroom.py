"""Openworld Arris Dome Sealed Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Sealed Room"""
    loc_id = ctenums.LocID.ARRIS_DOME_SEALED_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Sealed Room Event.
        - Fix the floor treasure.
        """
        pos = script.get_function_start(8, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

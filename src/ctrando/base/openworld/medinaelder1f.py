"""Openworld Medina Elder 1F"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID

from ctrando.base import openworldutils as owu


class EventMod(locationevent.LocEventMod):
    """EventMod for Medina Elder 1F"""
    loc_id = ctenums.LocID.MEDINA_ELDER_1F

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Medina Elder for an Open World.
        - Update tab treasure text
        """

        pos = script.get_function_start(0xC, FID.ACTIVATE)
        owu.update_add_item(script, pos)
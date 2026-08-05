"""Openworld Medina Elder 2F"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID

from ctrando.base import openworldutils as owu


class EventMod(locationevent.LocEventMod):
    """EventMod for Medina Elder 2F"""
    loc_id = ctenums.LocID.MEDINA_ELDER_2F

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Medina Elder 2F for an Open World.
        - Update tab treasure text
        """

        pos = script.get_function_start(0x9, FID.ACTIVATE)
        owu.update_add_item(script, pos)
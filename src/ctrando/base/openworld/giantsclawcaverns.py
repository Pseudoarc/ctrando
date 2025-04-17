"""Openworld Giant's Claw Lair Caverns"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID

from ctrando.base import openworldutils as owu


class EventMod(locationevent.LocEventMod):
    """EventMod for Giant's Claw Lair Caverns"""
    loc_id = ctenums.LocID.GIANTS_CLAW_CAVERNS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Giant's Claw Lair Caverns for an Open World.
        - Update tab treasure spot on ground.
        """

        owu.remove_item_pause(
            script,
            script.get_function_start(0xD, FID.ACTIVATE)
        )
"""Openworld Giant's Claw Lair Caverns"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Giant's Claw Lair Caverns"""
    loc_id = ctenums.LocID.ANCIENT_TYRANO_LAIR_TRAPS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Giant's Claw Lair Caverns for an Open World.
        - Update tab treasure spot on ground.
        """

        owu.remove_item_pause(
            script,
            script.get_function_start(0x15, FID.ACTIVATE)
        )

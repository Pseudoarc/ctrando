"""Openworld Porre Inn"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Porre Inn"""
    loc_id = ctenums.LocID.PORRE_INN_600

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Inn (600) for an Open World.
        - Exploremode after partyfollows
        """
        owu.add_exploremode_to_partyfollows(script)

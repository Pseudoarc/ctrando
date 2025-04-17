"""Openworld Dorino Inn"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Dorino Inn"""
    loc_id = ctenums.LocID.DORINO_INN

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Inn (600) for an Open World.
        - Exploremode after partyfollows
        """
        owu.add_exploremode_to_partyfollows(script)

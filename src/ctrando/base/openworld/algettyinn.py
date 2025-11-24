"""Openworld Algetty Inn"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Algetty Inn"""
    loc_id = ctenums.LocID.ALGETTY_INN

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Algetty Inn Event.
        - Add partyfollows
        """

        owu.add_exploremode_to_partyfollows(script)

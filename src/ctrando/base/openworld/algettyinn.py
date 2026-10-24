"""Openworld Algetty Inn"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Algetty Inn"""
    loc_id = ctenums.LocID.ALGETTY_INN

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Algetty Inn Event.
        - Add partyfollows
        - Give Magus arbs to sleep properly
        """

        owu.add_exploremode_to_partyfollows(script)

        for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2):
            script.link_function(7, fid, 1, fid)

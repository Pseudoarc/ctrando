"""Openworld Choras Carpenter's Residence (1000)"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Choras Carpenter's Residence (1000)"""
    loc_id = ctenums.LocID.CHORAS_CARPENTER_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Carpenter's Residence (1000) for an Open World.
        - Add a missing exploremode on command.
        """

        owu.add_exploremode_to_partyfollows(script)

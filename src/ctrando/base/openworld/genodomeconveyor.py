"""Openworld Geno Dome Main Conveyor"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Geno Dome Main Conveyor"""
    loc_id = ctenums.LocID.GENO_DOME_CONVEYOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Geno Dome Main Conveyor for an Open World.
        - Add movement functions for Robo for when he's not first.
        """

        script.link_function(4, FID.ARBITRARY_0, 1, FID.ARBITRARY_0)
        script.link_function(4, FID.ARBITRARY_1, 1, FID.ARBITRARY_1)

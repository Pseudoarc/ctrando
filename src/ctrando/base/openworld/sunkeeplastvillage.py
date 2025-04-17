"""Openworld Sun Keep (Last Village)"""

from ctrando.common import ctenums
from ctrando.base.openworld import sunkeep600
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
class EventMod(locationevent.LocEventMod):
    """EventMod for Sun Keep (Last Village)"""

    loc_id = ctenums.LocID.SUN_KEEP_LAST_VILLAGE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Keep (Last Village) for an Open World.
        - Change draw conditions for Moon Stone to use rando flags.
        """
        sunkeep600.EventMod.modify_moonstone_draw_conditions(script)

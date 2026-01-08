"""Openworld Northern Ruins Landing"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Northern Ruins Vestibule"""

    loc_id = ctenums.LocID.NORTHERN_RUINS_LANDING

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Vestibule for an Open World.
        - Update magic tab pickup
        """
        owu.update_add_item(
            script, script.get_function_start(0x8, FID.ACTIVATE))
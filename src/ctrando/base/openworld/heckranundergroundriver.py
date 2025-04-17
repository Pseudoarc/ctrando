"""Change Underground River for open world."""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC


class EventMod(locationevent.LocEventMod):
    loc_id = ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Underground River of Hecrkan's Cave.
        - Partyfollow does not turn exploremode on if there is only one PC.
          This needs to be forced on after vortexing in.
        """

        owu.add_exploremode_to_partyfollows(script)

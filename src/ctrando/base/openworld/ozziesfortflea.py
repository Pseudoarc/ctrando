"""Openworld Ozzie's Fort Throne of Impertinence"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Ozzie's Fort Throne of Impertinence"""

    loc_id = ctenums.LocID.OZZIES_FORT_FLEA_PLUS

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ozzie's Fort Throne of Impertinence for an Open World.
        - exploremode after partyfollow
        """

        owu.add_exploremode_to_partyfollows(script)


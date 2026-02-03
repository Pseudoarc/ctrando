"""Openworld Reptite Lair 2F"""

from ctrando.base import openworldutils as owu
from ctrando.base.openworld import reptiteburrowb1
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair 2F"""
    loc_id = ctenums.LocID.REPTITE_LAIR_2F

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair 2F Event.
         - Add exploremode on after partyfollows.
        """

        pos = script.find_exact_command(EC.party_follow()) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

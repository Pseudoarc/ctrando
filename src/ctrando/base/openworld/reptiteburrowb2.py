"""Openworld Reptite Lair Weevil Burrows B2"""

from ctrando.base import openworldutils as owu
from ctrando.base.openworld import reptiteburrowb1
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair Weevil Burrows B2"""
    loc_id = ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B2

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair Weevil Burrows B2 Event.
         - Add exploremode on after partyfollows.
        """

        reptiteburrowb1.EventMod.fix_tunnel_entry(script)

        pos = script.find_exact_command(EC.end_cmd())
        script.insert_commands(
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )
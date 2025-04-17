"""Openworld Reptite Lair 1F"""

from ctrando.base import openworldutils as owu
from ctrando.base.openworld import reptiteburrowb1
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair 1F"""
    loc_id = ctenums.LocID.REPTITE_LAIR_1F

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair 1F Event.
         - Add exploremode on after partyfollows.
        """

        reptiteburrowb1.EventMod.fix_tunnel_entry(script, fall_fid=FID.ARBITRARY_1)

        pos = script.find_exact_command(EC.party_follow())
        script.insert_commands(
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )
        pos += 3  # Len inserted
        script.delete_commands(pos, 1)

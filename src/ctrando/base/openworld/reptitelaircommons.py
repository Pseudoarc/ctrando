"""Openworld Reptite Lair Commons"""

from ctrando.base import openworldutils as owu
from ctrando.base.openworld import reptiteburrowb1
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair Commons"""
    loc_id = ctenums.LocID.REPTITE_LAIR_COMMONS

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair Commons Event.
         - Add exploremode on after partyfollows.
         _ Maybe: Remove reptites after Nizbel is defeated
        """

        reptiteburrowb1.EventMod.fix_tunnel_entry(script)

        pos = script.find_exact_command(EC.party_follow())
        script.insert_commands(
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )
        pos += 3  # Len inserted
        script.delete_commands(pos, 1)

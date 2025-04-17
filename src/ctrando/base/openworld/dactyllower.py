"""Openworld Dactyl Nest (Lower)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Note that there are some storyline < 0xA8 checks here that we're leaving alone
# because they have no effect.  We're never letting storyline get past 3.

class EventMod(locationevent.LocEventMod):
    """EventMod for Dactyl Nest (Lower)"""
    loc_id = ctenums.LocID.DACTYL_NEST_LOWER

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Dactyl Nest (Lower) Event.
        - Add an exploremode on after a partyfollow after a battle.
        """

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(8, FID.ARBITRARY_1)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
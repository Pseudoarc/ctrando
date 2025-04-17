"""Openworld Factory Ruins Crane Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Factory Ruins Crane Room"""
    loc_id = ctenums.LocID.FACTORY_RUINS_CRANE_ROOM
    pc3_addr = 0x7F0220
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Factory Ruins Crane Room Event.
        - Add an explore mode on command after the crane gauntlet
        """

        # Lucky it's the very first partyfollow
        pos = script.find_exact_command(EC.party_follow()) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

"""Openworld Skyway Enhasa South (0x151)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Skyway Enhasa South"""
    loc_id = ctenums.LocID.SKYWAY_ENHASA_S

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Skyway Enhasa South Event.
        - Aad an exploremode on command after warping in
        """

        pos = script.find_exact_command(EC.party_follow())
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
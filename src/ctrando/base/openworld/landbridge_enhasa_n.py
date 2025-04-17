"""Openworld Land Bridge Enhasa North (0x160)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Land Bridge Enhasa North"""
    loc_id = ctenums.LocID.LAND_BRIDGE_ENHASA_N

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Land Bridge Enhasa North Event.
        - Aad an exploremode on command
        """
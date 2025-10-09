"""Openworld Castle Magus Exterior"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Slash is in 0xB, Slash + Sword is in 0xC

class EventMod(locationevent.LocEventMod):
    """EventMod for Castle Magus Exterior"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_EXTERIOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Chamber Exterior an Open World.
        - Gfx from rom are slower than ram.  There are a few too many bats on this screen
          and it becomes sluggish.  We'll remove a handful of bats.
        """
    
        for obj_id in reversed(range(0x17, 0x1B)):
            script.remove_object(obj_id)
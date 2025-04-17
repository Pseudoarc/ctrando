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

class EventMod(locationevent.LocEventMod):
    """EventMod for Castle Magus Exterior"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_EXTERIOR

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Exterior for an Open World.
        - Remove the "This can only be... Magus's Castle" scene.  This also updates
          the storyline.
        """

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x22),
            script.get_function_start(0xD, FID.STARTUP)
        )
        del_end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, del_end)
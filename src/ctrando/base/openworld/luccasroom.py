"""Openworld Lucca's Room"""

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
    """EventMod for Lucca's Room"""
    loc_id = ctenums.LocID.LUCCAS_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Lucca's Room for an Open World.
        - Remove some party manipulation commands when accessing the portal.
        """

        pos = script.find_exact_command(
            EC.add_pc_to_active(ctenums.CharID.FROG),
            script.get_function_start(0xD, FID.ACTIVATE)
        )
        script.delete_commands(pos, 1)

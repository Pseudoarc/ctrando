"""Openworld Guardia Forest 1000"""

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
    """EventMod for Guardia Forest 1000"""

    loc_id = ctenums.LocID.GUARDIA_FOREST_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Guardia Forest 1000 for an Open World.
        - Update Sealed chest to use correct condition and fit
        """

        pos = script.get_function_start(0x29, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)

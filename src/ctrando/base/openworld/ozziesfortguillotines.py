"""Openworld Ozzie's Fort Guillotines"""

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
    """EventMod for Ozzie's Fort Guillotines"""

    loc_id = ctenums.LocID.OZZIES_FORT_GUILLOTINE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ozzie's Fort Guillotines for an Open World.
        - Update magic tab to fit normal pattern
        """

        pos = script.get_function_start(0xD, FID.ACTIVATE)
        owu.update_add_item(script, pos)
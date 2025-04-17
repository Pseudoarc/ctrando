"""Openworld Sunken Desert B1"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Sunken Desert B1"""

    loc_id = ctenums.LocID.SUNKEN_DESERT_PARASITES

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sunken Desert B1 for an Open World.
        - Update Power Tab
        - Exploremodes
        """
        owu.update_add_item(
            script,
            script.get_function_start(0xD, FID.ACTIVATE)
        )

        owu.add_exploremode_to_partyfollows(script)
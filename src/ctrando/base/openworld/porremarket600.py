"""Openworld Porre Market 600"""
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
    """EventMod for Porre Market 600"""

    loc_id = ctenums.LocID.PORRE_MARKET_600

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Market 600 for an Open World.
        - Update tab pickup
        """

        owu.update_add_item(script, script.get_function_start(0xC, FID.ACTIVATE))
        owu.remove_item_pause(script, script.get_function_start(0xC, FID.ACTIVATE))

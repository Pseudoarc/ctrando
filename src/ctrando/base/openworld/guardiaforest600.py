"""Openworld Guardia Forest 600"""
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
    """EventMod for Guardia Forest 600"""

    loc_id = ctenums.LocID.GUARDIA_FOREST_600
    temp_addr = 0x7F0230

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Guardia Forest 600 for an Open World.
        - Remove unused objects because this location is at the max.
        """

        for _ in range(6):
            script.remove_object(0x8)

        pos = script.get_function_start(0x38, FID.ACTIVATE)
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE))
        owu.update_add_item(script, script.get_function_start(0x38, FID.ACTIVATE))
        owu.update_add_item(script, script.get_function_start(0x39, FID.ACTIVATE))
        owu.remove_item_pause(script, script.get_function_start(0x39, FID.ACTIVATE))

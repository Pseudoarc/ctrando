"""Openworld Kajar Balthasar's Study"""

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
    """EventMod for Kajar Balthasar's Study"""

    loc_id = ctenums.LocID.KAJAR_ROCK_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Kajar Balthasar's Study for an Open World.
        - Update the Black Rock spot
        """
        pos = script.get_function_start(8, FID.ACTIVATE)
        owu.update_add_item(script, pos, update_text=False)

        pos, _ = script.find_command([0xBB], pos)
        pos, _ = script.find_command([0xBB], pos+2)
        script.data[pos+1] = owu.add_default_treasure_string(script)

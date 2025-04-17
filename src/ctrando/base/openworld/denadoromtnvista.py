"""Openworld Denadoro Mountain Vista"""

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
    """EventMod for Denadoro Mountain Vista"""

    loc_id = ctenums.LocID.DENADORO_MTN_VISTA

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Denadoro Mountain Vista for an Open World.
        - Update Sealed chest to use correct condition and fit
        """

        pos = script.find_exact_command(
            EC.add_item(ctenums.ItemID.MAGIC_TAB),
            script.get_function_start(0xD, FID.ACTIVATE)
        )
        owu.update_add_item(script, pos)

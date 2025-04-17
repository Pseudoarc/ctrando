"""Openworld Guardia King's Tower 1000"""

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
    """EventMod for Guardia King's Tower 1000"""

    loc_id = ctenums.LocID.GUARDIA_KINGS_TOWER_1000
    pendant_charge_check_addr = 0x7F0230

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Guardia King's Tower 1000 for an Open World.
        - Update Sealed chest to use correct condition and fit
        """

        owu.update_charge_chest_charge_loc(script, 0x8, cls.pendant_charge_check_addr)

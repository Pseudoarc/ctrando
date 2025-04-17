"""Openworld Porre Mayor 2F"""

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
    """EventMod for Porre Mayor 2F"""

    loc_id = ctenums.LocID.PORRE_MAYOR_2F
    pendant_charge_check_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Mayor 2F for an Open World.
        - Update Sealed chest to use correct condition and fit normal pattern
        """

        owu.update_charge_chest_charge_loc(script, 0x9, cls.pendant_charge_check_addr)
        owu.update_charge_chest_charge_loc(script, 0xA, cls.pendant_charge_check_addr)

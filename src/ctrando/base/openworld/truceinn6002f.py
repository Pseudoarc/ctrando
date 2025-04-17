"""Openworld Truce Inn 600 2F"""

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
    """EventMod for Truce Inn 600 2F"""

    loc_id = ctenums.LocID.TRUCE_INN_600_2F
    charge_check_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Truce Inn 600 2F for an Open World.
        - Update Sealed chest to use correct condition and fit the normal pattern.
        """

        owu.update_charge_chest_base_loc(script, 0xC, cls.charge_check_addr)

"""Openworld Enhasa"""

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
    """EventMod for Gato Exhibit"""

    loc_id = ctenums.LocID.GATO_EXHIBIT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Gato exhibit for an Open World.
        - Prevent running after battle.
        """

        # No regroup after battle.
        pos, _ = script.find_command([0xD8])
        script.data[pos + 2] |= 0x80

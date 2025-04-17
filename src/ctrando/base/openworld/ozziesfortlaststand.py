"""Openworld Ozzie's Fort Last Stand"""

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
    """EventMod for Ozzie's Fort Last Stand"""

    loc_id = ctenums.LocID.OZZIES_FORT_LAST_STAND

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ozzie's Fort Last Stand for an Open World.
        - explore mode after party follow
        """
        owu.add_exploremode_to_partyfollows(script)

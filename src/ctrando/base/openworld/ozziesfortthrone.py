"""Openworld Ozzie's Fort Throne of Incompetence"""

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
    """EventMod for Ozzie's Fort Throne of Incompetence"""

    loc_id = ctenums.LocID.OZZIES_FORT_THRONE_INCOMPETENCE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ozzie's Fort Throne of Incompetence for an Open World.
        - Fast exit after defeating Ozzie
        """

        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_function_start(8, FID.TOUCH)
        )
        script.insert_commands(
            EF()
            .add(EC.fade_screen())
            .add(EC.change_location(
                0x1F1, 0x3D * 2, 0x1A * 2, 1, 0, False
            ))
            .get_bytearray(), pos
        )
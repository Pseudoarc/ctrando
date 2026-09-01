"""Openworld Northern Ruins Vestibule"""

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
    """EventMod for Northern Ruins Vestibule"""

    loc_id = ctenums.LocID.NORTHERN_RUINS_VESTIBULE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Vestibule for an Open World.
        - Move a Reaper down a tile to avoid softlocks with throwing enemies
        """

        pos = script.find_exact_command(
            EC.move_sprite(9, 0x38, False),
            script.get_function_start(8, FID.ACTIVATE)
        )
        script.replace_command_at_pos(
            pos, EC.move_sprite(9, 0x39, False)
        )
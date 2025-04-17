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
    """EventMod for Enhasa"""

    loc_id = ctenums.LocID.ENHASA

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Enhasa for an Open World.
        - Remove Janus scene.
        """

        # Just set the flag.
        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_VIEWED_ENHASA_JANUS_SCENE)
            .to_bytearray(),
            pos
        )

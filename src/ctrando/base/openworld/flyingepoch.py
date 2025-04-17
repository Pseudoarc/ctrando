"""Openworld Flying Epoch"""
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
    """EventMod for Flying Epoch"""

    loc_id = ctenums.LocID.FLYING_EPOCH

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Flying Epoch for an Open World.
        - Skip the Lavos emerging cutscene.
        - Remove dialog except for the choice to fight or not.
        """

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999),
            script.get_function_start(0xA, FID.ARBITRARY_1)
        )
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999).to_bytearray(),
            pos
        )

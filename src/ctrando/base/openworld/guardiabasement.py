"""Openworld Guardia Basement"""

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
    """EventMod for Guardia Basement"""
    loc_id = ctenums.LocID.GUARDIA_BASEMENT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Guardia Basement for an Open World.
        - Modify the music depending on the shard quest's status
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EF()
            .add_if_else(
                # If quest is complete
                EC.if_flag(memory.Flags.KINGS_TRIAL_COMPLETE),
                EF(),  # do nothing
                EF().add_if_else(
                    # elif castle is on lockdown
                    EC.if_flag(memory.Flags.GUARDIA_THRONE_1000_BLOCKED),
                    EF(),  # Do nothing b/c playing a different song
                    # Play the ocean palace music
                    EF().add(EC.play_song(0x31))
                )
            ).get_bytearray(), pos
        )
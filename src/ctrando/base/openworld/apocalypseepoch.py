"""Openworld Apocalypse Epoch"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Apocalypse Epoch"""

    loc_id = ctenums.LocID.APOCALYPSE_EPOCH

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Apocalypse Epoch for an Open World.
        - Skip the Lavos emerging cutscene.
        - Remove dialog except for the choice to fight or not.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.HAS_SEEN_LAVOS_EMERGE_1999).to_bytearray(),
            pos
        )

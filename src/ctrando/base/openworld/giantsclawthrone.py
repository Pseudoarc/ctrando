"""Openworld Giant's Claw Lair Throneroom"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Giant's Claw Lair Throneroom"""
    loc_id = ctenums.LocID.GIANTS_CLAW_LAIR_THRONEROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Giant's Claw Lair Throneroom for an Open World.
        - Remove short scene where the party recognizes the Tyrano Lair.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.GIANTS_CLAW_VIEWED_THRONE_SCENE).to_bytearray(),
            pos
        )
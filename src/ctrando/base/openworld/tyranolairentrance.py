"""Openworld Tyrano Lair Entrance"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Entrance"""
    loc_id = ctenums.LocID.TYRANO_LAIR_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Entrance Event.  We're pretending like Kino has already
        been rescued and the door is open.
        - Set the left skull to be always open
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.TYRANO_LAIR_ENTRANCE_SKULL_OPEN).to_bytearray(),
            pos
        )
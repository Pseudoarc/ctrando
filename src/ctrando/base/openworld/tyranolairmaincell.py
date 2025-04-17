"""Openworld Tyrano Lair Main Cell"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Main Cell"""
    loc_id = ctenums.LocID.TYRANO_LAIR_MAIN_CELL

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Main Cell Event.  We're pretending like Kino has already
        been rescued and the door is open.
        - Have the cells always be empty.
        - Remove the "plot" fights before and after the cells.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.TYRANO_PRISONERS_FREED))
            .add(EC.set_flag(memory.Flags.TYRANO_MAIN_CELL_LEFT_BATTLE))
            .add(EC.set_flag(memory.Flags.TYRANO_MAIN_CELL_RIGHT_BATTLE))
            .get_bytearray(), pos
        )

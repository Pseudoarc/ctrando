"""Openworld Lab 32 West"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Lab 32 West"""
    loc_id = ctenums.LocID.LAB_32_WEST
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Lab 32 West Event.
        - Pre-set a flag to skip the Johnny entrance scene.
        - Pre-set the has raced flag so that foot access is still possible.
        - TODO: Set up a warp between lab endpoints if the race has been won
        """

        # The break command we find is within an if has bike key block.
        # We set the flag to skip the Johnny cutscene here.
        pos = script.find_exact_command(EC.break_cmd())
        script.insert_commands(
            EF().add(EC.set_flag(memory.Flags.HAS_MET_JOHNNY))
            .add(EC.set_flag(memory.Flags.HAS_ATTEMPTED_JOHNNY_RACE))
            .get_bytearray(), pos
        )

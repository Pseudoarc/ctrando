"""Openworld Choras Inn (1000)"""

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
    """EventMod for Choras Inn (1000)"""
    loc_id = ctenums.LocID.CHORAS_INN_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Inn (1000) for an Open World.
        - Remove the checks for speaking to the 600 Carpenter to get tool permission.
        """

        # There are actually two checks depending on whether you had talked to the
        # carpenter previously or not.
        pos = script.get_function_start(0xB, FID.ACTIVATE)
        for _ in range(2):
            pos = script.find_exact_command(
                EC.if_flag(memory.Flags.CHORAS_600_TALKED_TO_CARPENTER), pos
            )
            script.delete_commands(pos, 1)

        owu.add_exploremode_to_partyfollows(script)
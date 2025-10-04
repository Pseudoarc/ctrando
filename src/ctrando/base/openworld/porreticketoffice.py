"""Openworld Porre Ticket Office"""
import dataclasses

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Porre Ticket Office"""

    loc_id = ctenums.LocID.PORRE_TICKET_OFFICE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Ticket Office for an Open World.
        - Remove cutscene
        """

        for obj_id in (9, 0xA, 0xB):
            pos = script.find_exact_command(
                EC.set_flag(memory.Flags.OW_FERRY_TO_TRUCE),
                script.get_function_start(8, FID.ACTIVATE)
            )

            script.delete_commands(pos, 1)
            script.replace_command_at_pos(
                pos,
                EC.change_location(ctenums.LocID.TRUCE_TICKET_OFFICE, 0x6, 0x3C, wait_vblank=False),
            )

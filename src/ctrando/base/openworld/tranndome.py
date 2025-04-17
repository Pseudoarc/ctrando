"""Openworld Trann Dome"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Trann Dome"""
    loc_id = ctenums.LocID.TRANN_DOME
    temp_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Trann Dome Event.
        - Change charged pendant condition
        """

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xAB),
            script.get_function_start(0x11, FID.ACTIVATE)
        )

        owu.modify_if_not_charge(
            script, pos, cls.temp_addr
        )
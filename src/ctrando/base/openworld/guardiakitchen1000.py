"""Openworld Guardia Kitchen 1000"""
from dataclasses import dataclass

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Kitchen 1000"""
    loc_id = ctenums.LocID.GUARDIA_KITCHEN_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Kitchen 1000 Event.
        - Fix partyfollows for 1 pc parties
        """
        owu.add_exploremode_to_partyfollows(script)
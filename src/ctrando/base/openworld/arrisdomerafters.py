"""Openworld Arris Dome Rafters"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Rafters"""
    loc_id = ctenums.LocID.ARRIS_DOME_RAFTERS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Food Rafters Event.
        - Remove the "There it is!" scene with the rat.
        """

        script.set_function(0xB, FID.ACTIVATE, EF().add(EC.return_cmd()))

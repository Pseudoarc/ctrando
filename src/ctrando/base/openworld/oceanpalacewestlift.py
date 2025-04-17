"""Openworld Ocean Palace Western Access Lift"""

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
    """EventMod for Ocean Palace Western Access Lift"""

    loc_id = ctenums.LocID.OCEAN_PALACE_WESTERN_ACCESS_LIFT

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Western Access Lift Event.
        - Add an exploremode on after the lift stops
        """

        # Copying Crono because the rest have linked functions which will break.
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(8, FID.STARTUP)
        )
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

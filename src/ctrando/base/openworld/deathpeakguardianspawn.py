"""Openworld Death Peak Guardian Spawn"""

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
    """EventMod for Death Peak Guardian Spawn"""
    loc_id = ctenums.LocID.DEATH_PEAK_GUARDIAN_SPAWN

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Death Peak Guardian Spawn for an Open World.
        - Return Exploremode after climbing the shell.
        - Return Exploremode after dropping down the shell.
        """

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(9, FID.ACTIVATE)
        ) + 1
        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0xA, FID.ACTIVATE)
        ) + 1
        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(), pos
        )
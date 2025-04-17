"""Openworld Algetty Entrance"""

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
    """EventMod for Algetty Entrance"""
    loc_id = ctenums.LocID.ALGETTY_ENTRANCE
    closed_portal_id = 0xE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Algetty Entrance for an Open World.
        - Set the ladder to always be down.
        - Add a portal to return to pre-fall Dark Ages
        """

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(EC.return_cmd().to_bytearray(), pos)
        pos += 1
        script.delete_jump_block(pos)

        cls.add_portal(script)

    @classmethod
    def add_portal(cls, script: Event):
        change_loc_command = EC.change_location(
            ctenums.LocID.LAST_VILLAGE_EMPTY_HUT, 0x19, 0x17,
            Facing.DOWN, 0, True
        )

        closed_portal_id = owu.insert_portal_complete(
            script, 0x57, 0x97,
            0x358, 0x310,
            FID.ARBITRARY_0, FID.ARBITRARY_1, 1, change_loc_command,
            memory.Flags.HAS_ALGETTY_PORTAL
        )

        if closed_portal_id != cls.closed_portal_id:
            raise ValueError

        # Fix up the portal that we just made
        # 1) Make it only appear when Zeal has fallen
        # 2) Add the screen scroll for a consistent position for the portal effect

        # 1) Make it only appear when Zeal has fallen
        #    No, handled by flag now?
        # pos = script.get_function_start(closed_portal_id, FID.STARTUP)
        # script.insert_commands(
        #     EF().add_if(
        #         EC.if_not_flag(memory.Flags.ZEAL_HAS_FALLEN),
        #         EF().add(EC.return_cmd()).add(EC.end_cmd())
        #     ).get_bytearray(), pos
        # )

        # 2) Add the screen scroll for a consistent position for the portal effect
        pos = script.get_function_start(closed_portal_id, FID.ACTIVATE)
        pos = script.find_exact_command(EC.set_explore_mode(False), pos)
        script.insert_commands(
            EC.generic_command(0xE7, 0x30, 0x27).to_bytearray(), pos
        )

"""Openworld North Cape"""

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
    """EventMod for North Cape"""
    loc_id = ctenums.LocID.NORTH_CAPE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify North Cape for an Open World.
        - Remove storyline checks.
        - Remove checks related to the Magus flashback scene.
        - Default hide the sparkle (recruit enables).
        - Give everyone a normal startup function and let the recruit setter handle
          the rest.
        """
        cls.remove_extra_checks(script)
        cls.fix_magus_startup(script)


    @classmethod
    def remove_extra_checks(cls, script: Event):
        """
        Remove unneeded code.  This is not strictly needed but it
        1) Frees up a flag (NC Flashback), and
        2) Makes the event much simpler to parse for the recruit setting later.
        """

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.VIEWING_NORTH_CAPE_MAGUS_FLASHBACK)
        )
        script.delete_jump_block(pos)
        script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xD2)
        )

        script.delete_jump_block(pos)
        script.delete_jump_block(pos)

        script.insert_commands(
            EC.set_own_drawing_status(False).to_bytearray(), pos)

    @classmethod
    def fix_magus_startup(cls, script: Event):
        """
        Give Magus a normal startup function.
        """
        startup = (
            EF().add(EC.load_pc_in_party(ctenums.CharID.MAGUS))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )
        script.set_function(7, FID.STARTUP, startup)


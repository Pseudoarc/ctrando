"""Openworld Black Omen 99F Seat of Agelessness"""
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
    """EventMod for Black Omen 99F Seat of Agelessness"""

    loc_id = ctenums.LocID.BLACK_OMEN_ZEAL

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen 99F Seat of Agelessness for an Open World.
        - Remove Zeal dialogue
        """

        # Zeal dialogue is a little weird.  At times it launches a thread to display the
        # dialogue and then checks for the activate button in the main thread to change the
        # animation.

        # We're going to rip all that out and just play a few of the animations.

        zeal_obj = 0x8
        pos = script.find_exact_command(
            EC.call_obj_function(0, FID.ARBITRARY_0, 1, FS.SYNC),
            script.get_object_start(zeal_obj),
        )

        # end = script.find_exact_command(EC.generic_command(0xAB, 0x07), pos)
        end = script.find_exact_command(EC.party_follow(), pos)
        script.delete_commands_range(pos, end)

        pos, _ = script.find_command([0xBB], pos)
        # script.data[pos:pos+1] = EC.generic_command(0xAD, 0x00).to_bytearray()
        script.delete_commands(pos, 1)

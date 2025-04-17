"""Openworld Tyrano Lair Throneroom"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Throneroom"""
    loc_id = ctenums.LocID.TYRANO_LAIR_THRONEROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Throneroom Event.
        - Remove dialog/pc-specific animation from Azala's scene
        - Actually, just remove the whole scene for now.
        """

        pos = script.get_object_start(0)
        script.insert_commands(
            EC.set_flag(memory.Flags.VIEWED_TYRANO_THRONE_AZALA_MONOLOGUE)
            .to_bytearray(), pos
        )

        # The scene is triggered in and obj00 coordinate checking loop
        pos, _ = script.find_command([0xC2])
        script.delete_commands(pos, 3)

        pos = script.find_exact_command(EC.party_follow(), pos) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # One of Azala's functions has some dialog and an abnormally long pause
        pos = script.get_function_start(0x8, FID.ARBITRARY_2)
        pos = script.find_exact_command(EC.pause(5))
        script.data[pos+1] = 0x20

        pos, _ = script.find_command([0xC1], pos)
        script.delete_commands(pos, 1)


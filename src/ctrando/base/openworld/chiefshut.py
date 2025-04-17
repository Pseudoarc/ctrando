"""Openworld Chief's Hut (Ioka)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Chief's Hut """
    loc_id = ctenums.LocID.IOKA_CHIEFS_HUT

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Chief's Hut Event.
        - Remove a bunch of storyline checks.  Nothing happens here in rando.
        - Give Ayla a normal startup.
        - Add an exploremode on command after sleeping.
        """

        # Delete a bunch of storyline conditions
        pos = script.get_function_start(0, FID.STARTUP)
        end, _ = script.find_command([0xB8], pos)  # String Index
        script.delete_commands_range(pos, end)
        pos += len(EC.get_blank_command(0xB8))
        end = script.find_exact_command(EC.return_cmd())
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EC.remove_object(0xD).to_bytearray(), pos
        )

        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        end = script.find_exact_command(EC.end_cmd())
        script.delete_commands_range(pos, end)

        # Give Ayla a normal startup
        # Note other characters have weird startups, but only Ayla's will cause
        # issues.  Just don't let storyline be 7C or 8A
        script.set_function(
            6, FID.STARTUP,
            EF().add(EC.load_pc_in_party(ctenums.CharID.AYLA))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
            .add(EC.end_cmd())
        )

        # Add exploremode on command after sleeping
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0, FID.ARBITRARY_0)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)
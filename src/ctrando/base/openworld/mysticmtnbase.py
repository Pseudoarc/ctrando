"""Change Mystic Mountains Base for open world."""
from ctrando.common.memory import Flags
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event,\
    get_command
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS,\
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


# Note:  There are lots of checks for storyline == 0x6C, but since we never will let
#        The storyline get to that level, it's OK to just ignore them for now.
#        Storyline is stored in 0x7F020E, and checks are made relative to that.


class EventMod(locationevent.LocEventMod):
    """EventMod for Mystic Mountains Base"""
    loc_id = ctenums.LocID.MYSTIC_MTN_BASE

    @classmethod
    def modify(cls, script: Event):
        """
        Update Mystic Mountains Base event.
        - Add an exploremore on after falling down the mountain
        """

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(8, FID.ARBITRARY_0)
        )

        block = EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
        script.insert_commands(
            block.get_bytearray(), pos
        )
        pos += len(block)
        script.delete_commands(pos, 1)

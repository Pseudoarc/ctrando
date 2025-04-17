"""Openworld Truce Market 1000"""

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
    """EventMod for Truce Market 1000"""

    loc_id = ctenums.LocID.TRUCE_MARKET

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Truce Market 1000 for an Open World.
        - Remove storyline triggers on Fritz
        - Remove the extra cutscene with mom and dad
        """

        # Remove Storyline < 0x27 Triggers
        storyline_cmd = EC.if_storyline_counter_lt(0x27)

        pos = script.find_exact_command(
            storyline_cmd, script.get_object_start(0))
        script.delete_jump_block(pos)

        for _ in range(2):
            pos = script.find_exact_command(
                storyline_cmd, script.get_object_start(0xB))
            script.delete_jump_block(pos)

        # Modify the scene that plays.  Just remove dad coming out completely.
        pos = script.find_exact_command(EC.auto_text_box(0),
                                        script.get_function_start(9, FID.TOUCH))
        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        pos = script.find_exact_command(
            EC.call_obj_function(8, FID.ARBITRARY_0, 5, FS.HALT),
            script.get_function_start(0, FID.ARBITRARY_0)
        )
        script.delete_commands(pos, 1)

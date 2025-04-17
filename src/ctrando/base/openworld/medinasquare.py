"""Change Medina Square for open world."""
from typing import Optional

from ctrando.common import ctenums
from ctrando.common.memory import Flags, FlagData
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Medina Square"""
    loc_id = ctenums.LocID.MEDINA_SQUARE

    @classmethod
    def modify(cls, script: Event):
        """
        Update Medina Square
        - Remove screen scrolling for first visit.
        - Replace storyline triggers with Flag triggers (Statue)
        """
        cls.remove_initial_screen_scroll(script)
        cls.replace_storyline_triggers(script)

    @classmethod
    def remove_initial_screen_scroll(cls, script: Event):
        """
        Remove screen scrolling for first visit.
        """
        pos = script.find_exact_command(
            EC.if_flagdata(FlagData(0x7F01A2, 0x20))
        )

        end = script.find_exact_command(EC.end_cmd(), pos)
        script.delete_commands_range(pos, end)

    @classmethod
    def replace_storyline_triggers(cls, script: Event):
        """
        Replace storline < 0x8A with Magus not defeated.
        """

        pos: Optional[int] = script.get_object_start(0)
        repl_cmd = EC.if_not_flag(Flags.MAGUS_DEFEATED)
        while True:
            pos = script.find_exact_command_opt(
                EC.if_storyline_counter_lt(0x8A), pos
            )

            if pos is None:
                break

            script.replace_jump_cmd(pos, repl_cmd)

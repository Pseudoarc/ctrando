"""Openworld Manoria Kitchen"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Kitchen"""
    loc_id = ctenums.LocID.MANORIA_KITCHEN

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Kitchen Event.
        - Change storyline triggers
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x1B))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.MANORIA_BOSS_DEFEATED)
        )

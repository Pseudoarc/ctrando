"""Openworld Manoria Royal Guard Hall"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Royal Guard Hall"""
    loc_id = ctenums.LocID.MANORIA_ROYAL_GUARD_HALL

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Royal Guard Hall Event.
        - Change storyline triggers
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x1B))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.MANORIA_BOSS_DEFEATED)
        )

        # This storyline check doesn't seem to do anything and references
        # an unused value of 0x18
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x18))
        script.delete_jump_block(pos)

"""Openworld Manoria Confinement"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID


class EventMod(locationevent.LocEventMod):
    """EventMod for Manoria Confinement"""
    loc_id = ctenums.LocID.MANORIA_CONFINEMENT

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Manoria Confinement Event.
        - Change storyline triggers
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x1B))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.MANORIA_BOSS_DEFEATED)
        )

        pos = script.get_function_start(0xA, FID.ACTIVATE)
        owu.update_add_item(script, pos)
        owu.remove_item_pause(script, pos)
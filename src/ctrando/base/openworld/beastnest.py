"""Openworld Beast Nest"""

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
    """EventMod for Beast Nest"""
    loc_id = ctenums.LocID.BEAST_NEST

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Beast Nest for an Open World.
        - Change the storyline checking/setting to use a flag.
        - Modify power tab pickup.
        """

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xB4))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.BEAST_CAVE_BOSS_DEFEATED)
        )

        pos = script.find_exact_command(EC.set_storyline_counter(0xB4), pos)
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.BEAST_CAVE_BOSS_DEFEATED))

        # There's a storyline check on the Woe Chain, but we'll ignore it because
        # the storyline never gets that high.

        # Set a spot for beast cave boss objective.
        # pos = script.find_exact_command(EC.set_flag(memory.Flags.BEAST_CAVE_BOSS_DEFEATED))
        pos, cmd = script.find_command([0xEA], pos)
        pos, _ = script.find_command([0xEA], pos + len(cmd))
        script.insert_commands(
            EF().add(EC.set_explore_mode(False))
            .add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )

        for obj_id in range(0xA, 0x11):
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0xB4),
                script.get_object_start(obj_id)
            )
            script.replace_jump_cmd(
                pos, EC.if_not_flag(memory.Flags.BEAST_CAVE_BOSS_DEFEATED)
            )

        # Power Tab
        pos = script.get_function_start(9, FID.ACTIVATE)
        owu.update_add_item(script, pos)
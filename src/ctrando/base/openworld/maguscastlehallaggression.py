"""Openworld Castle Magus Hall of Aggression"""

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
    """EventMod for Castle Magus Hall of Aggression"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_HALL_AGGRESSION

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Hall of Aggression for an Open World.
        - Fix exploremode on entry
        - Remove dialogue and animations from Ozzie scene at the end of the hall.
        """

        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_object_start(9)
        )
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        repl_scene = (
            EF().add(EC.play_animation(3))
            .add(EC.play_animation(0))
            .add(EC.set_own_facing('left')).add(EC.pause(0.25))
            .add(EC.set_own_facing('right')).add(EC.pause(0.25))
            .add(EC.set_own_facing('down'))
            .add(EC.play_animation(3)).add(EC.pause(0.25))
            .add(EC.play_animation(1)).add(EC.pause(0.25))
            .add(EC.set_move_speed(0x80))
            .add(EC.set_move_properties(True, True))
            .add(EC.move_sprite(0x27, 4))
            .add(EC.set_own_drawing_status(False))
            .add(EC.set_flag(memory.Flags.MAGUS_CASTLE_OZZIE_LEFT_HALL_AGGRESSION))
            .add(EC.reset_byte(0x7F020C))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))

        )

        pos, _ = script.find_command(
            [0xC1],
            script.get_function_start(9, FID.TOUCH)
        )

        del_end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, del_end)
        script.insert_commands(repl_scene.get_bytearray(), pos)

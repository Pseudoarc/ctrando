"""Openworld Tyrano Lair Storage"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tyrano Lair Storage"""
    loc_id = ctenums.LocID.TYRANO_LAIR_STORAGE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tyrano Lair Storage Event.
        - Add switch flag unsetting to each PC
        """

        for obj_id in range(2, 7):
            pos = script.find_exact_command(
                EC.play_animation(0),
                script.get_function_start(obj_id, FID.STARTUP)
            )

            script.insert_commands(
                EC.reset_flag(memory.Flags.TYRANO_LAIR_SWITCH_FALLING).to_bytearray(),
                pos
            )

        new_magus_fall_st_func = (
            EF()
            .add_if(
                EC.if_flag(memory.Flags.TYRANO_LAIR_SWITCH_FALLING),
                EF()
                .add(EC.set_own_drawing_status(False))
                .add(EC.set_move_speed(0xF0))
                .add(EC.move_sprite(0x1D, 0x0C))
                .add(EC.set_own_drawing_status(True))
                .add(EC.generic_command(0x8E, 0x3B))  # Sprite prio
                .add(EC.set_move_speed(0x80))
                .add(EC.static_animation(0x6E))
                .add(EC.move_sprite(0x1D, 0x15, True))
                .add(EC.play_animation(0))
                .add(EC.reset_flag(memory.Flags.TYRANO_LAIR_SWITCH_FALLING))
            )
        )

        pos = script.find_exact_command(
            EC.set_controllable_infinite(),
            script.get_function_start(7, FID.STARTUP)
        )
        script.insert_commands(new_magus_fall_st_func.get_bytearray(), pos)

        new_magus_fall_arb = (
            EF()
            .add(EC.set_move_speed(0x80))
            .add(EC.static_animation(0x6E))
            .add(EC.generic_command(0xAD, 0x05))  # pause
            .add(EC.vector_move(200, 20, True))
            .add(EC.return_cmd())
        )
        script.set_function(7, FID.ARBITRARY_0, new_magus_fall_arb)


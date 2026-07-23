"""Openworld Ocean Palace Elevator Top"""

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
    """EventMod for Ocean Palace Elevator Top"""

    loc_id = ctenums.LocID.OCEAN_PALACE_EASTERN_ACCESS_LIFT
    room_status_addr = 0x7F0214

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Elevator Top.
        - Add an ability to travel down on the elevator and skip the bulk of the
          dungeon.
        """

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x01A2, 2)
        )
        script.insert_commands(
            EF()
            .add_if(
                EC.if_flag(memory.Flags.ZEAL_HAS_FALLEN),
                EF()
                .add(EC.assign_val_to_mem(2, cls.room_status_addr, 1))
            ).get_bytearray(), pos
        )

        # Replace the check of status > 0 with status == 1 for the elevator entrance
        # animations.
        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.room_status_addr, OP.GREATER_THAN, 0),
            pos
        )
        script.replace_jump_cmd(
            pos,
            EC.if_mem_op_value(cls.room_status_addr, OP.EQUALS, 1)
        )

        pos = script.get_object_start(1)
        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.room_status_addr, OP.GREATER_THAN, 0),
            pos
        )
        script.delete_jump_block(pos)

        # Copy switch activation from other elevator room
        obj_id = script.append_empty_object()
        script.set_function(
            obj_id, FID.STARTUP,
            EF()
            .add(EC.load_npc(ctenums.NpcID.GIANT_BLUE_STAR))
            .add(EC.set_object_coordinates_pixels(0x26, 0x146))
            .add_if(
                EC.if_not_flag(memory.Flags.ZEAL_HAS_FALLEN),
                EF()
                .add(EC.set_own_drawing_status(False))
                .add(EC.disable_script_processing(obj_id))
            )
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        script.set_function(
            obj_id, FID.ACTIVATE,
            EF()
            .add(EC.play_sound(0x52))
            .add(EC.set_explore_mode(False))
            .add(EC.set_own_drawing_status(False))
            .add(EC.play_sound(0x56))
            .add(EC.shake_screen(True))
            .add(EC.generic_command(0xE6, 0xE000, 0x01, 0x08))  # scroll
            .add(EC.move_party(
                0x87, 0x14, 0x88, 0x11, 0x88, 0x17))
            .add(EC.generic_command(0xE7, 0x0, 0xE))
            .add(EC.shake_screen(False))
            .add(EC.play_sound(0x6D))
            .add(EC.generic_command(0xE6, 0xF000, 0x01, 0x00))
            .add(EC.generic_command(0xE6, 0x0C00, 0x02, 0x00))
            .add(EC.pause(0.5))
            .add(EC.darken(4))
            .add(EC.fade_screen())
            .add(EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1))
            .add(EC.change_location(0x1A2, 0x07, 0x10,
                                    force_command_id=0xDF))
        )
        script.set_function(
            obj_id, FID.TOUCH, EF().add(EC.return_cmd())
        )

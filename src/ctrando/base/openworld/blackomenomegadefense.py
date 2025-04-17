"""Openworld Black Omen Omega Defense"""
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
    """EventMod for Black Omen Omega Defense"""
    loc_id = ctenums.LocID.BLACK_OMEN_98F_OMEGA_DEFENSE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen Omega Defense for an Open World.
        - Prevent access to throne unless the Omen Boss flag is set
        - (Maybe) Add a teleporter back to the start.
        """

        copy_cmd = EC.generic_command(0xE4, 0, 0x1C, 1, 0x1F, 7, 1, 0x3B)
        pos = script.find_exact_command(copy_cmd)

        script.insert_commands(
            EC.if_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE,
                       len(copy_cmd)+1).to_bytearray(),
            pos
        )

        copy_cmd.command = 0xE5
        pos = script.find_exact_command(copy_cmd, script.get_function_start(8, FID.ACTIVATE))
        script.insert_commands(
            EC.if_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE,
                       len(copy_cmd) + 1).to_bytearray(),
            pos
        )

        # Add fake exit to throne
        x_addr, y_addr = 0x7F0212, 0x7F0214
        pos = script.find_exact_command(
            EC.if_mem_op_value(x_addr, OP.EQUALS, 3),
            script.get_function_start(0xE, FID.STARTUP)
        )
        new_cond = (
            EF()
            .add_if(
                EC.if_mem_op_value(y_addr, OP.LESS_OR_EQUAL, 5),
                EF()
                .add_if(
                    EC.if_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE),
                    EF()
                    .add(EC.darken(1))
                    .add(EC.fade_screen())
                    .add(EC.change_location(
                        ctenums.LocID.BLACK_OMEN_ZEAL,
                        0x08, 0x2B, Facing.UP
                    ))
                    .add(EC.end_cmd())
                )
            )
        )
        script.insert_commands(new_cond.get_bytearray(), pos)

        obj_id = script.append_empty_object()

        x_addr, y_addr = 0x7F0212, 0x7F0214
        x_coord, y_coord = 0xC, 0x9
        startup = (
            EF()
            .add(EC.load_npc(ctenums.NpcID.SAVE_POINT))
            .add(EC.set_object_coordinates_tile(x_coord, y_coord))
            .add(EC.generic_one_arg(0x8E, 0x3B))
            .add_if(
                EC.if_flag(memory.Flags.BLACK_OMEN_FINAL_PANELS_DEFEATED),
                EF().jump_to_label(EC.jump_forward(), "show")
            ).add(EC.disable_script_processing(obj_id))
            .add(EC.set_own_drawing_status(False))
            .set_label("show")
            .add(EC.return_cmd())
            .add(EC.set_solidity_properties(False, False))
            .set_label("loop")
            .add_if(
                EC.if_mem_op_value(x_addr, OP.EQUALS, x_coord),
                EF().add_if(
                    EC.if_mem_op_value(y_addr, OP.EQUALS, y_coord),
                    EF().add(EC.play_sound(0x2B))
                    .add(EC.set_explore_mode(False))
                    .add(EC.darken(1))
                    .add(EC.fade_screen())
                    .add(EC.change_location(
                        ctenums.LocID.BLACK_OMEN_1F_ENTRANCE,
                        0x05, 0x28, Facing.DOWN
                    ))
                )
            ).jump_to_label(EC.jump_back(), "loop")
        )

        script.set_function(obj_id, FID.STARTUP, startup)
        script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))

        pos = script.find_exact_command(
            EC.enable_script_processing(0xE),
            script.get_function_start(8, FID.ACTIVATE)
        )
        script.insert_commands(
            EF().add(EC.enable_script_processing(obj_id))
            .add(EC.set_object_drawing_status(obj_id, True))
            .get_bytearray(), pos
        )

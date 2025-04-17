"""Openworld Black Omen 1F Entrance"""
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
    """EventMod for Black Omen 1F Entrance"""
    loc_id = ctenums.LocID.BLACK_OMEN_1F_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Black Omen 1F Entrance for an Open World.
        - Remove Zeal scene from Mega Mutant Entrance.
        - Add the shortcut sparkle.
        """

        zeal_obj = 0x08
        script.set_function(zeal_obj, FID.STARTUP,
                            EF().add(EC.return_cmd()).add(EC.end_cmd()))
        script.set_function(
            zeal_obj, FID.ACTIVATE,
            EF()
            .add(EC.generic_command(0xE7, 0, 0x18))
            .add(EC.play_sound(0x78))
            .add(get_command(bytes.fromhex("FF907F5038")))  # big portal mode7
            .add(EC.call_obj_function(0xC, FID.TOUCH, 6, FS.CONT))
            .add(EC.call_obj_function(0xB, FID.TOUCH, 6, FS.HALT))
            .add(EC.play_sound(0x78))
            .add(get_command(bytes.fromhex("FF91"))).add(EC.pause(1))
            .add(EC.generic_command(0xE7, 0, 0x1B))
            .add(EC.pause(1))
            .add(EC.return_cmd())
        )

        obj_id = script.append_empty_object()
        x_addr, y_addr = 0x7F0212, 0x7F0214
        x_coord, y_coord = 0x5, 0x27
        startup = (
            EF()
            .add(EC.load_npc(ctenums.NpcID.SAVE_POINT))
            .add(EC.set_object_coordinates_tile(x_coord, y_coord))
            .add(EC.generic_one_arg(0x8E, 0x3B))
            .add_if(
                EC.if_flag(memory.Flags.HAS_OMEN_NU_SHOP_ACCESS),
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
                    .add_if_else(
                        EC.if_flag(memory.Flags.BLACK_OMEN_FINAL_PANELS_DEFEATED),
                        EF()
                        .add(EC.decision_box(
                            script.add_py_string(
                                "Where to?{line break}"
                                "   Nu Shop{line break}"
                                "   Final Panels{null}"
                            ), 1, 2
                        ))
                        .add(EC.darken(1))
                        .add(EC.fade_screen())
                        .add_if(
                            EC.if_result_equals(2),
                            EF()
                            .add(EC.change_location(
                                ctenums.LocID.BLACK_OMEN_98F_OMEGA_DEFENSE,
                                0x0B, 0x09, Facing.LEFT
                            ))
                        )
                        .add(EC.change_location(
                            ctenums.LocID.BLACK_OMEN_47F_EMPORIUM,
                            0x0B, 0x10, Facing.LEFT
                        )),
                        EF().add(EC.darken(1))
                        .add(EC.fade_screen())
                        .add(EC.change_location(
                            ctenums.LocID.BLACK_OMEN_47F_EMPORIUM,
                            0x0B, 0x10, Facing.LEFT
                        ))
                    )
                )
            ).jump_to_label(EC.jump_back(), "loop")
        )

        script.set_function(obj_id, FID.STARTUP, startup)
        script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))



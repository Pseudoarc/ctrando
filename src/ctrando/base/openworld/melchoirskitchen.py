"""Openworld Melchior's Kitchen"""

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
    """EventMod for Melchior's Kitchen"""

    loc_id = ctenums.LocID.MELCHIORS_KITCHEN
    can_forge_masa_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Melchior's Kitchen for an Open World.
        - Update Masa forge conditions
        - Never hide Melchior
        """

        # Remove the block that would hide Melchior if he's in the treasury.
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.MELCHIOR_IN_TREASURY),
            script.get_object_start(8)
        )
        script.delete_jump_block(pos)

        can_forge_masa_func = (
            EF()
            .add_if(
                EC.if_has_item(ctenums.ItemID.BENT_HILT),
                EF().add(EC.set_bit(cls.can_forge_masa_addr, 0x01)),
            )
            .add_if(
                EC.if_has_item(ctenums.ItemID.BENT_SWORD),
                EF().add(EC.set_bit(cls.can_forge_masa_addr, 0x02)),
            )
            .add_if(
                EC.if_has_item(ctenums.ItemID.DREAMSTONE),
                EF().add(EC.set_bit(cls.can_forge_masa_addr, 0x04)),
            )
            .add_if(
                EC.if_pc_active(ctenums.CharID.LUCCA),
                EF().add(EC.set_bit(cls.can_forge_masa_addr, 0x08)),
            )
            .add_if(
                EC.if_pc_active(ctenums.CharID.ROBO),
                EF().add(EC.set_bit(cls.can_forge_masa_addr, 0x08)),
            )
        )

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(can_forge_masa_func.get_bytearray(), pos)

        new_melchior_activate = (
            EF()
            .add_if(
                EC.if_flag(memory.Flags.OW_OMEN_PRESENT),
                EF().add(EC.auto_text_box(0x2D)),
            )
            .add_if(
                EC.if_flag(memory.Flags.HAS_FORGED_MASAMUNE),
                EF().jump_to_label(EC.jump_forward(), "shop"),
            )
            .add_if(
                EC.if_mem_op_value(cls.can_forge_masa_addr, OP.EQUALS, 7),
                EF()
                .add(
                    EC.auto_text_box(
                        script.add_py_string(
                            "MELCHIOR: Bring {lucca} or {robo} to help{line break}"
                            "repair the Masamune.{null}"
                        )
                    )
                )
                .jump_to_label(EC.jump_forward(), "shop"),
            )
            .add_if(
                EC.if_mem_op_value(cls.can_forge_masa_addr, OP.EQUALS, 0x0F),
                EF()
                .add(EC.set_explore_mode(False))
                .add(EC.move_party(0x28, 0x19, 0x2A, 0x19,
                                   0x26, 0x19))
                .add(
                    EC.auto_text_box(
                        script.add_py_string(
                            "MELCHIOR:  It'll take a while to fix this...{null}"
                        )
                    )
                )
                .add(EC.play_song(3))
                .add(EC.set_move_speed(0x20))
                .add(EC.play_animation(1))
                .add(EC.move_sprite(0x27, 0x1B))
                .add(EC.move_sprite(0x29, 0x1B))
                .add(EC.move_sprite(0x2B, 0x1E, is_animated=True))
                .add(EC.darken(0xF))
                .add(EC.fade_screen())
                .add(EC.set_object_coordinates_tile(0x28, 0x17))
                .add_if_else(
                    EC.if_pc_active(ctenums.CharID.LUCCA),
                    EF().add(EC.call_obj_function(3, FID.ARBITRARY_2, 6, FS.HALT)),
                    EF().add(EC.call_obj_function(4, FID.ARBITRARY_2, 6, FS.HALT))
                )
                .add(EC.reset_animation())
                .add(EC.pause(2))
                .add(EC.darken(0xF4))
                .add(EC.fade_screen())
                .add(EC.assign_val_to_mem(ctenums.ItemID.MASAMUNE_1, 0x7F0200, 1))
                .add(EC.add_item_memory(0x7F0200))
                .add(EC.set_flag(memory.Flags.HAS_FORGED_MASAMUNE))
                .add(EC.auto_text_box(0x27))
                .add(EC.set_own_facing("right"))
                .add(EC.reset_animation()).add(EC.pause(0.375))
                .add_if_else(
                    EC.if_pc_active(ctenums.CharID.LUCCA),
                    EF().add(EC.call_obj_function(3, FID.ARBITRARY_1, 6, FS.HALT)),
                    EF().add(EC.call_obj_function(4, FID.ARBITRARY_1, 6, FS.HALT))
                ).add(EC.auto_text_box(
                    script.add_py_string(
                        "MELCHIOR:Take a good look!{line break}"
                        "THIS is the {item}!{null}"
                    )
                )).add(EC.auto_text_box(owu.add_default_treasure_string(script)))
                .add(get_command(bytes.fromhex("F1E083")))  # remove white
                .add(EC.auto_text_box(0x28))
                .add(EC.set_object_drawing_status(9, False))
                .add(EC.party_follow()).add(EC.set_explore_mode(True))
                .add(EC.return_cmd()),
            )
            .set_label("shop")
            .add(EC.decision_box(0, 2, 3))  # Shop
            .add_if_else(
                EC.if_result_equals(2),
                EF()
                .add(EC.generic_command(0xC8, 0x84))  # Shop
                .add(EC.auto_text_box(1)),
                EF().add(EC.play_animation(3)).add(EC.auto_text_box(2)),
            )
            .add(EC.play_animation(1))
            .add(EC.return_cmd())
        )
        script.set_function(8, FID.ACTIVATE, new_melchior_activate)

        for char_id in (ctenums.CharID.LUCCA, ctenums.CharID.ROBO):
            obj_id = char_id + 1
            script.set_function(
                obj_id, FID.ARBITRARY_2,
                EF()
                .add(EC.set_object_coordinates_tile(0x2A, 0x17))
                .add(EC.set_own_facing('down'))
                .add(EC.return_cmd())
            )

        pos = script.get_function_start(9, FID.STARTUP)
        script.delete_commands(pos, 1)

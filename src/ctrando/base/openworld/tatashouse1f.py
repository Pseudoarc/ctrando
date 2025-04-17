"""Openworld Tata's House 1F"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Tata's House 1F"""
    loc_id = ctenums.LocID.TATAS_HOUSE_1F

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Tata's House 1F Event.
        - Set Flags instead of storyline.
        - Change activation to sword part + met Tata
        """
        cls.modify_storyline_triggers(script)
        cls.modify_tata_activation(script)

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Replace storyline checks with flag checks.
        """

        # Tata's House uses three storyline values:
        # 1) Storyline == 0x60 (obtained bent sword)
        #   - Draws one version of Tata in the house (Obj 09).
        #   - This is the version who can give you the medal
        # 2) Storyline >= 0x66 (>= obtained Hero Medal)
        #   - Draws a different version of Tata in the house (Obj 0A).
        #     This version just argues with dad.
        #   - Changes the dialog for Obj09 Tata (he won't be drawn on next
        #     entry)

        # I don't see the point in having the Obj09 Tata

        # Change Storyline == 0x60 to Tata scene complete
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x60))
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.TATA_SCENE_COMPLETE))

        # Replace three Storyline >= 
        for _ in range(3):
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0x66),
                pos
            )
            script.replace_jump_cmd(
                pos, EC.if_flag(memory.Flags.OBTAINED_TATA_ITEM)
            )

        # Convenient that the storyline set happens at the end
        pos = script.find_exact_command(
            EC.assign_val_to_mem(0x66, 0x7F0000, 1), pos
        )
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.OBTAINED_TATA_ITEM))

    @classmethod
    def modify_tata_activation(cls, script: Event):
        """
        Change Tata to give the item after having a sword part and the
        intro scene on Denadoro
        """

        check_item_addr = 0x7F0220
        check_item_func = (
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.BENT_SWORD),
                EF().add(EC.assign_val_to_mem(1, check_item_addr, 1))
                .jump_to_label(EC.jump_forward(), 'done')
            ).add_if(
                EC.if_has_item(ctenums.ItemID.BENT_HILT),
                EF().add(EC.assign_val_to_mem(1, check_item_addr, 1))
                .jump_to_label(EC.jump_forward(), 'done')
            ).add_if(
                # May lose the sword parts when forging
                EC.if_flag(memory.Flags.REPAIRED_MASAMUNE),
                EF().add(EC.assign_val_to_mem(1, check_item_addr, 1))
                .jump_to_label(EC.jump_forward(), 'done')
            ).set_label('done')
        )

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(check_item_func.get_bytearray(), pos)

        fail_condition_id = script.add_py_string(
            "TATA: So there was no sword up there?{null}"
        )

        item_str_id = script.add_py_string(
            "{line break}Got 1 {item}!{line break}{itemdesc}{null}"
        )

        tata_activate = (
            EF().add_if(
                EC.if_flag(memory.Flags.OBTAINED_TATA_ITEM),
                EF().add(EC.set_own_facing_pc(0))
                .add(EC.auto_text_box(5))
                .jump_to_label(EC.jump_forward(), 'done')
            ).add_if(
                EC.if_mem_op_value(check_item_addr, OP.EQUALS, 1),
                EF().add(EC.set_explore_mode(False))
                .add(EC.set_own_facing_pc(0))
                .add(EC.auto_text_box(1))
                .add(EC.call_obj_function(8, FID.ARBITRARY_0, 3, FS.HALT))
                .add(EC.generic_command(0xAD, 5))
                .add(EC.play_sound(4))
                .add(EC.generic_command(0xAD, 5))
                .add(EC.assign_val_to_mem(ctenums.ItemID.HERO_MEDAL,
                                          0x7F0200, 1))
                .add(EC.add_item(ctenums.ItemID.HERO_MEDAL))
                .add(EC.auto_text_box(item_str_id))
                .add(EC.set_flag(memory.Flags.OBTAINED_TATA_ITEM))
                .add(EC.set_explore_mode(True))
                .jump_to_label(EC.jump_forward(), 'done')
            ).add(EC.auto_text_box(fail_condition_id))
        )  # The return is sitting in touch in the vanilla script

        tata_obj = 9  # Item-giving Tata
        script.set_function(tata_obj, FID.ACTIVATE, tata_activate)

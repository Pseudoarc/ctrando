"""Openworld Ioka Trading Post"""
import dataclasses

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
from ctrando.strings import ctstrings


@dataclasses.dataclass()
class TradeSelection:
    base_item: ctenums.ItemID
    upgrade_item: ctenums.ItemID
    trade_item_1: ctenums.ItemID
    trade_item_2: ctenums.ItemID


class EventMod(locationevent.LocEventMod):
    """EventMod for Ioka Trading Post"""

    loc_id = ctenums.LocID.IOKA_TRADING_POST
    item_count_temp = 0x7F0230
    upgrade_flag = memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS
    trade_selection = 0x7F020C
    materials_required_addr = 0x7F0232
    armor_materials_required_addr = 0x7F0234
    armor_flag = memory.Flags.HAS_ALGETTY_PORTAL

    trade_selection_dict: dict[int, TradeSelection] = {
        0x03: TradeSelection(ctenums.ItemID.RUBY_GUN, ctenums.ItemID.DREAM_GUN,
                             ctenums.ItemID.PETAL, ctenums.ItemID.FANG),
        0x05: TradeSelection(ctenums.ItemID.SAGE_BOW, ctenums.ItemID.DREAM_BOW,
                             ctenums.ItemID.PETAL, ctenums.ItemID.HORN),
        0x09: TradeSelection(ctenums.ItemID.STONE_ARM, ctenums.ItemID.MAGMA_HAND,
                             ctenums.ItemID.PETAL, ctenums.ItemID.FEATHER),
        0x06: TradeSelection(ctenums.ItemID.FLINT_EDGE, ctenums.ItemID.AEON_BLADE,
                             ctenums.ItemID.FANG, ctenums.ItemID.HORN),
        0x0A: TradeSelection(ctenums.ItemID.RUBY_VEST, ctenums.ItemID.RUBY_VEST,
                             ctenums.ItemID.FANG, ctenums.ItemID.FEATHER),
        0x0C: TradeSelection(ctenums.ItemID.ROCK_HELM, ctenums.ItemID.ROCK_HELM,
                             ctenums.ItemID.HORN, ctenums.ItemID.FEATHER)
    }

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ioka Trading Post for an Open World.
        - Remove storyline lock on trading
        """

        pos = script.get_object_start(0)

        while True:
            pos, cmd = script.find_command_opt([0x18], pos)

            if pos is None:
                break

            if cmd.args[0] == 0x72:
                script.delete_jump_block(pos)
            elif cmd.args[0] == 0x8A:
                script.replace_jump_cmd(
                    pos, EC.if_not_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS)
                )
            else:
                pos += len(cmd)
            # elif cmd.args[0] == 0xD4:
            #     script.replace_jump_cmd(
            #         pos, EC.if_not_flag(memory.Flags.HAS_ALGETTY_PORTAL)
            #     )

        trade_confirm_string_id = script.add_py_string(
            "Trade for {item}?{line break}"
            "   Yes.{line break}"
            "   No.{null}"
        )
        got_item_string_id = owu.add_default_treasure_string(script)

        new_trade_fn = EF()
        for selection_val, selection_data in cls.trade_selection_dict.items():
            new_trade_fn.append(
                EF().add_if(
                    EC.if_mem_op_value(cls.trade_selection, OP.EQUALS, selection_val),
                    cls.make_trading_post_block(
                        selection_data.base_item, selection_data.upgrade_item,
                        trade_confirm_string_id, got_item_string_id,
                        selection_data.trade_item_1, selection_data.trade_item_2
                    )
                ).add(EC.pause(0))
            )
        new_trade_fn.add(EC.return_cmd())

        script.set_function(0xC, FID.ARBITRARY_1, new_trade_fn)

        # Modify item spoiler
        pos, _ = script.find_command([0xBB],
                                     script.get_function_start(9, FID.ACTIVATE))
        script.delete_commands(pos, 3)

        # Other
        cls.modify_material_count_checks(script)
        cls.modify_elder_activate(script)

    @classmethod
    def make_trading_post_block(
            cls,
            base_item_id: ctenums.ItemID,
            upgrade_item_id: ctenums.ItemID,
            trade_confirm_string_id: int,
            got_item_string_id: int,
            trade_item_1: ctenums.ItemID,
            trade_item_2: ctenums.ItemID,
    ) -> EF:

        prefix=trade_item_1.name + "_" + trade_item_2.name

        ret_ef = (
            EF()
            .add(EC.assign_val_to_mem(base_item_id, 0x7F0200, 1))
            .add_if(
                EC.if_flag(cls.upgrade_flag),
                EF().add(EC.assign_val_to_mem(upgrade_item_id, 0x7F0200, 1))
            )
            .add(EC.decision_box(trade_confirm_string_id, 1, 2, "top"))
            .add_if(
                EC.if_result_equals(1),  # Yes
                EF()
                .add(EC.assign_mem_to_mem(cls.materials_required_addr, cls.item_count_temp, 1))
                .set_label(prefix+"_loop_st")
                .add_if(
                    EC.if_mem_op_value(cls.item_count_temp, OP.GREATER_THAN, 0),
                    EF()
                    .add(EC.remove_item(trade_item_1))
                    .add(EC.remove_item(trade_item_2))
                    .add(EC.decrement_mem(cls.item_count_temp))
                    .jump_to_label(EC.jump_back(), prefix+"_loop_st")
                )
                .add(EC.play_sound(0xB0))
                .add(EC.add_item_memory(0x7F0200))
                .add(EC.auto_text_box(got_item_string_id))
            )
        )

        return ret_ef

    @classmethod
    def modify_material_count_checks(cls, script: locationevent.LocationEvent):
        pos = script.get_object_start(0)
        script.insert_commands(
            EF()
            .add_if_else(
                EC.if_flag(cls.upgrade_flag),
                EF().add(EC.assign_val_to_mem(3, cls.materials_required_addr, 1)),
                EF().add(EC.assign_val_to_mem(3, cls.materials_required_addr, 1))
            ).add(EC.assign_val_to_mem(10, cls.armor_materials_required_addr, 1))
            .get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020E, OP.LESS_THAN, 3)
        )
        addr = 0x7F020E

        # The material counts go in 0x7F020E and the next 3 spots.
        # These checks compare each to the requirement to see whether it's even possible to trade.
        for _ in range(4):
            script.replace_jump_cmd(
                pos,
                EC.if_mem_op_mem(addr, OP.LESS_THAN, cls.materials_required_addr),
            )
            addr += 2
            pos, cmd = script.find_command([0x12], pos)

        # Next checks actually remove from the material counts

        for outer in range(2):
            addr = 0x7F020E
            for inner in range(4):
                pos, cmd = script.find_command([0x1A], pos)  # If result == xx
                pos = script.find_exact_command(EC.if_mem_op_value(addr, OP.LESS_THAN, 3))
                script.replace_jump_cmd(
                    pos,
                    EC.if_mem_op_mem(addr, OP.LESS_THAN, cls.materials_required_addr)
                )
                if outer == 0:
                    pos, __ = script.find_command([0x5F], pos)
                    script.replace_command_at_pos(pos, EC.sub_from_memory(addr, cls.materials_required_addr))

                addr += 2

        # Get the ruby armor checks

        addr = 0x7F020E
        pos = script.get_function_start(0xC, FID.ARBITRARY_2)

        for _ in range(4):
            pos = script.find_exact_command(
                EC.if_mem_op_value(addr, OP.LESS_THAN, 10), pos
            )
            script.replace_jump_cmd(
                pos,
                EC.if_mem_op_mem(addr, OP.LESS_THAN, cls.armor_materials_required_addr)
            )
            addr += 2

        got_item_str_id = owu.add_default_treasure_string(script)
        pos = script.find_exact_command(EC.play_sound(0xB0), pos) + 2
        script.delete_commands(pos, 2)
        script.insert_commands(
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.RUBY_ARMOR, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(got_item_str_id))
            .get_bytearray(), pos
        )

        for _ in range(4):
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0220, OP.LESS_THAN, 10), pos
            )
            script.replace_jump_cmd(
                pos,
                EC.if_mem_op_mem(0x7F0220, OP.LESS_THAN, cls.armor_materials_required_addr)
            )

        cmd_id = EC.decision_box(0, 0, 1, "top").command
        pos, _ = script.find_command([cmd_id], pos)
        script.delete_commands(pos, 4)

        # # finally, replace the trade strings to read from the required
        # script.strings[3] = ctstrings.CTString.from_str(
        #     '{"1}Fang,{"2} {"1}Petal,{"2} {"1}Horn,{"2} {"1}Feather{"2}...{linebreak+0}'
        #     'Bring {value 8} each of any 2 items, I give you{linebreak+0}'
        #     '1 weapon or 1 item!{linebreak+0}'
        #     'What you give me?{null}'
        # )
        #
        # pos = script.find_exact_command(
        #     EC.auto_text_box(3), script.get_function_start(8, FID.ACTIVATE)
        # )
        # script.insert_commands(
        #     EC.assign_mem_to_mem(cls.materials_required_addr, 0x7E0200, 1)
        #     .to_bytearray(), pos
        # )

        pos = script.get_function_start(0xC, FID.ARBITRARY_0)
        for _ in range(2):
            script.find_exact_command(
                EC.text_box(8, True), pos
            )
            script.delete_commands(pos, 1)


    @classmethod
    def set_materials_required(
            cls, script: locationevent.LocationEvent,
            num_required_base: int | None = None,
            num_required_upgrade: int | None = None,
            num_required_special: int | None = None
    ):
        pos = script.get_object_start(0)
        set_cmd = EC.assign_val_to_mem(3, cls.materials_required_addr, 1)

        pos, cmd = script.find_command([set_cmd.command], pos)
        if num_required_upgrade is not None:
            script.replace_command_at_pos(
                pos,
                EC.assign_val_to_mem(num_required_upgrade, cls.materials_required_addr, 1)
            )

        pos += len(cmd)
        pos, _ = script.find_command([set_cmd.command], pos)
        if num_required_base is not None:
            script.replace_command_at_pos(
                pos,
                EC.assign_val_to_mem(num_required_base, cls.materials_required_addr, 1)
            )

        pos += len(cmd)
        pos, _ = script.find_command([set_cmd.command], pos)
        if num_required_base is not None:
            script.replace_command_at_pos(
                pos,
                EC.assign_val_to_mem(num_required_special, cls.armor_materials_required_addr, 1)
            )

    @classmethod
    def modify_elder_activate(cls, script: locationevent.LocationEvent):

        script.strings[1] = ctstrings.CTString.from_str(
            "Well come. What you have?{line break}"
            "   Normal trade ({value 8}, 2 types){line break}"
            "   Special trade ({item}, {value 8}, all){line break}"
            "   No trade{null}"
        )
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xD4), script.get_object_start(8)
        )

        end = script.find_exact_command(EC.set_explore_mode(True), pos)
        script.delete_commands_range(pos, end)

        new_block = (
            EF()
            .add(EC.assign_mem_to_mem(cls.materials_required_addr, 0x7E0200, 1))
            .add(EC.assign_mem_to_mem(cls.armor_materials_required_addr, 0x7E0201, 1))
            .add(EC.assign_val_to_mem(ctenums.ItemID.RUBY_ARMOR, 0x7F0200, 1))
            .add(EC.decision_box(1, 1, 3, "top"))
            .add_if(
                EC.if_result_equals(1),
                EF()
                .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 1, FS.HALT))
            )
            .add_if(
                EC.if_result_equals(2),
                EF()
                .add_if_else(
                    EC.if_flag(cls.armor_flag),
                    EF().add(EC.call_obj_function(0xC, FID.ARBITRARY_2, 1, FS.HALT)),
                    EF().add(
                        EC.auto_text_box(
                            script.add_py_string("Come back after you have{linebreak+0}"
                                                 "Algetty portal.{null}"))
                    )
                )

            )
        )

        script.insert_commands(new_block.get_bytearray(), pos)






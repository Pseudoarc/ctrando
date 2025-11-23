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
                .add(EC.assign_val_to_mem(3, cls.item_count_temp, 1))
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

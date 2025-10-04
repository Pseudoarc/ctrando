"""Openworld Truce Ticket Office"""
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
class FerryDest:
    name: str
    cost: int
    change_loc_cmd: EC


class EventMod(locationevent.LocEventMod):
    """EventMod for Truce Ticket Office"""

    loc_id = ctenums.LocID.TRUCE_TICKET_OFFICE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Truce Ticket Office for an Open World.
        - Remove cutscene
        """

        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.OW_FERRY_TO_PORRE),
            script.get_function_start(8, FID.ACTIVATE)
        )

        script.delete_commands(pos, 1)
        script.replace_command_at_pos(
            pos,
            EC.change_location(ctenums.LocID.PORRE_TICKET_OFFICE, 0x35, 0x2C, wait_vblank=False),
        )

        # result_dict: dict[int, FerryDest] = {
        #     1: FerryDest(
        #         "Porre", 10,
        #         EC.change_location(ctenums.LocID.PORRE_TICKET_OFFICE, 0x35, 0x2C, wait_vblank=False)
        #     ),
        #     2: FerryDest(
        #         "Choras", 100,
        #         EC.change_location(ctenums.LocID.OW_PRESENT, 2*0x46, 2*0x32, wait_vblank=False)
        #     ),
        #     4: FerryDest(
        #         "Choras 600AD", 1000,
        #         EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 2*0x46, 2*0x32, wait_vblank=False)
        #     ),
        #     5: FerryDest(
        #         "Giant's Claw", 2000,
        #         EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x77, 0x4B, wait_vblank=False)
        #     ),
        #     6: FerryDest(
        #         "Ozzie's Fort", 2000,
        #         EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x79, 0x32, wait_vblank=False)
        #     ),
        #     # 7: FerryDest(
        #     #     "{magus}'s Castle", 10000,
        #     #     EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x51, 0x3C, wait_vblank=False)
        #     # )
        # }
        #
        # def get_option_str(result: int) -> str:
        #     dest = result_dict[result]
        #     return f"       {dest.name} ({dest.cost}G)"
        #
        # main_decbox_str = (
        #     "Where to? {linebreak+0}" +
        #     get_option_str(1) + "{linebreak+0}" +
        #     get_option_str(2) + "{null}"
        # )
        #
        # alt_decbox_str = (
        #     "Where to? {linebreak+0}" +
        #     get_option_str(1) + "{linebreak+0}" +
        #     get_option_str(2) + "{linebreak+0}" +
        #     "       See 600AD Destinations{null}"
        # )
        # alt_600_str = (
        #     get_option_str(4) + "{linebreak+0}" +
        #     get_option_str(5) + "{linebreak+0}" +
        #     get_option_str(6) + "{null}"
        #     # get_option_str(7) + "{null}"
        # )
        #
        # result_addr = 0x7F0A80 + 2*0x08
        # temp_addr = 0x7F0220
        # ferry_func =(
        #     EF()
        #     .add_if_else(
        #         EC.if_has_item(ctenums.ItemID.GATE_KEY),
        #         EF()
        #         .add(EC.decision_box(script.add_py_string(alt_decbox_str),1, 3))
        #         .add_if(
        #             EC.if_result_equals(3),
        #             EF()
        #             .add(EC.decision_box(script.add_py_string(alt_600_str), 0, 3))
        #             .add(EC.assign_mem_to_mem(result_addr, temp_addr, 1))
        #             .add(EC.add(temp_addr, 4))
        #             .add(EC.assign_mem_to_mem(temp_addr, result_addr, 1))
        #         ),
        #         EF()
        #         .add(EC.decision_box(script.add_py_string(main_decbox_str), 1, 3))
        #     )
        # ).add(EC.pause(0))
        #
        # no_cash_str_id = script.add_py_string("Not enough cash!{null}")
        #
        # for result, dest in result_dict.items():
        #     print(result, dest.name)
        #     result_func = (
        #         EF()
        #         .add_if(
        #             EC.if_result_equals(result),
        #             EF()
        #             .add(EC.decision_box(
        #                 script.add_py_string(
        #                     f"Travel to {dest.name} for {dest.cost}G? {{linebreak+0}}"
        #                     "       Yes{linebreak+0}"
        #                     "       No{null}"
        #                 ), 1, 2
        #             ))
        #             .add_if(
        #                 EC.if_result_equals(1),
        #                 EF().add_if_else(
        #                     EC.if_has_gold(dest.cost),
        #                     EF().add(EC.sub_gold(dest.cost))
        #                     .add(dest.change_loc_cmd),
        #                     EF().add(EC.auto_text_box(no_cash_str_id))
        #                     .add(EC.return_cmd())
        #                 )
        #             )
        #         )
        #     )
        #     ferry_func.append(result_func)
        #
        # script.set_function(
        #     8, FID.ACTIVATE, ferry_func
        # )
        # # print(ferry_func)
        # # input()







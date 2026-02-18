"""Minor tweaks to logic that require script changes."""
import dataclasses

from ctrando.arguments import logicoptions
from ctrando.base.openworld import blackbirdscaffolding
from ctrando.common import ctenums, memory

from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.scriptmanager import ScriptManager

def apply_hard_lavos_end_boss(
        script_manager: ScriptManager
):
    script = script_manager[ctenums.LocID.LAVOS]
    pos = script.find_exact_command(
        EC.call_obj_function(8, FID.ARBITRARY_1, 4, FS.HALT)
    )
    script.insert_commands(
        EF()
        .add_if(
            EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 3),
            EF()
            .add(EC.darken(0x10))
            .add(EC.fade_screen())
            .add(EC.change_location(
                ctenums.LocID.ENDING_SELECTOR_052, 0, 0, 0,
                1, True
            )).add(EC.return_cmd())
        )
        .get_bytearray(),
        pos
    )


@dataclasses.dataclass()
class FerryDest:
    name: str
    cost: int
    change_loc_cmd: EC


def apply_boats_of_time(
        logic_options: logicoptions.LogicOptions,
        script_manager: ScriptManager
):
    result_dict: dict[int, FerryDest] = {
        1: FerryDest(
            "Porre", 10,
            EC.change_location(ctenums.LocID.PORRE_TICKET_OFFICE, 0x35, 0x2C, wait_vblank=False)
        ),
        2: FerryDest(
            "Choras", 100,
            EC.change_location(ctenums.LocID.OW_PRESENT, 2*0x46, 2*0x32, wait_vblank=False)
        ),
        4: FerryDest(
            "Choras 600AD", 1000,
            EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 2*0x44, 2*0x34, wait_vblank=False)
        ),
        5: FerryDest(
            "Giant's Claw", 2000,
            EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x77, 0x4B, wait_vblank=False)
        ),
        6: FerryDest(
            "Ozzie's Fort", 2000,
            EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x7A, 0x36, wait_vblank=False)
        ),
        # 7: FerryDest(
        #     "{magus}'s Castle", 10000,
        #     EC.change_location(ctenums.LocID.OW_MIDDLE_AGES, 0x51, 0x3C, wait_vblank=False)
        # )
    }

    def get_option_str(result: int) -> str:
        dest = result_dict[result]
        return f"       {dest.name} ({dest.cost}G)"


    for loc_id in (ctenums.LocID.TRUCE_TICKET_OFFICE,
                   ctenums.LocID.PORRE_TICKET_OFFICE):
        script = script_manager[loc_id]
        if loc_id == ctenums.LocID.TRUCE_TICKET_OFFICE:
            obj_ids = (8,)
            result_dict[1] = FerryDest(
                "Porre", 10,
                EC.change_location(ctenums.LocID.PORRE_TICKET_OFFICE, 0x35, 0x2C,
                                   wait_vblank=False)
            )
        else:
            result_dict[1] = FerryDest(
                "Truce", 10,
                EC.change_location(ctenums.LocID.TRUCE_TICKET_OFFICE, 0x6, 0x3C,
                                   wait_vblank=False)
            )
            obj_ids = (9, 0xA, 0xB)

        main_decbox_str = (
            "If you bring a gate key, we can expand{line break}"
            "service to 600AD.{full break}"
            "Where to? {linebreak+0}" +
            get_option_str(1) + "{linebreak+0}" +
            get_option_str(2) + "{null}"
        )

        alt_decbox_str = (
            "Where to? {linebreak+0}" +
            get_option_str(1) + "{linebreak+0}" +
            get_option_str(2) + "{linebreak+0}" +
            "       See 600AD Destinations{null}"
        )
        alt_600_str = (
            get_option_str(4) + "{linebreak+0}" +
            get_option_str(5) + "{linebreak+0}" +
            get_option_str(6) + "{null}"
            # get_option_str(7) + "{null}"
        )

        no_cash_str_id = script.add_py_string("Not enough cash!{null}")
        main_decbox_id = script.add_py_string(main_decbox_str)
        alt_decbox_id = script.add_py_string(alt_decbox_str)
        alt_600_id = script.add_py_string(alt_600_str)

        for obj_id in obj_ids:
            result_addr = 0x7F0A80 + 2*obj_id
            temp_addr = 0x7F0220

            if loc_id == ctenums.LocID.TRUCE_TICKET_OFFICE:
                ferry_func = EF()
            else:
                ferry_func = EF().add(EC.call_obj_function(
                8, FID.ARBITRARY_0, 3, FS.HALT))

            ferry_func.append(
                EF()
                .add_if_else(
                    EC.if_has_item(ctenums.ItemID.GATE_KEY),
                    EF()
                    .add(EC.decision_box(alt_decbox_id,1, 3))
                    .add_if(
                        EC.if_result_equals(3),
                        EF()
                        .add(EC.decision_box(alt_600_id, 0, 2))
                        .add(EC.assign_mem_to_mem(result_addr, temp_addr, 1))
                        .add(EC.add(temp_addr, 4))
                        .add(EC.assign_mem_to_mem(temp_addr, result_addr, 1))
                    ),
                    EF()
                    .add(EC.decision_box(main_decbox_id, 1, 2))
                )
            ).add(EC.pause(0))

            for result, dest in result_dict.items():
                result_func = (
                    EF()
                    .add_if(
                        EC.if_result_equals(result),
                        EF()
                        .add(EC.decision_box(
                            script.add_py_string(
                                f"Travel to {dest.name} for {dest.cost}G? {{linebreak+0}}"
                                "       Yes{linebreak+0}"
                                "       No{null}"
                            ), 1, 2
                        ))
                        .add_if(
                            EC.if_result_equals(1),
                            EF().add_if_else(
                                EC.if_has_gold(dest.cost),
                                EF().add(EC.sub_gold(dest.cost))
                                .add(dest.change_loc_cmd),
                                EF().add(EC.auto_text_box(no_cash_str_id))
                                .add(EC.return_cmd())
                            )
                        )
                    )
                )
                ferry_func.append(result_func)
                script.set_function(
                    obj_id, FID.ACTIVATE, ferry_func
                )


def apply_jets_of_time(
        logic_options: logicoptions.LogicOptions,
        script_manager: ScriptManager
):
    script = script_manager[ctenums.LocID.BLACKBIRD_SCAFFOLDING]
    blackbirdscaffolding.EventMod.add_flight_turn_in(script)


def lock_portals(script_manager: ScriptManager):
    @dataclasses.dataclass()
    class PortalData:
        loc_id: ctenums.LocID
        portal_obj_id: int | None
        activate_obj_id: int

    # Note:
    # The Dark Ages portal is sealed until Lavos falls in prehistory.
    # That is a different locking mechanism which will not conflict.

    portal_data_list = [
        PortalData(ctenums.LocID.TELEPOD_EXHIBIT, 0xA, 0xA),
        PortalData(ctenums.LocID.TRUCE_CANYON_PORTAL, 0xB, 0xB),
        PortalData(ctenums.LocID.GUARDIA_FOREST_DEAD_END, 9, 9),
        PortalData(ctenums.LocID.BANGOR_DOME, 0xB, 0xB),
        PortalData(ctenums.LocID.PROTO_DOME_PORTAL, 0xB, 0xB),
        PortalData(ctenums.LocID.MEDINA_PORTAL, None, 0xD),
        PortalData(ctenums.LocID.MYSTIC_MTN_PORTAL, 0xB, 0xA),
        PortalData(ctenums.LocID.LAIR_RUINS_PORTAL, 8, 9),
        PortalData(ctenums.LocID.DARK_AGES_PORTAL, 0xB, 0xB)
    ]

    portal_load_block = (
        EF()
        .add_if_else(
            EC.if_has_item(ctenums.ItemID.GATE_KEY),
            EF().add(EC.load_npc(ctenums.NpcID.CLOSED_PORTAL)),
            EF().add(EC.load_npc(ctenums.NpcID.SEALED_PORTAL))
        )
    )

    for data in portal_data_list:
        script = script_manager[data.loc_id]

        if data.portal_obj_id is not None:
            pos = script.find_exact_command(
                EC.load_npc(ctenums.NpcID.CLOSED_PORTAL),
                script.get_object_start(data.portal_obj_id)
            )
            script.insert_commands(
                portal_load_block.get_bytearray(), pos
            )
            pos += len(portal_load_block)
            script.delete_commands(pos, 1)

        pos = script.get_function_start(data.activate_obj_id, FID.ACTIVATE)

        sealed_str_id = script.add_py_string(
            "{line break}   Requires Gate Key{null}"
        )
        script.insert_commands(
            EF()
            .add_if_else(
                EC.if_has_item(ctenums.ItemID.GATE_KEY),
                EF(),
                EF()
                .add(EC.auto_text_box(sealed_str_id))
                .add(EC.return_cmd())
            ).get_bytearray(), pos
        )


def apply_logic_tweaks(
        logic_options: logicoptions.LogicOptions,
        script_manager: ScriptManager
):
    if logic_options.hard_lavos_final_boss:
        apply_hard_lavos_end_boss(script_manager)

    if logic_options.boats_of_time:
        apply_boats_of_time(logic_options, script_manager)

    if logic_options.jets_of_time:
        apply_jets_of_time(logic_options, script_manager)

    if logic_options.lock_gates:
        lock_portals(script_manager)

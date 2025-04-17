"""Alter recruitable character for Guardia Prison"""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.strings import ctstrings


def assign_pc_to_spot(
        char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
):
    """
    Assign the given PC to the spot.
    """

    # This is the worst!  We need to visit all of the prison spots and Guardia
    # Castle 1000 and change the default Luccas to something else.
    loc_id_obj_id_dict = {
        ctenums.LocID.PRISON_CATWALKS: 5,
        ctenums.LocID.PRISON_SUPERVISORS_OFFICE: 7,
        ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM: 4,
        ctenums.LocID.PRISON_CELLS: 0x16,
        ctenums.LocID.PRISON_STAIRWELLS: 9,
        ctenums.LocID.PRISON_EXTERIOR: 3
    }

    crono_symbol = b'\x13'
    lucca_symbol = b'\x15'
    recruit_symbol = bytes([0x13 + char_id])
    pc1_symbol = b'\x1B'

    # Update names
    for loc_id in loc_id_obj_id_dict.keys():
        strings = script_man[loc_id].strings
        for ind, ct_string in enumerate(strings):
            ct_string = ct_string.replace(crono_symbol, pc1_symbol).replace(lucca_symbol, recruit_symbol)
            strings[ind] = ct_string

    repl_load_party = EC.load_pc_in_party(char_id)
    repl_load_npc = EC.load_pc_always(char_id)

    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel, 0x7F0250, 0x7F0252
    )

    for loc_id, obj_id in loc_id_obj_id_dict.items():
        script = script_man[loc_id]
        start, end = script.get_function_bounds(obj_id, FID.STARTUP)

        pos = script.find_exact_command(
            EC.load_pc_in_party(ctenums.CharID.LUCCA), start, end
        )
        script.insert_commands(repl_load_party.to_bytearray(), pos)
        pos += len(repl_load_party)
        script.delete_commands(pos, 1)

        if loc_id in (ctenums.LocID.PRISON_SUPERVISORS_OFFICE,
                      ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM):

            pos = script.find_exact_command(
                EC.if_pc_active(ctenums.CharID.LUCCA), start, end)
            script.data[pos+1] = char_id

            pos = script.find_exact_command(
                EC.load_pc_always(ctenums.CharID.LUCCA), pos, end)
            script.insert_commands(repl_load_npc.to_bytearray(), pos)
            pos += len(repl_load_npc)
            script.delete_commands(pos, 1)

            pos = script.find_exact_command(
                EC.if_pc_active(ctenums.CharID.LUCCA), pos, end)
            script.data[pos+1] = char_id

            pos = script.find_exact_command(
                EC.add_pc_to_active(ctenums.CharID.LUCCA)
            )
            script.data[pos+1] = char_id
            script.insert_commands(
                owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED)
                .append(scale_block)
                .add(EC.name_pc(char_id))
                .get_bytearray(), pos)

            pos = script.find_exact_command(
                EC.generic_command(0x80, 0x02), pos   # Weird loadpc version
            )
            script.data[pos+1] = char_id

        if loc_id == ctenums.LocID.PRISON_STAIRWELLS:
            pos = script.get_function_start(7, FID.ARBITRARY_3)
            for _ in range(6):
                pos = script.find_exact_command(
                    EC.if_pc_active(ctenums.CharID.LUCCA)
                )
                script.data[pos+1] = char_id

    # Now change the castle NPC to the recruit.
    script = script_man[ctenums.LocID.GUARDIA_THRONEROOM_1000]
    pos = script.find_exact_command(
        EC.load_npc(ctenums.NpcID.CRONOS_MOM),
        script.get_object_start(0x13)
    )
    script.replace_command_at_pos(pos, EC.load_pc_always(char_id))

    pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.LUCCA))
    script.delete_commands(pos, 1)

    pos = script.find_exact_command(EC.if_mem_op_value(0x7F0222, OP.EQUALS, ctenums.CharID.LUCCA))
    script.delete_jump_block(pos)

    # Now change the party restoration part
    pos = script.find_exact_command(EC.remove_pc_from_active_party(ctenums.CharID.LUCCA))
    script.delete_commands(pos, 1)

    # change old 3rd party member to go reserve
    pos = script.find_exact_command(EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC3,
                                    OP.LESS_OR_EQUAL, 6, 1),)
    for _ in range(7):
        # Change active to reserve
        pos, cmd = script.find_command([0xD3], pos)
        script.data[pos] = 0xD0


def assign_item_to_spot(char_id: ctenums.CharID,
                        script_man: ScriptManager):
    """
    Assign an item instead of a PC to this spot.
    """

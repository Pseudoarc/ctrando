"""Module for modifying forced encounters in the Beast Cave."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_first_battle(script_manager: ScriptManager):
    """Replace the first 2x Beast fight with an interactable object"""

    script = script_manager[ctenums.LocID.BEAST_NEST]
    # print(script.get_function(0, 0))
    # print(EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0))
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0)
    )
    body_st, cmd = script.find_command([0xE7], pos)
    body_end = script.find_exact_command(
        EC.if_mem_op_value(0x7F0218, OP.EQUALS, 0)
    )

    func = EF.from_bytearray(script.data[body_st: body_end])
    func = (
        EF()
        .add(EC.set_object_drawing_status(0xF, True))
        .add(EC.set_object_drawing_status(0x10, True))
    ).append(func)
    script.delete_jump_block(pos)

    for obj_id in (0xF, 0x10):
        pos = script.get_function_start(obj_id, 0)
        script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)

    encounterutils.add_battle_object(script, func)


def unforce_second_battle(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.BEAST_NEST]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0218, OP.EQUALS, 0)
    )
    body_st, cmd = script.find_command([0xE7], pos)
    body_end = script.find_exact_command(
        EC.if_mem_op_value(0x7F021A, OP.EQUALS, 0)
    )

    func = EF.from_bytearray(script.data[body_st: body_end])
    func = (
        EF()
        .add(EC.set_object_drawing_status(0xD, True))
        .add(EC.set_object_drawing_status(0xE, True))
    ).append(func)
    script.delete_jump_block(pos)

    for obj_id in (0xD, 0xE):
        pos = script.get_function_start(obj_id, 0)
        script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)

    encounterutils.add_battle_object(script, func)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_first_battle(script_manager)
    unforce_second_battle(script_manager)
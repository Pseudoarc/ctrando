"""Module for modifying forced encounters in Ocean Palace."""
from ctrando.common import ctenums, memory
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_top_stair_battle(script_manager: ScriptManager):
    """Make the top stairway fight optional."""
    script = script_manager[ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL]
    body = script.get_function(8, FID.ACTIVATE)

    encounterutils.add_battle_object(
        script, body, x_tile=8, y_tile=0xD
    )

    pos, _ = script.find_command([0x12], script.get_object_start(0xF))
    script.delete_jump_block(pos)
    script.delete_jump_block(pos)


def unforce_bottom_stair_battle(script_manager: ScriptManager):
    """Make the bottom stairway fight optional"""
    script = script_manager[ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL]
    body = script.get_function(8, FID.ARBITRARY_1)

    encounterutils.add_battle_object(
        script, body, x_tile=0x18, y_tile=0x6D
    )

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.BITWISE_AND_NONZERO, 0x02),
        script.get_object_start(0xF)
    )
    script.delete_jump_block(pos)
    script.delete_jump_block(pos)


def unforce_button_battles(script_manager: ScriptManager):
    """Make the button battles optional."""

    script = script_manager[ctenums.LocID.OCEAN_PALACE_SIDE_ROOMS]

    switch_objs = (0xB, 0x11)
    trigger_cmds = (
        EC.call_obj_function(8, FID.ACTIVATE, 1, FS.HALT),
        EC.call_obj_function(8, FID.ARBITRARY_0, 1, FS.HALT)
    )
    flags = (
        memory.FlagData(0x7F0162, 0x04),
        memory.FlagData(0x7F0162, 0x02)
    )
    coords = (
        (0x10, 0xE),
        (0x27, 0x37)
    )

    for switch_obj, trigger_cmd, coord in zip(switch_objs, trigger_cmds, coords):
        body = (
            EF()
            .add(EC.set_object_drawing_status(switch_obj, False))
            .add(trigger_cmd)
            .add(EC.set_object_drawing_status(switch_obj, True))
        )

        x_tile, y_tile = coord
        battle_obj_id = encounterutils.add_battle_object(
            script, body, x_tile=x_tile, y_tile=y_tile, default_show=False
        )

        pos = script.find_exact_command(trigger_cmd, script.get_object_start(0xB))
        script.replace_command_at_pos(pos, EC.set_object_drawing_status(battle_obj_id, True))


def make_first_elevator_battle_optional(script_manager: ScriptManager):
    """Make the battle at the top of the elevator optional."""
    script = script_manager[ctenums.LocID.OCEAN_PALACE_SOUTHERN_ACCESS_LIFT]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.GREATER_THAN, 0x12)
    )
    body_st = script.find_exact_command(EC.set_explore_mode(False), pos)
    body_end = script.find_exact_command(EC.jump_forward(0), body_st)

    body = EF().from_bytearray(script.data[body_st:body_end])
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    encounterutils.add_battle_object(script, body)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_top_stair_battle(script_manager)
    unforce_bottom_stair_battle(script_manager)
    unforce_button_battles(script_manager)
    make_first_elevator_battle_optional(script_manager)
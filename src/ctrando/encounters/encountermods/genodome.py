"""Module for modifying forced encounters in Geno Dome."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_charger_proto_4_battle(script_manager: ScriptManager):
    """Make the battle near the charger optional."""

    script = script_manager[ctenums.LocID.GENO_DOME_LABS]
    body = script.get_function(0x1F, FID.ARBITRARY_0)

    pos = script.find_exact_command(EC.return_cmd(),
                              script.get_object_start(0x27)) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    # Trigger is on one of the protos
    # pos = script.find_exact_command(
    #     EC.if_mem_op_value(0x7F0214, OP.LESS_THAN, 0x1E),
    #     script.get_object_start(0x27)
    # )
    # script.delete_jump_block(pos)
    # script.delete_commands_range()


def unforce_labs_laserguard_fight(script_manager: ScriptManager):
    """Make the laserguards guarding the switches optional."""
    script = script_manager[ctenums.LocID.GENO_DOME_LABS]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.LESS_THAN, 0x0F),
        script.get_object_start(0x2A)
    )

    script.delete_jump_block(pos)

    body = (
        EF().add(EC.call_obj_function(0x1F, FID.ARBITRARY_1, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    encounterutils.add_battle_object(script, body, x_tile=0xD, y_tile=0xC)


def unforce_robot_access_fight(script_manager: ScriptManager):
    """Make the fight on the non-conveyor skip path optional."""

    script = script_manager[ctenums.LocID.GENO_DOME_ROBOT_ELEVATOR_ACCESS]
    pos = script.find_exact_command(EC.return_cmd(),
                                    script.get_object_start(0xB)) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF().add(EC.call_obj_function(0, FID.ARBITRARY_0, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    encounterutils.add_battle_object(script, body, x_tile=0x37, y_tile=0x23)


def unforce_labs_laser_back_fight(script_manager: ScriptManager):
    """Make the fight near the conveyor switch optional."""
    script = script_manager[ctenums.LocID.GENO_DOME_LABS]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.GREATER_THAN, 0x2A),
        script.get_object_start(0x2E)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(0x1F, FID.ARBITRARY_2, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    encounterutils.add_battle_object(script, body, x_tile=0x2C, y_tile=0xE)


def unforce_2x_laserguard_fight(script_manager: ScriptManager):
    """Make the pre-Atropos laserguard fight optional."""
    script = script_manager[ctenums.LocID.GENO_DOME_MAINFRAME]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.GREATER_THAN, 0x25),
        script.get_object_start(0xF)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(0xC, FID.ACTIVATE, 1, FS.CONT))
        .add(EC.return_cmd())
    )
    script.set_function(0xF, FID.ACTIVATE, body)
    script.link_function(0x10, FID.ACTIVATE, 0xF, FID.ACTIVATE)

    #
    # encounterutils.add_battle_object(script, body, x_tile=0x28, y_tile=0x26)


def unforce_post_atropos_laserguards(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.GENO_DOME_MAINFRAME]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.GREATER_THAN, 0x06),
        script.get_object_start(0x11)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(0xC, FID.TOUCH, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    script.set_function(0x11, FID.ACTIVATE, body)
    for obj_id in range(0x12, 0x17):
        script.link_function(obj_id, FID.ACTIVATE, 0x11, FID.ACTIVATE)


    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.GREATER_THAN, 0x06),
        script.get_object_start(0x17)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 1, FS.CONT))
        .add(EC.return_cmd())
    )
    script.set_function(0x17, FID.ACTIVATE, body)
    for obj_id in range(0x18, 0x1D):
        script.link_function(obj_id, FID.ACTIVATE, 0x17, FID.ACTIVATE)

    # encounterutils.add_battle_object(script, body, x_tile=0x9, y_tile=0x18)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_charger_proto_4_battle(script_manager)
    unforce_labs_laserguard_fight(script_manager)
    unforce_robot_access_fight(script_manager)
    unforce_labs_laser_back_fight(script_manager)
    unforce_2x_laserguard_fight(script_manager)
    unforce_post_atropos_laserguards(script_manager)
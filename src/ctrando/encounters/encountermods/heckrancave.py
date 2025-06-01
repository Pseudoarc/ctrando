"""Module for modifying forced encounters in Heckran Cave."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def remove_intro_fight(script_manager: ScriptManager):
    """Make the entrance fight activatable instead of forced."""
    script = script_manager[ctenums.LocID.HECKRAN_CAVE_ENTRANCE]

    start_pos = script.find_exact_command(
        EC.move_party(0x24, 0x16, 0x23, 0x19, 0x26, 0x18)
    )

    end_cmd = EC.set_bit(0x7F01A3, 0x02)

    del_start_pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F01A3, OP.BITWISE_AND_NONZERO, 0x02, 1, 0)
    )
    end_pos = script.find_exact_command(end_cmd) + len(end_cmd)

    func = EF.from_bytearray(script.data[start_pos: end_pos])
    script.delete_commands_range(del_start_pos, end_pos)

    # If an enemy calls their own battle, it can cause errors with future
    # battles.  Make a new object to contain the battle commands.
    new_battle_obj = script.append_empty_object()
    script.set_function(new_battle_obj, FID.STARTUP,
                        EF().add(EC.return_cmd()).add(EC.end_cmd()))
    script.set_function(new_battle_obj, FID.ACTIVATE, func)

    hench_objs = [8, 9]

    for obj_id in hench_objs:
        script.set_function(
            obj_id, FID.ACTIVATE,
            EF().add(EC.call_obj_function(new_battle_obj, FID.ACTIVATE,
                                          5, FS.CONT)).add(EC.return_cmd())
        )
        # script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))


def unforce_jinn_bottle_1(script_manager: ScriptManager):
    """Alter the coordinate check on the first Jinn Bottle fight."""

    script = script_manager[ctenums.LocID.HECKRAN_CAVE_ENTRANCE]

    coord_check_cmd = EC.if_mem_op_value(0x7F0212, OP.EQUALS, 9, 1, 0)
    pos = script.find_exact_command(coord_check_cmd)

    jinn_object = 0xA

    # Objects can't call their own battles.  Put the battle commands here.
    battle_block = (
        EF()
        .add(EC.call_obj_function(jinn_object, FID.ACTIVATE, 6,
                                  FS.HALT))
        .add(EC.assign_val_to_mem(0x80, 0x7E2A21, 1))
        .add(EC.generic_command(0xD8, 0x10, 0x40))  # battle
    )

    new_func = (
        EF()
        .add_if(
            EC.if_mem_op_value(0x7F0212, OP.LESS_OR_EQUAL, 7, 1, 0),
            EF().add_if(
                EC.if_mem_op_value(0x7F0214, OP.LESS_OR_EQUAL, 0x16, 1, 0),
                battle_block
            )
        )
    )
    script.delete_jump_block(pos)
    script.insert_commands(new_func.get_bytearray(), pos)

    # Remove redundant battle commands from the jinn bottle.
    pos = script.get_function_start(jinn_object, FID.ACTIVATE)
    pos = script.find_exact_command(EC.assign_val_to_mem(0x80, 0x7E2A21, 1),
                                    pos)
    script.delete_commands(pos, 2)


def unforce_four_tempurite_battle(script_manager: ScriptManager):
    """Add an extra object to trigger the forced 4x tempurite fight."""

    encounterutils.unforce_coordinate_loop_battle(
        script_manager, ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER,
        0x7F01AE, 0x04,
        0, 0
    )


def unforce_two_tempurite_battle(script_manager: ScriptManager):
    """
    Add an extra object to trigger the 2x tempurite fight.

    Note: This fight is only forced when exploring the side path.
    """
    encounterutils.unforce_coordinate_loop_battle(
        script_manager, ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER,
        0x7F01AE, 0x02, 0, 0
    )


def unforce_four_rolypoly_battle(script_manager: ScriptManager):
    """Add an extra object to trigger the 4x rolypoly fight."""

    encounterutils.unforce_coordinate_loop_battle(
        script_manager, ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS,
        0x7F01AE, 0x10, 0, 0
    )


def unforce_three_rolypoly_battle(script_manager: ScriptManager):
    """Add an extra object to trigger the 3x rolypoly side path fight."""

    encounterutils.unforce_coordinate_loop_battle(
        script_manager, ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS,
        0x7F01AE, 0x08, 0, 0
    )


def unforce_sidepath_cavebat_battle(script_manager: ScriptManager):
    '''Modify the object that triggers the sidepath cavebat fight.'''

    script = script_manager[ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS]

    obj_id = 2

    extra_battle_init = (
        EF()
        .add(EC.call_obj_function(0x12, FID.ARBITRARY_0, 6, FS.CONT))
        .add(EC.call_obj_function(0x13, FID.ARBITRARY_0, 6, FS.CONT))
        .add(EC.call_obj_function(0x14, FID.ARBITRARY_0, 6, FS.CONT))
    )

    pos, _ = script.find_command([0], script.get_function_start(obj_id, 0))
    script.insert_commands(
        EF()
        .add(EC.load_npc(0x72))
        .add(EC.generic_command(0x84, 0x00)).get_bytearray(), pos)

    battle_func = extra_battle_init.append(
        script.get_function(obj_id, FID.TOUCH))

    script.set_function(obj_id, FID.ACTIVATE, battle_func)
    script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))


def apply_all_encounter_reduction(script_manager: ScriptManager):
    """Remove all supported Heckran Cave encounters"""
    remove_intro_fight(script_manager)
    unforce_jinn_bottle_1(script_manager)
    unforce_four_tempurite_battle(script_manager)
    unforce_two_tempurite_battle(script_manager)
    unforce_four_rolypoly_battle(script_manager)
    unforce_three_rolypoly_battle(script_manager)
    unforce_sidepath_cavebat_battle(script_manager)

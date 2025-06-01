"""Remove most forced encounters from the Black Omen."""
from ctrando.common import ctenums, ctrom, memory
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def make_entrance_battle_optional(script_manager: ScriptManager):
    """Make the 2x Incognito battle optional."""

    script = script_manager[ctenums.LocID.BLACK_OMEN_1F_ENTRANCE]

    pos = script.find_exact_command(
        EC.if_flag(memory.Flags.BLACK_OMEN_1F_INCOGNITO_BATTLE)
    )
    body_st, _ = script.find_command([0xE7], pos)
    body_end = script.find_exact_command(EC.jump_back(0), body_st)
    body = EF().from_bytearray(script.data[body_st:body_end])
    script.delete_commands_range(pos, body_end)

    body = (
        EF()
        .add(EC.set_object_drawing_status(0xD, True))
        .add(EC.set_object_drawing_status(0xE, True))
    ).append(body)

    flag = memory.Flags.BLACK_OMEN_1F_INCOGNITO_BATTLE
    encounterutils.add_battle_object(
        script, body, flag.value.address, flag.value.bit
    )

    for obj_id in (0xD, 0xE):
        pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(obj_id))
        script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)


def make_entrance_1f_battles_optional(script_manager: ScriptManager):
    """Modify 2x Goon fight."""

    script = script_manager[ctenums.LocID.BLACK_OMEN_1F_WALKWAY]

    # Goon fight
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0)
    )
    body_st, _ = script.find_command([0xE7], pos)
    body_end = script.find_exact_command(
        EC.if_mem_op_value(0x7F0218, OP.EQUALS, 0),
        body_st
    )

    body = EF.from_bytearray(script.data[body_st:body_end])
    script.delete_commands_range(pos, body_end)

    encounterutils.add_battle_object(script, body)


    # top fight
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F021A, OP.EQUALS, 0)
    )
    body_st, _ = script.find_command([0xE7], pos)
    body_end = script.find_exact_command(EC.jump_back(0), body_st)

    body = EF.from_bytearray(script.data[body_st:body_end])
    script.delete_commands_range(pos, body_end)

    encounterutils.add_battle_object(script, body)


def make_first_panel_fights_optional(script_manager: ScriptManager):
    """Make the first two panel fights optional"""

    script = script_manager[ctenums.LocID.BLACK_OMEN_1F_DEFENSE_CORRIDOR]

    flags = (memory.Flags.BLACK_OMEN_1F_PANELS_BOTTOM,
             memory.Flags.BLACK_OMEN_1F_PANELS_TOP)
    body_st_cmd_id = 0xE8
    end_cmd = EC.set_explore_mode(True)

    for flag in flags:
        pos = script.find_exact_command(EC.if_flag(flag))
        body_st, _ = script.find_command([body_st_cmd_id], pos)
        body_end = script.find_exact_command(end_cmd, body_st) + 2

        body = EF().from_bytearray(script.data[body_st:body_end])
        encounterutils.add_battle_object(script, body, flag.value.address, flag.value.bit)

    pos = script.find_exact_command(EC.return_cmd()) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

def make_boss_orb_optional(script_manager: ScriptManager):
    """Make the one unskippable boss orb optional."""

    script = script_manager[ctenums.LocID.BLACK_OMEN_1F_STAIRWAY]

    script.set_function(
        0x11, FID.ARBITRARY_0,
        EF()
        .add(EC.play_animation(7))
        .add(EC.call_obj_function(8, FID.ARBITRARY_0, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(0x11))
    script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)
    pos, _ = script.find_command([0x12], pos)
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.set_own_drawing_status(True))
        .add(EC.call_obj_function(0x11, FID.ARBITRARY_0, 1, FS.HALT))
    )

    encounterutils.add_battle_object(script, body, x_tile=7, y_tile=6)


def make_metal_mute_optional(script_manager: ScriptManager):
    """Make the 2x metal mute 2x flyclops battle optional."""
    script = script_manager[ctenums.LocID.BLACK_OMEN_3F_WALKWAY]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020C, OP.GREATER_THAN, 3),
        script.get_object_start(0xD)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)


def make_first_tubster_optional(script_manager: ScriptManager):
    """Make the first tubster fight optional."""
    script = script_manager[ctenums.LocID.BLACK_OMEN_47F_ROYAL_PATH]

    pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(9)) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body_st, _ = script.find_command([0xE7], pos)
    body_end, cmd = script.find_command([0xD8], body_st)
    body_end += len(cmd)

    body = EF().from_bytearray(script.data[body_st:body_end])
    body.add(EC.return_cmd())

    script.set_function(9, FID.ACTIVATE, body)


def make_first_cybot_optional(script_manager: ScriptManager):
    """Make first 2x Cybot fight optional."""
    script = script_manager[ctenums.LocID.BLACK_OMEN_47F_ROYAL_BALLROOM]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x27),
        script.get_object_start(0xB)
    )

    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(8, FID.ACTIVATE, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    for obj_id in (0xB, 0xC):
        script.set_function(obj_id, FID.ACTIVATE, body)


def make_royal_assembly_battle_optional(script_manager: ScriptManager):
    """Make the 2x goon, flyclops battle optional."""

    script = script_manager[ctenums.LocID.BLACK_OMEN_47F_ROYAL_ASSEMBLY]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020C, OP.EQUALS, 0x28),
        script.get_object_start(0xE)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    script.set_function(
        0xE, FID.ACTIVATE,
        EF()
        .add(EC.call_obj_function(8, FID.TOUCH, 1, FS.CONT))
        .add(EC.return_cmd())
    )


def make_royal_promenade_battle_optional(script_manager: ScriptManager):
    """Make 2x flyclops, tubster, battle optional."""

    script = script_manager[ctenums.LocID.BLACK_OMEN_47F_ROYAL_PROMENADE]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.LESS_THAN, 0x2D),
        script.get_object_start(0x0C)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)
    pos = script.find_exact_command(EC.set_explore_mode(False), pos) + 2
    pos = script.find_exact_command(EC.set_explore_mode(False), pos)
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(8, FID.ACTIVATE, 1, FS.HALT))
    )

    encounterutils.add_battle_object(script, body, x_tile=0x37, y_tile=0x2F)


def make_astral_walkway_97f_fights_optional(script_manager: ScriptManager):
    """Synchrite fight and 2x tubster fight"""

    script = script_manager[ctenums.LocID.BLACK_OMEN_97F_ASTRAL_WALKWAY]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x2A),
        script.get_object_start(0xB)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(8, FID.ACTIVATE, 1, FS.CONT))
    )

    encounterutils.add_battle_object(script, body, 0x7F0161, 0x01,
                                     0xE, 0x2A)

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.GREATER_THAN, 8),
        script.get_object_start(0x13)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    script.set_function(
        0x13, FID.ACTIVATE,
        EF()
        .add(EC.call_obj_function(8, FID.ARBITRARY_0, 1, FS.CONT))
        .add(EC.return_cmd())
    )


def make_terra_mutant_panels_optional(script_manager: ScriptManager):
    """Make the panels before Terra Mutant optional."""
    script = script_manager[ctenums.LocID.BLACK_OMEN_TERRA_MUTANT]

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x15),
        script.get_object_start(0xB)
    )
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    body = (
        EF()
        .add(EC.call_obj_function(8, FID.ACTIVATE, 1, FS.CONT))
    )

    encounterutils.add_battle_object(
        script, body,
        0x7F015A, 0x02,
        x_tile=8, y_tile=0x17
    )


def apply_all_encounter_reduction(script_manager: ScriptManager):
    make_entrance_battle_optional(script_manager)
    make_entrance_1f_battles_optional(script_manager)
    make_first_panel_fights_optional(script_manager)
    make_boss_orb_optional(script_manager)
    make_metal_mute_optional(script_manager)
    make_first_tubster_optional(script_manager)
    make_first_cybot_optional(script_manager)
    make_royal_assembly_battle_optional(script_manager)
    make_royal_promenade_battle_optional(script_manager)
    make_astral_walkway_97f_fights_optional(script_manager)
    make_terra_mutant_panels_optional(script_manager)
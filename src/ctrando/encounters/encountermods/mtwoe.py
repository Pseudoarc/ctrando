"""Module for modifying forced encounters in Mt. Woe."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def get_loop_body(script: LocationEvent, obj_id: int):
    """
    Replace a coordinate-check loop with a battle object.
    The loop has format:
        if coord check(s):
            battle body
            goto END
        goto checks
        END
    """
    pos, cmd = script.find_command(EC.fwd_jump_commands,
                                   script.get_object_start(obj_id))
    pos += len(cmd)

    while True:
        cmd = get_command(script.data, pos)
        if cmd.command not in EC.fwd_jump_commands:
            break
        pos += len(cmd)

    body_st = pos
    body_end = script.find_exact_command(EC.end_cmd(), body_st)

    move_party_pos, move_party_cmd = script.find_command([0xD9], body_st, body_end)
    x_tile, y_tile = encounterutils.tile_coords_from_moveparty(move_party_cmd)

    body = EF.from_bytearray(script.data[body_st: body_end])

    return body


def apply_all_encounter_reduction(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.MT_WOE_MIDDLE_EASTERN_FACE]
    encounterutils.add_battle_object(
        script, get_loop_body(script, 2), replace_obj_id=2, npc_id=ctenums.NpcID.CRONOS_MOM
    )

    script = script_manager[ctenums.LocID.MT_WOE_WESTERN_FACE]
    encounterutils.add_battle_object(
        script, get_loop_body(script, 1), replace_obj_id=1
    )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 2), replace_obj_id=2
    )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 3), replace_obj_id=3
    )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 4), replace_obj_id=4
    )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 5), replace_obj_id=5
    )

    # encounterutils.add_battle_object(
    #     script, get_loop_body(script, 6), replace_obj_id=6
    # )

    encounterutils.add_battle_object(
        script, get_loop_body(script, 7), replace_obj_id=7
    )

    script = script_manager[ctenums.LocID.MT_WOE_LOWER_EASTERN_FACE]
    encounterutils.add_battle_object(
        script, get_loop_body(script, 1), replace_obj_id=1
    )
    # encounterutils.add_battle_object(
    #     script, get_loop_body(script, 2), replace_obj_id=2
    # )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 3), replace_obj_id=3
    )
    encounterutils.add_battle_object(
        script, get_loop_body(script, 4), replace_obj_id=4
    )
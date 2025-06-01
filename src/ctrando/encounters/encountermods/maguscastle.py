"""Module for modifying forced encounters in Castle Magus."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_hall_of_aggression(script_manager: ScriptManager):
    """Make the Hall of Aggression fights optional."""
    script = script_manager[ctenums.LocID.MAGUS_CASTLE_HALL_AGGRESSION]


    hench_objs = (0x0F, 0x11, 0x13, 0x15)
    move_y_coords = (0x33, 0x27, 0x1B, 0x0F)

    hide_func = EF()

    for obj_id, y_coord in zip(hench_objs, move_y_coords):
        hide_func.add(EC.set_object_drawing_status(obj_id, False))
        hide_func.add(EC.set_object_drawing_status(obj_id+1, False))

        pos = script.find_exact_command(EC.return_cmd(),
                                        script.get_object_start(obj_id)) + 1
        script.insert_commands(EC.end_cmd().to_bytearray(), pos)

        body_st = script.find_exact_command(EC.play_song(0x45), pos)
        own_fn_pos, cmd = script.find_command([0x03], body_st)
        own_fn_end = own_fn_pos
        for _ in range(4):
            own_fn_end += len(get_command(script.data, own_fn_end))
        # own_fn_end, _ = script.find_command([0x12], own_fn_pos+len(cmd))
        own_fn = EF.from_bytearray(script.data[own_fn_pos:own_fn_end])
        own_fn.add(EC.return_cmd())

        if obj_id == 0x15:
            facing_check = script.find_exact_command(
                EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
                own_fn_end
            )
            script.delete_commands(facing_check, 1)

        facing_check = script.find_exact_command(
            EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
            own_fn_end
        )
        script.delete_commands(facing_check, 1)
        pos = script.find_exact_command(EC.jump_forward(0), facing_check)
        script.delete_commands(pos, 3)

        script.delete_commands(own_fn_pos, 4)
        script.insert_commands(
            EC.call_obj_function(obj_id, FID.ARBITRARY_0, 4, FS.CONT)
            .to_bytearray(), own_fn_pos
        )
        body_end = script.find_exact_command(EC.jump_back(0), body_st)
        body = EF.from_bytearray(script.data[body_st:body_end])

        body = (
            EF()
            .add(EC.set_object_drawing_status(obj_id, True))
            .add(EC.set_object_drawing_status(obj_id+1, True))
        ).append(body)

        # print(body)
        # input()
        script.set_function(obj_id, FID.ARBITRARY_0, own_fn)
        encounterutils.add_battle_object(script, body, x_tile=0x27, y_tile=y_coord)

    pos = script.get_object_start(0)
    script.insert_commands(hide_func.get_bytearray(), pos)

def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_hall_of_aggression(script_manager)
    # pass
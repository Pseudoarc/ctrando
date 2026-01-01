"""Alter starter character."""
from ctrando.base import openworldutils as owu

from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.recruits import recruitassign as ra

def assign_pc_to_spot(
        char_ids: list[ctenums.CharID],
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False,
):
    """
    Assign a PC to the Starter spot.
    """

    if not char_ids:
        raise ValueError("Empty Starters")

    recruit_fn = EF()
    for char_id in char_ids:

        scale_block = (
            EF().add(EC.set_level(char_id, min_level))
            .add(EC.set_tech_level(char_id, min_techlevel))
        )
        if scale_gear:
            scale_block.append(ra.get_dynamic_gear_function(char_id))
        recruit_fn.append(scale_block)
        recruit_fn.append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))

    bitmask = 0
    for char_id in char_ids:
        bitmask |= (0x80 >> char_id)

    # Most of the work has been done in the openworld mod
    script = script_man[ctenums.LocID.LOAD_SCREEN]

    recruit_obj = script.append_empty_object()
    script.set_function(recruit_obj, FID.STARTUP,
                        EF().add(EC.return_cmd()).add(EC.end_cmd()))
    script.set_function(
        recruit_obj, FID.ACTIVATE,
        recruit_fn
        .add(EC.assign_val_to_mem(
            bitmask,
            memory.Memory.RECRUITED_CHARACTERS, 1)
        ).append(scale_block)
        .add(EC.return_cmd())
    )
    # A little clunky.  Finds the second big memset command and writes
    # the char_id instead of 0 (Crono) to the first byte of the payload.
    pos, cmd = script.find_command([0x4E])
    pos, cmd = script.find_command([0x4E], pos+len(cmd))

    for ind, char_id in enumerate(char_ids):
        script.data[pos + ind + 6] = char_id

    pos = script.find_exact_command(
        EC.name_pc(ctenums.CharID.CRONO)
    )
    script.delete_commands(pos, 1)

    repl_cmds = EF()
    for char_id in char_ids:
        repl_cmds.add(EC.name_pc(char_id))
    repl_cmds.add(EC.call_obj_function(recruit_obj, FID.ACTIVATE, 4, FS.HALT))
    script.insert_commands(repl_cmds.get_bytearray(), pos)


    script = script_man[ctenums.LocID.CRONOS_ROOM]

    for char_id in char_ids[1:]:
        obj_id = char_id + 1
        # print(char_id, obj_id)
        # st = script.get_function_start(obj_id, FID.STARTUP)
        # end = script.get_object_start(obj_id+1)
        # func = EF.from_bytearray(script.data[st:end])
        # print(func)
        # input()
        pos = script.find_exact_command(
            EC.script_speed(0x10),
            script.get_object_start(obj_id)
        )
        script.delete_commands(pos, 2)

    if len(char_ids) > 1:
        pos = script.find_exact_command(
            EC.set_explore_mode(True),
            script.get_function_start(1, FID.ARBITRARY_2)
        )
        script.insert_commands(EC.party_follow().to_bytearray(), pos)
"""Remove most forced encounters from Lab 32."""
from ctrando.common import ctenums, ctrom, memory
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def apply_all_encounter_reduction(script_manager: ScriptManager):
    """Remove 2 mutant fights and the ghosts."""

    script =script_manager[ctenums.LocID.LAB_32]
    start_cmds = (
        # EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0),
        EC.if_mem_op_value(0x7F0214, OP.EQUALS, 0),
        EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0),
        EC.if_mem_op_value(0x7F0218, OP.EQUALS, 0),
    )

    body_st_cmd = EC.set_explore_mode(False)

    body_end_cmds = (
        # EC.if_mem_op_value(0x7F0214, OP.EQUALS, 0),
        EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0),
        EC.jump_back(0),
        EC.jump_back(0),
    )

    pos = script.get_object_start(0)
    for start_cmd, body_end_cmd in zip(start_cmds, body_end_cmds):

        start = script.find_exact_command(start_cmd, pos)
        body_st = script.find_exact_command(body_st_cmd, start)
        body_end = script.find_exact_command(body_end_cmd, body_st)

        body = EF().from_bytearray(script.data[body_st:body_end])
        script.delete_jump_block(start)

        encounterutils.add_battle_object(script, body)



    pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(1)) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)
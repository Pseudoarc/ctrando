"""Module for modifying forced encounters in Denadoro Mts."""
from ctrando.common import ctenums, ctrom
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)


def remove_south_face_sleeping_ogan_fight(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.DENADORO_SOUTH_FACE]
    x_addr, y_addr = 0x7F0214, 0x7F0216

    pos, cmd = script.find_command([0x12], script.get_function_start(1, FID.STARTUP))
    repl_cmd = EC.if_mem_op_value(y_addr, OP.EQUALS, 0x13)

    script.replace_jump_cmd(pos, repl_cmd)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    remove_south_face_sleeping_ogan_fight(script_manager)
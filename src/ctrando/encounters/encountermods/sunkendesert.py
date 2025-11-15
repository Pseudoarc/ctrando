"""Module for modifying forced encounters in the Magic Cave."""
from ctrando.common import ctenums, memory
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils

def apply_all_encounter_reduction(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.SUNKEN_DESERT_PARASITES]

    flag = memory.Flags.SUNKEN_DESERT_MIDDLE_BATTLE
    flag_data = flag.value
    pos = script.find_exact_command(EC.if_flag(flag))

    func_st = script.find_exact_command(EC.play_song(0x45), pos)
    func_end = script.find_exact_command(EC.set_explore_mode(True), func_st) + 2
    func = EF.from_bytearray(script.data[func_st:func_end])

    script.delete_jump_block(pos)
    script.delete_jump_block(pos)

    encounterutils.add_battle_object(
        script, func, flag_data.address, flag_data.bit
    )
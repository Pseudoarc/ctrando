"""Module for modifying forced encounters in the Proto Dome."""
from ctrando.common import ctenums, memory
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils

def apply_all_encounter_reduction(script_manager: ScriptManager):
    script = script_manager[ctenums.LocID.PROTO_DOME]

    # By default the second encounter is turned off until the first is taken.
    pos = script.find_exact_command(
        EC.disable_script_processing(0x13)
    )
    script.delete_commands(pos, 1)

    pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(0x10))
    script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)

    # Disable the normal battle object
    pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(0xF)) + 1
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    pos = script.find_exact_command(EC.set_explore_mode(False), pos)
    end = script.find_exact_command(EC.enable_script_processing(0x13), pos)

    battle_func = EF.from_bytearray(script.data[pos: end])

    second_battle_objs = (0x14, 0x15, 0x16, 0x17)
    pre_battle = EF()
    pre_battle.add(EC.set_object_drawing_status(0x10, True))
    battle_func = pre_battle.append(battle_func)

    flag_data = memory.Flags.PROTO_DOME_ENTRANCE_BATTLE.value
    encounterutils.add_battle_object(
        script, battle_func, flag_data.address, flag_data.bit,
    )

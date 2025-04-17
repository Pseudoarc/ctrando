"""Alter starter character."""
from ctrando.base import openworldutils as owu

from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.recruits import recruitassign as ra

def assign_pc_to_spot(
        char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False,
):
    """
    Assign a PC to the Milennial Fair spot.
    """

    scale_block = (
        EF().add(EC.set_level(char_id, min_level))
        .add(EC.set_tech_level(char_id, min_techlevel))
    )
    if scale_gear:
        scale_block.append(ra.get_dynamic_gear_function(char_id))

    # Most of the work has been done in the openworld mod
    script = script_man[ctenums.LocID.LOAD_SCREEN]

    # A little clunky.  Finds the second big memset command and writes
    # the char_id instead of 0 (Crono) to the first byte of the payload.
    pos, cmd = script.find_command([0x4E])
    pos, cmd = script.find_command([0x4E], pos+len(cmd))
    script.data[pos + 6] = char_id

    pos = script.find_exact_command(
        EC.name_pc(ctenums.CharID.CRONO)
    )
    repl_cmd = EC.name_pc(char_id)
    script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()
    script.insert_commands(
        owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED)
        .add(EC.assign_val_to_mem(
            0x80 >> char_id,
            memory.Memory.RECRUITED_CHARACTERS, 1)
        ).append(scale_block)
        .get_bytearray(), pos
    )


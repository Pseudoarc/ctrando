"""Remove most forced encounters from the Dactyl Nest."""
from ctrando.common import ctenums, ctrom
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventfunction import EventFunction as EF

def unforce_first_battle(script_manager: ScriptManager):
    """Remove the extra fight trigger beyond the Cave Ape/Shist"""

    script = script_manager[ctenums.LocID.DACTYL_NEST_LOWER]
    x_addr, y_addr= 0x7F0216, 0x7F0218
    pos = script.get_function_start(0x10, FID.STARTUP)
    pos = script.find_exact_command(
        EC.if_mem_op_value(y_addr, OP.EQUALS, 0x32)
    )
    script.delete_jump_block(pos)


def unforce_avian_rex_battle(script_manager: ScriptManager):
    """Have the fight trigger by touching Avian Rexes."""

    script = script_manager[ctenums.LocID.DACTYL_NEST_LOWER]

    script.set_function(0x10, FID.TOUCH, EF().add(EC.return_cmd()))
    # trigger_obj = 0x10
    # pos = script.get_function_start(trigger_obj, FID.STARTUP)
    # script.insert_commands(
    #     EF()
    #     .add(EC.load_npc(ctenums.NpcID.RED_FLAME))
    #     .add(EC.set_solidity_properties(False, False))
    #     .get_bytearray(),
    #     pos
    # )
    #
    # pos = script.find_exact_command()
    #
    # pos = script.find_exact_command(EC.return_cmd(),
    #                                 script.get_function(trigger_obj, FID.ACTIVATE))
    # script.insert_commands(EC.remove_object(trigger_obj).to_bytearray(), pos)
    # avian_rex_ids = 0x11, 0x12
    # battle_func = (
    #     EF()
    #     .add(EC.call_obj_function(0x08, FID.TOUCH, 4, FS.CONT))
    #     .add(EC.return_cmd())
    # )
    # for obj_id in avian_rex_ids:
    #     script.set_function(obj_id, FID.TOUCH)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_first_battle(script_manager)
    unforce_avian_rex_battle(script_manager)
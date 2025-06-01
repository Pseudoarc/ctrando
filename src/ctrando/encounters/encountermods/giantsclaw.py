"""Module for modifying forced encounters in Giant's Claw."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_entrance_battles(script_manager: ScriptManager):
    """Make 3x Lizardactyl battle optional."""
    script = script_manager[ctenums.LocID.GIANTS_CLAW_ENTRANCE]
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0214, OP.EQUALS, 0)
    )

    body_st = script.find_exact_command(EC.set_explore_mode(False), pos)
    body_end, cmd = script.find_command([0xD8], body_st)
    body_end += len(cmd)

    body = EF().from_bytearray(script.data[body_st:body_end])

    script.delete_jump_block(pos)
    encounterutils.add_battle_object(script, body)


def fix_pit_battles(script_manager: ScriptManager):
    """Reduce range on pit encounters."""
    script = script_manager[ctenums.LocID.ANCIENT_TYRANO_LAIR]

    # pos = script.find_exact_command(
    #     EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x1C)
    # )
    # script.replace_jump_cmd(
    #     pos,
    #     EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x1F)
    # )

    pos = script.get_object_start(1)
    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x10), pos
    )
    script.replace_jump_cmd(
        pos,
        EC.if_mem_op_value(0x7F020E, OP.EQUALS, 0x0D)
    )

def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_entrance_battles(script_manager)
    fix_pit_battles(script_manager)
    # pass
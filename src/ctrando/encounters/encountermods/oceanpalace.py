"""Module for modifying forced encounters in Ocean Palace."""
from ctrando.common import ctenums
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils


def unforce_top_stair_battle(script_manager: ScriptManager):
    """Make the top stairway fight optional."""
    script = script_manager[ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL]
    body = script.get_function(8, FID.ACTIVATE)

    encounterutils.add_battle_object(
        script, body, x_tile=8, y_tile=0xD
    )

    pos, _ = script.find_command([0x12], script.get_object_start(0xF))
    script.delete_jump_block(pos)
    script.delete_jump_block(pos)


def unforce_bottom_stair_battle(script_manager: ScriptManager):
    """Make the bottom stairway fight optional"""
    script = script_manager[ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL]
    body = script.get_function(8, FID.ARBITRARY_1)

    encounterutils.add_battle_object(
        script, body, x_tile=0x18, y_tile=0x6D
    )

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.BITWISE_AND_NONZERO, 0x02),
        script.get_object_start(0xF)
    )
    script.delete_jump_block(pos)
    script.delete_jump_block(pos)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_top_stair_battle(script_manager)
    unforce_bottom_stair_battle(script_manager)
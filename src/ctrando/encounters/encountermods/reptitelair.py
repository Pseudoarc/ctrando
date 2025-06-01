"""Remove most forced encounters from the Reptite Lair."""
from ctrando.common import ctenums, ctrom
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.encounters import encounterutils

def unforce_tunnel_battles(script_manager: ScriptManager):
    """Remove the fight trigger from the tunnel objects."""

    script = script_manager[ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B1]
    hole_ids = (0x14, 0x15, 0x16, 0x17, 0x18)
    special_hole_id = 0x17
    for obj_id in hole_ids:
        start = script.get_function_start(obj_id, FID.ACTIVATE)
        script.delete_jump_block(start)  # Perhaps verify the exact command
        if obj_id == special_hole_id:
            script.delete_jump_block(start)

    script = script_manager[ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B2]
    # Object 0x12 has all of the battle commands.
    # Normal Holes: 0x14, 0x15, 0x16, 0x18
    # Hole dug by Evilweevil: 0x17

    # Normal holes are easy.  Delete the conditional block at the very start.
    # The block is checking for whether a fight has occurred.
    # Is the EvilWeevil hole different?  Seems not.
    for obj_id in range(0x15, 0x19):
        start = script.get_function_start(obj_id, FID.ACTIVATE)
        script.delete_jump_block(start)  # Perhaps verify the exact command


def unforce_pre_nizbel_battle(script_manager: ScriptManager):
    """Replace withe Megasaur + 2x Reptite battle with a flame object."""

    script = script_manager[ctenums.LocID.REPTITE_LAIR_TUNNEL]

    # Remove the trigger from reptite in object 0xE
    pos, _ = script.find_command([0x22], script.get_object_start(0xE))
    script.insert_commands(EC.end_cmd().to_bytearray(), pos)

    pos += 1
    end = script.find_exact_command(EC.return_cmd(), pos)
    script.delete_commands_range(pos, end)

    body = script.get_function(0x13, FID.ARBITRARY_0)
    body = (
        EF()
        .add(EC.set_object_drawing_status(0xE, True))
        .add(EC.set_object_drawing_status(0xF, True))
        .add(EC.set_object_drawing_status(0x10, True))
    ).append(body)

    encounterutils.add_battle_object(
        script, body, x_tile=8, y_tile=0x19,
        flag_addr=0x7F0158, flag_bit=0x01
    )


    for obj_id in (0xE, 0xF, 0x10):
        pos = script.get_object_start(obj_id)
        script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)


def apply_all_encounter_reduction(script_manager: ScriptManager):
    unforce_tunnel_battles(script_manager)
    unforce_pre_nizbel_battle(script_manager)
"""Some functions for handling basic encounter patterns."""
from typing import Optional

from ctrando.common import ctenums, ctrom
from ctrando.locations import eventcommand
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import  FunctionID as FID, LocationEvent
from ctrando.locations.eventcommand import (
    EventCommand as EC, Operation as OP, FuncSync as FS
)
from ctrando.locations.eventfunction import EventFunction as EF


def tile_coords_from_moveparty(move_party_cmd: EC) -> tuple[int, int]:
    real_args = [arg & 0x7F for arg in move_party_cmd.args]

    x_tile = round((real_args[0] + real_args[2] + real_args[4]) / 3)
    y_tile = round((real_args[1] + real_args[3] + real_args[5]) / 3)

    return x_tile, y_tile


def add_battle_object(
        script: LocationEvent,
        activate_function: EF,
        flag_addr: Optional[int] = None, flag_bit: Optional[int] = None,
        x_tile: Optional[int] = None, y_tile: Optional[int] = None,
        npc_id: int = 0x72,  # small flame
        replace_obj_id: int | None = None
) -> int:
    """
    Adds an object that removes itself after activate is called.

    Params:
      - activate_function: EF
          The new object's activate function.  Will be surrounded by commands
          to hide/re    move the object.
      - flag_addr: Optional[int], flag_bit: Optional[int]
          Object will only load when flag_addr & flag_bit is not set.  If None
          then the object will load on every map load (for repeatable fights).
      - x_tile: Optional[int], y_tile: Optional[int]
          Tile coordinates of the new object.  If None, will scan the activate
          function for a party_move command and place the object at the average
          coordinate.  Will raise ValueError if this fails.
      - npc_id: int
          The ID of the NPC to use for this object.  Defaults to small flame.
    Returns id of new object.
    """

    if x_tile is None or y_tile is None:
        cmd_inds = activate_function.find_command([0xD9])
        if not cmd_inds:
            raise ValueError("No coords and no party move.")

        cmd_ind = cmd_inds[0]
        cmd = activate_function.commands[cmd_ind]
        real_args = [arg & 0x7F for arg in cmd.args]

        if x_tile is None:
            x_tile = round((real_args[0] + real_args[2] + real_args[4]) / 3)
        if y_tile is None:
            y_tile = round((real_args[1] + real_args[3] + real_args[5]) / 3)

    if replace_obj_id is None:
        obj_id = script.append_empty_object()
    else:
        obj_id = replace_obj_id

    startup_ef = (
        EF()
        .add(EC.load_npc(npc_id))
        .add(EC.set_object_coordinates_tile(x_tile, y_tile))
        .add(EC.generic_command(0x84, 0x00))
    )

    if flag_addr is not None and flag_bit is not None:
        startup_ef = (
            EF()
            .add_if_else(
                EC.if_mem_op_value(flag_addr, OP.BITWISE_AND_NONZERO,
                                   flag_bit, 1, 0),
                EF(),
                startup_ef
            )
        )
    startup_ef.add(EC.return_cmd()).add(EC.end_cmd())
    script.set_function(obj_id, FID.STARTUP, startup_ef)

    activate_ef = (
        EF()
        .add(EC.set_own_drawing_status(False))
        .append(activate_function)
        .add(EC.remove_object(obj_id))
    )

    script.set_function(obj_id, FID.ACTIVATE, activate_ef)

    touch_ef = EF().add(EC.return_cmd())
    script.set_function(obj_id, FID.TOUCH, touch_ef)

    return obj_id


def unforce_coordinate_loop_battle(
        script_manager: ScriptManager,
        loc_id: ctenums.LocID,
        flag_addr: int, flag_bit: int,
        loop_obj: int, loop_fn: int,
        object_sprite_id: int = 0x72
        ) -> int:
    """
    Create an interactable object that replaces a battle.  Returns the id of
    the new object created.  The script pattern is to have an infinite loop
    with the following piece inside:

    if flag is set:
        goto SKIP
    if coordinates in range:
        some setup commands including a party move
        battle
        set flag
    [SKIP]

    This function will place an interactable object with coordinates based on
    the party move command.  Interacting will trigger the fight by calling the
    same commands as were found in the loop.
    """
    script = script_manager[loc_id]

    flag_cmd = EC.if_mem_op_value(flag_addr, OP.BITWISE_AND_NONZERO,
                                  flag_bit, 1, 0)
    start = script.get_function_start(loop_obj, loop_fn)
    end = script.get_function_end(loop_obj, loop_fn)

    flag_pos = script.find_exact_command(flag_cmd, start, end)
    startup_commands = script.get_jump_block(flag_pos)
    script.delete_jump_block(flag_pos)

    if startup_commands.commands[-1].command != 0x10:
        raise ValueError("No goto at startup block end")

    startup_commands.delete_at_index(-1)  # Remove final goto.

    block_pos = flag_pos

    battle_block = script.get_jump_block(block_pos)
    script.delete_jump_block(block_pos)

    while battle_block.commands[0].command in EC.fwd_jump_commands:
        battle_block.delete_at_index(0)

    return add_battle_object(script, battle_block, flag_addr, flag_bit,
                             npc_id=object_sprite_id)

"""
Module containing functions useful for openworld conversion.
"""
import typing
from typing import Literal, Optional

from ctrando.locations import locationevent
from ctrando.common import ctenums, memory
from ctrando.common.ctenums import ItemID
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    Operation as OP,
    get_command,
    FuncSync as FS,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import (
    LocationEvent as Event,
    FunctionID as FID,
    CommandNotFoundException,
)
from ctrando.common.memory import Flags, Memory


def add_exploremode_to_partyfollows(script: Event):
    """
    Make sure that every partyfollow is preceded or followed by an exploremode on.
    """
    pos: Optional[int] = script.get_object_start(0)
    prev_pos: Optional[int] = None
    exploremode_cmd = EC.set_explore_mode(True)
    partyfollow_cmd = EC.party_follow()

    cmd_bytes = partyfollow_cmd.to_bytearray() + exploremode_cmd.to_bytearray()

    while True:
        prev_pos = pos
        pos = script.find_exact_command_opt(partyfollow_cmd, pos)

        if pos is None:
            break

        prev_cmd = get_command(script.data, prev_pos)
        next_cmd = get_command(script.data, pos + 1)

        if prev_cmd == exploremode_cmd or next_cmd == exploremode_cmd:
            pos += 1
            continue

        # This might not be needed.  After insertion, the exploremode is before the
        # partyfollow.  This just rearranges those three bytes.
        script.insert_commands(exploremode_cmd.to_bytearray(), pos)
        script.data[pos : pos + len(cmd_bytes)] = cmd_bytes
        pos += 3


def append_portal_half_object(
    script: Event,
    portal_map_x_px: int,
    portal_map_y_px: int,
    half: Literal["top", "bottom"],
) -> int:
    """
    Add either a portal top or bottom half object to the script.  Returns the
    object id of the appended object.
    """

    ret_ind = script.append_empty_object()
    npc_id = 0x57 if half == "top" else 0x58

    script.set_function(
        ret_ind,
        FID.STARTUP,
        EF()
        .add(EC.load_npc(npc_id))
        .add(EC.set_object_coordinates_auto(portal_map_x_px, portal_map_y_px))
        .add(EC.generic_command(0x8E, 0x04))
        .add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd())
        .add(EC.end_cmd()),
    )

    script.set_function(ret_ind, FID.ACTIVATE, EF().add(EC.return_cmd()))

    script.set_function(
        ret_ind,
        FID.ARBITRARY_0,
        EF()
        .add(EC.set_own_drawing_status(True))
        .add(EC.pause(0.25))
        .add(get_command(bytes.fromhex("888D0800E44C84404330")))
        .add(get_command(bytes.fromhex("88301E02")))
        .add(EC.return_cmd()),
    )
    script.set_function(
        ret_ind,
        FID.ARBITRARY_1,
        EF()
        .add(get_command(bytes.fromhex("8800")))
        .add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd()),
    )

    return ret_ind


def insert_pc_object(
    script: Event, pc_id: ctenums.CharID, copy_pc_obj_id: int, insert_obj_id: int
):
    """
    Add character pc_id to the script as object insert_obj_id.  The object in
    copy_pc_obj_id is used as a base with the load commands altered.
    """

    script.insert_copy_object(copy_pc_obj_id, insert_obj_id)
    pos, end = script.get_function_bounds(insert_obj_id, FID.STARTUP)

    load_pc_in_party_cmd_ids = [
        EC.load_pc_in_party(pc_id).command for pc_id in ctenums.CharID
    ]

    while pos < end:
        cmd = get_command(script.data, pos)
        if cmd.command in load_pc_in_party_cmd_ids:
            script.data[pos] = EC.load_pc_in_party(pc_id).command
        elif cmd.command in (0x80, 0x81):  # indexed load in party
            script.data[pos + 1] = pc_id

        pos += len(cmd)


def insert_portal(
        script: Event,
        portal_screen_x: int,
        portal_screen_y: int,
        portal_map_x_px: int,
        portal_map_y_px: int,
        anim_fid: FID,
        change_loc_cmd: EC,
        activate_flag: Optional[memory.Flags] = None
) -> int:
    """
    Insert a portal at the given coordinates.  The three objects will be inserted
    at the end of the script.
    - First object: Closed portal (has activate function)
    - Next two objects: open portal halves to show when activated
    Two separate coordinates must be specified:
    - The portal coordinates (portal_screen_x and portal_screen_y)
    """

    load_fn = EF()
    if activate_flag is not None:
        load_fn = (
            EF().add_if_else(
                EC.if_not_flag(activate_flag),
                EF().add(EC.load_npc(ctenums.NpcID.SEALED_PORTAL)),
                EF().add(EC.load_npc(ctenums.NpcID.CLOSED_PORTAL))
            )
        )
    else:
        load_fn = EF().add(EC.load_npc(ctenums.NpcID.CLOSED_PORTAL))

    ret_ind = script.append_empty_object()
    script.set_function(
        ret_ind,
        FID.STARTUP,
        # .add(EC.load_npc(ctenums.NpcID.CLOSED_PORTAL))
        load_fn
        .add(EC.set_object_coordinates_auto(portal_map_x_px, portal_map_y_px))
        .add_if(
            EC.if_mem_op_value(memory.Memory.PORTAL_STATUS, OP.EQUALS, 1),
            EF().add(EC.set_own_drawing_status(False)),
        )
        .add(EC.return_cmd())
        .add(EC.end_cmd()),
    )

    tile_x = (portal_map_x_px - 0x8) // 0x10
    tile_y = (portal_map_y_px) // 0x10

    change_loc_cmd.command = 0xDD

    activate_gate = EF()
    if activate_flag is not None:
        activate_gate = (
            EF().add_if(
                EC.if_not_flag(activate_flag),
                EF().add(EC.return_cmd())
            )
        )

    script.set_function(
        ret_ind,
        FID.ACTIVATE,
        activate_gate
        .add(EC.set_explore_mode(False))
        .add(EC.play_sound(5))
        .add(EC.pause(0.5))
        .add(EC.play_song(0))
        .add(EC.set_own_drawing_status(False))
        .add(EC.open_portal_scene(portal_screen_x, portal_screen_y))
        .add(EC.call_obj_function(ret_ind + 1, FID.ARBITRARY_0, 6, FS.SYNC))
        .add(EC.call_obj_function(ret_ind + 2, FID.ARBITRARY_0, 6, FS.SYNC))
        .add(
            EC.move_party(
                tile_x,
                tile_y | 0x80,
                (tile_x - 1),
                (tile_y - 1) | 0x80,
                (tile_x + 1),
                (tile_y - 1) | 0x80,
            )
        )
        .add(EC.call_pc_function(0, anim_fid, 1, FS.CONT))
        .add(EC.call_pc_function(1, anim_fid, 1, FS.CONT))
        .add(EC.call_pc_function(2, anim_fid, 1, FS.CONT))
        .add(EC.pause(0.75))
        .add(EC.play_sound(0x70))
        .add(EC.generic_command(0xFF, 0x91))
        .add(EC.pause(1))
        .add(EC.call_obj_function(ret_ind + 1, FID.ARBITRARY_1, 6, FS.SYNC))
        .add(EC.call_obj_function(ret_ind + 2, FID.ARBITRARY_1, 6, FS.HALT))
        .add(EC.assign_val_to_mem(1, memory.Memory.PORTAL_STATUS, 1))
        .add(EC.play_song(0x37))
        .add(change_loc_cmd)
        .add(EC.generic_command(0xFF, 0x81))
        .add(EC.return_cmd()),
    )
    script.set_function(ret_ind, FID.TOUCH, EF().add(EC.return_cmd()))

    append_portal_half_object(script, portal_map_x_px, portal_map_y_px - 0x10, "top")
    append_portal_half_object(script, portal_map_x_px, portal_map_y_px - 0x10, "bottom")

    return ret_ind


def insert_portal_complete(
        script: Event,
        portal_screen_x: int,
        portal_screen_y: int,
        portal_map_x_px: int,
        portal_map_y_px: int,
        anim_fid: FID,
        return_fid: FID,
        pc_obj_start_id: int,
        change_loc_cmd: EC,
        activate_flag: Optional[memory.Flags] = None
) -> int:
    """
    Insert a portal and its return function.
    """

    # Set up PC functions
    for obj_id in range(pc_obj_start_id, pc_obj_start_id + 7):
        script.set_function(
            obj_id,
            anim_fid,
            EF()
            .add(EC.generic_command(0x8E, 0))
            .add(EC.static_animation(0x60))
            .add(EC.return_cmd()),
        )

        script.set_function(
            obj_id,
            return_fid,
            EF()
            .add(EC.generic_command(0x8E, 0x80))
            .add(EC.static_animation(0x60))
            .add(EC.return_cmd()),
        )

    # add the portal objects
    closed_portal_id = insert_portal(
        script,
        portal_screen_x,
        portal_screen_y,
        portal_map_x_px,
        portal_map_y_px,
        anim_fid,
        change_loc_cmd,
        activate_flag
    )

    pos = script.find_exact_command(EC.return_cmd()) + 1
    script.insert_commands(
        get_portal_exit_func(
            portal_screen_x,
            portal_screen_y,
            portal_map_x_px,
            portal_map_y_px,
            closed_portal_id,
            anim_fid,
            return_fid,
        ).get_bytearray(),
        pos,
    )

    return closed_portal_id


def get_write_pc_ids_to_script_memory(script_addr: int) -> EF:
    """
    Returns an EventFunction which writes PC1, 2, and 3 to the six bytes
    starting at script_addr in [0x7F0200, 0x7F0400).
    """

    if not (0x7F0200 <= script_addr < (0x7F0400-6)):
        raise ValueError("Not in script memory.")

    if script_addr & 2 != 0:
        raise ValueError("Script address must be even.")

    ret_fn = (
        EF()
        .add(EC.assign_mem_to_mem(Memory.ACTIVE_PC1, script_addr, 1))
        .add(EC.assign_mem_to_mem(Memory.ACTIVE_PC2, script_addr + 2, 1))
        .add(EC.assign_mem_to_mem(Memory.ACTIVE_PC3, script_addr + 4, 1))
    )

    return ret_fn


def get_can_eot_func(
    temp_addr: int,
    can_eot_addr: int,
) -> EF:
    """
    Return an EventFunction which determines whether EoT is available.
    Result is written (Can == 1, Cannot = 0) to can_eot_addr and uses temp_addr
    for computation.  Both should be script addresses.
    """
    func = (
        EF()
        .add_if(
            EC.if_has_item(ctenums.ItemID.GATE_KEY),
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.RESERVE_PC1, temp_addr, 1))
            .add_if(
                EC.if_mem_op_value(temp_addr, OP.NOT_EQUALS, 0x80),
                EF()
                .add(EC.assign_val_to_mem(1, can_eot_addr, 1))
                .jump_to_label(EC.jump_forward(), "end"),
            ),
        )
        .add_if(
            EC.if_flag(memory.Flags.HAS_EOT_TIMEGAUGE_ACCESS),
            EF().add(EC.assign_val_to_mem(1, can_eot_addr, 1)),
        )
        .set_label("end")
    )

    return func


def get_count_pcs_func(temp_addr: int, num_pcs_addr: int) -> EF:
    """
    Return an EventFunction which computes the number of active PCs and stores it in
    num_pcs_addr.
    """
    func = (
        EF()
        .add(EC.assign_val_to_mem(1, num_pcs_addr, 1))
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2, temp_addr, 1))
        .add_if(
            EC.if_mem_op_value(temp_addr, OP.NOT_EQUALS, 0x80),
            EF().add(EC.add(num_pcs_addr, 1)),
        )
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, temp_addr, 1))
        .add_if(
            EC.if_mem_op_value(temp_addr, OP.NOT_EQUALS, 0x80),
            EF().add(EC.add(num_pcs_addr, 1)),
        )
    )
    return func


def get_has_equipment_func(
    item_id: ctenums.ItemID, result_addr: int, temp_addr: int = 0x7F0300
) -> EF:
    """
    Returns an EventFunction that tests for the presence of an item.
    Assumes result_addr holds a 0. Writes a 1 in result_addr if the item is
    found.
    """

    if item_id in range(ctenums.ItemID.WOOD_SWORD, ctenums.ItemID.HIDE_TUNIC):
        start_addr = 0x7E2629
    elif item_id in range(ctenums.ItemID.HIDE_TUNIC, ctenums.ItemID.HIDE_CAP):
        start_addr = 0x7E2628
    elif item_id in range(ctenums.ItemID.HIDE_CAP, ctenums.ItemID.BANDANA):
        start_addr = 0x7E2627
    elif item_id in range(ctenums.ItemID.BANDANA, ctenums.ItemID.TONIC):
        start_addr = 0x7E262A
    else:
        return EF().add_if(
            EC.if_has_item(item_id), EF().add(EC.assign_val_to_mem(1, result_addr, 1))
        )

    end_label = f"{item_id}{result_addr}"
    ret_fn = EF().add_if(
        EC.if_has_item(item_id),
        EF()
        .add(EC.assign_val_to_mem(1, result_addr, 1))
        .jump_to_label(EC.jump_forward(), end_label),
    )

    cur_addr = start_addr
    for _ in range(7):
        ret_fn.add(EC.assign_mem_to_mem(cur_addr, temp_addr, 1))
        ret_fn.add_if(
            EC.if_mem_op_value(temp_addr, OP.EQUALS, item_id),
            EF()
            .add(EC.assign_val_to_mem(1, result_addr, 1))
            .jump_to_label(EC.jump_forward(), end_label),
        )
        cur_addr += 0x50

    ret_fn.set_label(end_label)
    ret_fn.add(EC.pause(0))  # Otherwise, future appends may move label
    return ret_fn


def get_portal_exit_func(
    portal_screen_x: int,
    portal_screen_y: int,
    portal_map_x_px: int,
    portal_map_y_px: int,
    closed_portal_id: int,
    anim_fid: FID,
    return_fid: FID,
):
    """
    Create a function for returning form a portal which is suitable to insert
    into a script's startup.  Includes the portal status check.
    """

    tile_x = (portal_map_x_px - 0x8) // 0x10
    tile_y = ((portal_map_y_px) // 0x10) | 0x80

    ret_func = EF().add_if(
        EC.if_mem_op_value(memory.Memory.PORTAL_STATUS, OP.EQUALS, 1),
        EF()
        .add(EC.set_explore_mode(False))
        .add(EC.call_pc_function(0, anim_fid, 3, FS.CONT))
        .add(EC.call_pc_function(1, anim_fid, 3, FS.CONT))
        .add(EC.call_pc_function(2, anim_fid, 3, FS.CONT))
        .add(EC.pause(1))
        .add(EC.move_party(tile_x, tile_y, tile_x, tile_y, tile_x, tile_y))
        .add(EC.call_obj_function(closed_portal_id + 1, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.call_obj_function(closed_portal_id + 2, FID.ARBITRARY_0, 4, FS.HALT))
        .add(EC.play_sound(0x70))
        .add(EC.pause(0.125))
        .add(EC.open_portal_scene(portal_screen_x, portal_screen_y))
        .add(EC.pause(1))
        .add(EC.call_pc_function(0, return_fid, 4, FS.HALT))
        .add(EC.call_pc_function(1, return_fid, 4, FS.HALT))
        .add(EC.call_pc_function(2, return_fid, 4, FS.HALT))
        .add(EC.play_sound(0x70))
        .add(EC.generic_command(0xFF, 0x91))
        .add(EC.pause(0.75))
        .add(EC.call_obj_function(closed_portal_id + 1, FID.ARBITRARY_1, 4, FS.CONT))
        .add(EC.call_obj_function(closed_portal_id + 2, FID.ARBITRARY_1, 4, FS.HALT))
        .add(EC.assign_val_to_mem(0, memory.Memory.PORTAL_STATUS, 1))
        .add(
            EC.move_party(
                tile_x, tile_y + 1, tile_x - 1, tile_y - 1, tile_x + 1, tile_y - 1
            )
        )
        .add(EC.party_follow())
        .add(EC.set_explore_mode(True))
        .add(EC.set_object_drawing_status(closed_portal_id, True)),
    )
    return ret_func


def add_default_treasure_string(script: Event) -> int:
    """
    Put the standard "Got 1 {item} ... " string into a script.  Returns the
    index of the inserted string.
    """

    return script.add_py_string(
        "{line break}Got 1 {item}!{line break}" "{itemdesc}{null}"
    )


def get_add_item_block_function(
    item_id: ctenums.ItemID,
    treasure_flag: typing.Optional[memory.Flags] = None,
    got_item_string_index: typing.Optional[int] = None,
) -> EF:
    block = (
        EF()
        .add(EC.assign_val_to_mem(item_id, 0x7F0200, 1))
        .add(EC.add_item_memory(0x7F0200))
    )

    if treasure_flag is not None:
        block.add(EC.set_flag(treasure_flag))

    if got_item_string_index is not None:
        block.add((EC.auto_text_box(got_item_string_index)))

    return block


def insert_add_item_block(
    script: Event,
    pos: int,
    item_id: ctenums.ItemID,
    treasure_flag: typing.Optional[memory.Flags] = None,
    got_item_string_index: typing.Optional[int] = None,
):
    """
    Add the given item to inventory and display the treasure text.
    """

    if got_item_string_index is None:
        got_item_string_index = script.add_py_string(
            "{line break}Got 1 {item}!{line break}" "{itemdesc}{null}"
        )

    block = (
        EF()
        .add(EC.assign_val_to_mem(item_id, 0x7F0200, 1))
        .add(EC.add_item_memory(0x7F0200))
    )

    if treasure_flag is not None:
        block.add(EC.set_flag(treasure_flag))

    block.add(EC.auto_text_box(got_item_string_index))

    script.insert_commands(block.get_bytearray(), pos)


def remove_next_dialogue_command(
    script: Event, pos: int, pause_duration_secs: float = 0.125
):
    pause_tics = round(pause_duration_secs * 0x10)
    pause_cmd = EC.generic_command(0xAD, pause_tics)
    pos, cmd = script.find_command([0xC1, 0xC2, 0xBB], pos)
    script.data[pos : pos + len(cmd)] = pause_cmd.to_bytearray()


def remove_dialog_from_function(
    script: Event,
    obj_id: int,
    func_id: FID,
    pause_duration_secs: float = 0.125,
    max_num_replacements: Optional[int] = None,
):
    """
    Replace some or dialog in a function with pauses.  Should only be called
    on normal (not linked) or it will likely remove more dialog than planned.
    """

    if max_num_replacements is None:
        num_replacements = -1
    elif max_num_replacements <= 0:
        raise ValueError

    pos, end = script.get_function_bounds(obj_id, func_id)

    # Force the two-byte pause instead of some of the one-byte alternatives
    num_ticks = int(0x10 * pause_duration_secs)
    repl_cmd = EC.generic_command(0xAD, num_ticks)

    while pos < end:
        pos, _ = script.find_command_opt(EC.str_commands, pos, end)

        if pos is None:
            break

        script.data[pos : pos + 2] = repl_cmd.to_bytearray()
        max_num_replacements -= 1

        # If None was provided, num_replacements starts negative and never hits 0
        if max_num_replacements == 0:
            break


def storyline_to_flag(script: Event, flag_dict: dict[int, Optional[Flags]]):
    """
    Convert storyline < X to if_not_flag(flag_dict[X]) in a script.
    """
    pos: Optional[int] = script.get_object_start(0)
    while True:
        pos, cmd = script.find_command_opt(
            [
                0x18,  # if storyline lt
                # 0x12,  # if mem op value
            ],
            pos,
        )

        if pos is None:
            break

        if cmd.command == 0x18:
            storyline_val = cmd.args[0]
            if storyline_val in flag_dict:
                flag = flag_dict[storyline_val]
                if flag is None:
                    script.delete_commands(pos, 1)
                else:
                    repl_cmd = EC.if_not_flag(flag)
                    script.replace_jump_cmd(pos, repl_cmd)
            else:
                pos += len(cmd)

        # print(f'{pos:04X}: {cmd}')


def remove_item_pause(
    script: Event, start_pos: int, end_pos: Optional[int] = None,
        flag: Optional[memory.Flags] = None
):
    """
    Remove the exploremode modification when picking up an item in the given region.
    Only guaranteed to work if a single item pickup is in the region.
    """

    set_flag_pos: Optional[int] = None
    add_item_pos: Optional[int] = None

    if end_pos is None:
        end_pos = script.find_exact_command(EC.set_explore_mode(True), start_pos)

    if flag is not None:
        set_flag_cmd = EC.set_flag(flag)
    else:
        set_flag_cmd = None

    pos = start_pos
    while pos < end_pos:
        cmd = get_command(script.data, pos)

        if cmd == EC.set_explore_mode(False):
            # Set any exploremodes to be On instead of Off
            script.data[pos + 1] = 1
        elif cmd.command in (0xC7, 0xCA):  # Add item
            if add_item_pos is None:
                add_item_pos = pos
            else:
                raise ValueError("Multiple add item commands")
        elif cmd.command == 0x65:
            if set_flag_cmd is None or set_flag_cmd == cmd:
                if set_flag_pos is None:
                    set_flag_cmd = cmd
                    set_flag_pos = pos
                else:
                    raise ValueError("Multiple Flags set")

        pos += len(cmd)

    if set_flag_cmd is None or set_flag_pos is None:
        raise CommandNotFoundException("Couldn't find flag setting command")

    if add_item_pos is None:
        raise CommandNotFoundException("Couldn't find add item command")

    if set_flag_pos > add_item_pos:
        script.delete_commands(set_flag_pos, 1)
        script.insert_commands(set_flag_cmd.to_bytearray(), add_item_pos)


def make_safe_pc_func_call(func_id: FID, priority: int, char_mem_st: int) -> EF:
    """
    Call each PC's func_id with given priority.  Cont/Halt depending on
    whether PC exists.
    """
    # This doesn't work unless the function being called is basically
    # the same for all PCs.  Probably we should just call cont on PC2
    # and 3 and Half on PC1 for the same effect.
    ret_fn = EF().add_if_else(
        # If PC2 is  empty
        EC.if_mem_op_value(char_mem_st + 2, OP.GREATER_THAN, 6),
        EF().add(
            # Call PC1 with Halt
            EC.call_pc_function(0, func_id, priority, FS.HALT)
        ),
        EF()
        .add(
            # Call PC1 with Cont
            EC.call_pc_function(0, func_id, priority, FS.CONT)
        )
        .add_if_else(
            # IF PC3 is empty
            EC.if_mem_op_value(char_mem_st + 4, OP.GREATER_THAN, 6),
            # Call PC2 with Halt
            EF().add(EC.call_pc_function(1, func_id, priority, FS.HALT)),
            # Call PC2 with cont and PC3 with Halt
            EF()
            .add(EC.call_pc_function(1, func_id, priority, FS.CONT))
            .add(EC.call_pc_function(2, func_id, priority, FS.HALT)),
        ),
    )
    return ret_fn


def get_epoch_set_block(
        epoch_map: ctenums.LocID,
        epoch_x_coord: Optional[int] = None,
        epoch_y_coord: Optional[int] = None,
        require_flight_to_move: bool = True,
        require_epoch_to_move: bool = True

) -> EF:
    """
    Returns an EventFunction which sets the Epoch map and (optionally) coordinates.
    """

    ret_block = EF().add(EC.assign_val_to_mem(epoch_map, memory.Memory.EPOCH_MAP_LO, 2))

    coord_set_block = EF()

    if epoch_x_coord is not None:
        coord_set_block.add(
            EC.assign_val_to_mem(epoch_x_coord, memory.Memory.EPOCH_X_COORD_LO, 2)
        )
    if epoch_y_coord is not None:
        coord_set_block.add(
            EC.assign_val_to_mem(epoch_y_coord, memory.Memory.EPOCH_Y_COORD_LO, 2)
        )

    if require_flight_to_move:
        coord_set_block = EF().add_if(
            EC.if_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT), coord_set_block
        )

    ret_block.append(coord_set_block)
    if require_epoch_to_move:
        ret_block = (
            EF().add_if(
                EC.if_flag(memory.Flags.EPOCH_OBTAINED_LOC),
                ret_block
            )
        )

    return ret_block


def modify_if_not_charge(
    script: Event, pos: int, check_pendant_charge_addr: int
) -> int:
    """
    Change the if command at the given position to be "if pendant is not charged"
    returns the new position of the if command
    """
    script.replace_jump_cmd(
        pos, EC.if_mem_op_value(check_pendant_charge_addr, OP.EQUALS, 0)
    )

    new_block = EF().add_if_else(
        EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE),
        EF().add(EC.assign_val_to_mem(1, check_pendant_charge_addr, 1)),
        EF().add(EC.assign_val_to_mem(0, check_pendant_charge_addr, 1)),
    )
    script.insert_commands(
        new_block.get_bytearray(),
        pos,
    )
    pos += len(new_block)
    return pos


def update_charge_chest_base_loc(
    script: Event,
    obj_id: int,
    check_pendant_charge_addr: int,
):
    try:
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xA5),
            script.get_function_start(obj_id, FID.ACTIVATE),
        )

        pos = modify_if_not_charge(script, pos, check_pendant_charge_addr)
    except locationevent.CommandNotFoundException:
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0xA5),
            script.get_function_start(obj_id, FID.ACTIVATE),
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE))

    pos, _ = script.find_command([0xCA], pos)
    reward = script.data[pos + 1]
    new_block = (
        EF()
        .add(EC.assign_val_to_mem(reward, 0x7F0200, 1))
        .add(EC.add_item_memory(0x7F0200))
    )
    script.insert_commands(new_block.get_bytearray(), pos)
    pos += len(new_block)
    script.delete_commands(pos, 1)

    got_item_str_id = add_default_treasure_string(script)
    text_pos, cmd = script.find_command([0xBB, 0xC1], pos)
    script.data[text_pos + 1] = got_item_str_id

    pos = script.find_exact_command_opt(
        EC.assign_val_to_mem(reward, 0x7F0200, 1),
        pos, text_pos
    )
    if pos is not None:
        script.delete_commands(pos, 1)


def update_charge_chest_charge_loc(
    script: Event,
    obj_id: int,
    check_pendant_charge_addr: int,
):
    try:
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xA5),
            script.get_function_start(obj_id, FID.ACTIVATE),
        )

        pos = modify_if_not_charge(script, pos, check_pendant_charge_addr)
        cmd = get_command(script.data, pos)
        pos += len(cmd) + cmd.args[-1] - 1  # Jump past the not charged block
    except locationevent.CommandNotFoundException:
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, 0xA5),
            script.get_function_start(obj_id, FID.ACTIVATE),
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE))

    got_item_str_id = add_default_treasure_string(script)
    for _ in range(2):
        add_item_pos, _ = script.find_command([0xCA], pos)
        reward = script.data[add_item_pos + 1]

        mem_set_pos = script.find_exact_command_opt(
            EC.assign_val_to_mem(reward, 0x7F0200, 1), pos
        )
        if mem_set_pos is not None:
            script.delete_commands(mem_set_pos, 1)
            if mem_set_pos < add_item_pos:
                add_item_pos -= 3

        textbox_pos, cmd = script.find_command([0xBB, 0xC1], pos)
        script.delete_commands(textbox_pos, 1)
        if textbox_pos < add_item_pos:
            add_item_pos -= len(cmd)

        new_block = (
            EF()
            .add(EC.assign_val_to_mem(reward, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(add_default_treasure_string(script)))
        )
        script.insert_commands(new_block.get_bytearray(), add_item_pos)
        add_item_pos += len(new_block)
        script.delete_commands(add_item_pos, 1)
        pos = add_item_pos


def update_add_item(script: Event, pos: int, update_text: bool = True):
    """
    Replace the add_item command with an add item from memory.
    Also change the *existing* textbox to default item text.
    """

    text_pos, _ = script.find_command([0xBB, 0xC1, 0xC2], pos)
    if update_text:
        script.delete_commands(text_pos, 1)

    item_pos, _ = script.find_command([0xCA], pos)
    item_id = script.data[item_pos + 1]

    # Remove possible extra set item mem command
    set_pos = script.find_exact_command_opt(
        EC.assign_val_to_mem(item_id, 0x7F0200, 1), pos, text_pos
    )
    if set_pos is not None:
        script.delete_commands(set_pos, 1)
        if set_pos < item_pos:
            item_pos -= len(EC.assign_val_to_mem(item_id, 0x7F0200, 1), pos, text_pos)
    script.delete_commands(item_pos, 1)

    new_block = (
        EF()
        .add(EC.assign_val_to_mem(item_id, 0x7F0200, 1))
        .add(EC.add_item_memory(0x7F0200))
    )

    song_pos, song_cmd = script.find_command_opt([0xEC], pos, text_pos)
    if song_pos is not None:
        new_block.add(song_cmd)
        ins_pos = song_pos
    else:
        ins_pos = item_pos

    if update_text:
        new_block.add(
            EC.auto_text_box(add_default_treasure_string(script))
        )
    script.insert_commands(new_block.get_bytearray(), ins_pos)
    if song_pos is not None:
        ins_pos += len(new_block)
        script.delete_commands(ins_pos, 1)


def get_increment_addr(addr: int, temp_addr: int = 0x7F0302) -> EF:
    """
    Get an EventFunction that increments the given address in memory.
    """

    ret_fn = (
        EF()
        .add(EC.assign_mem_to_mem(addr, temp_addr, 1))
        .add(EC.increment_mem(temp_addr))
        .add(EC.assign_mem_to_mem(temp_addr, addr, 1))
    )

    return ret_fn


def get_increment_quest_complete(temp_addr: int = 0x7F0302) -> EF:
    """
    Get an EventFunction that increments the quests complete counter.
    """

    ret_fn = (
        EF()
        .add(EC.assign_mem_to_mem(memory.Memory.QUESTS_COMPLETED, temp_addr, 1))
        .add(EC.increment_mem(temp_addr))
        .add(EC.assign_mem_to_mem(temp_addr, memory.Memory.QUESTS_COMPLETED, 1))
    )

    return ret_fn


def get_increment_recruit(temp_addr: int = 0x7F0302) -> EF:
    """
    Get an EventFunction that increments the recruit counter.
    """

    ret_fn = (
        EF()
        .add(EC.assign_mem_to_mem(memory.Memory.RECRUITS_OBTAINED, temp_addr, 1))
        .add(EC.increment_mem(temp_addr))
        .add(EC.assign_mem_to_mem(temp_addr, memory.Memory.RECRUITS_OBTAINED, 1))
    )

    return ret_fn


def get_lead_pc_level_tech_level_func(
        level_addr: int = 0x7F0304,
        tech_level_addr: int = 0x7F0306
) -> EF:
    """
    Return an EF that stores the leading PC's level in temp_addr
    """

    ret_fn = (
        EF()
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1, level_addr, 1))
    )
    for pc_id in ctenums.CharID:
        ram_level_addr = 0x7E2600 + 0x50*pc_id + 0x12
        ram_tech_level_addr = 0x7E2830 + pc_id
        ret_fn.add_if(
            EC.if_mem_op_value(level_addr, OP.EQUALS, pc_id),
            EF()
            .add(EC.assign_mem_to_mem(ram_level_addr, level_addr, 1))
            .add(EC.assign_mem_to_mem(ram_tech_level_addr, tech_level_addr, 1))
            .jump_to_label(EC.jump_forward(), "return")
        )

    ret_fn.set_label("return")
    ret_fn.add(EC.pause(0))

    return ret_fn


type GearSpec = tuple[ItemID, ItemID, ItemID, ItemID]

_dynamic_gear_specs: dict[ctenums.CharID, dict[int, GearSpec]] = {
    ctenums.CharID.CRONO: {
        10: (ItemID.WOOD_SWORD, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.BANDANA),
        20: (ItemID.BOLT_SWORD, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.BANDANA),
        30: (ItemID.FLINT_EDGE, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.BANDANA),
        40: (ItemID.AEON_BLADE, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.SPEED_BELT)
    },
    ctenums.CharID.MARLE: {
        10: (ItemID.BRONZE_BOW, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.RIBBON),
        20: (ItemID.LODE_BOW, ItemID.BERET, ItemID.MAIDENSUIT, ItemID.RIBBON),
        30: (ItemID.SAGE_BOW, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.RIBBON),
        40: (ItemID.DREAM_BOW, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.HIT_RING),
    },
    ctenums.CharID.LUCCA: {
        10: (ItemID.AIR_GUN, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.SIGHTSCOPE),
        20: (ItemID.AUTO_GUN, ItemID.BERET, ItemID.MAIDENSUIT, ItemID.SIGHTSCOPE),
        30: (ItemID.RUBY_GUN, ItemID.TABAN_HELM, ItemID.GOLD_SUIT, ItemID.SIGHTSCOPE),
        40: (ItemID.DREAM_GUN, ItemID.TABAN_HELM, ItemID.TABAN_VEST, ItemID.BANDANA)
    },
    ctenums.CharID.ROBO: {
        20: (ItemID.TIN_ARM, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.DEFENDER),
        30: (ItemID.STONE_ARM, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.DEFENDER),
        40: (ItemID.MAGMA_HAND, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.MUSCLERING),
    },
    ctenums.CharID.FROG: {
        10: (ItemID.BRONZEEDGE, ItemID.BRONZEHELM, ItemID.BRONZEMAIL, ItemID.POWERGLOVE),
        20: (ItemID.IRON_SWORD, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.POWERGLOVE),
        30: (ItemID.FLASHBLADE, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.POWERGLOVE),
        40: (ItemID.FLASHBLADE, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.POWERSCARF),
    },
    ctenums.CharID.AYLA: {
        40: (ItemID.FIST_3, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.POWERSCARF),
    },
    ctenums.CharID.MAGUS: {
        40: (ItemID.DARKSCYTHE, ItemID.DOOM_HELM, ItemID.RAVENARMOR, ItemID.AMULET)
    }
}


def get_dynamic_gear_function(
        char_id: ctenums.CharID,
        temp_addr: int = 0x7F0308
) -> EF:

    stat_block_start = 0x7E2600 + 0x50*char_id
    cur_level_offset = 0x12
    equip_offset = 0x27  # Helm, Arm, Weap, Acc
    equip_addr = stat_block_start + equip_offset

    # print(f"{stat_block_start:06X}")
    # print(f"{stat_block_start+cur_level_offset:06X}")
    # input()

    func = (
        EF()
        .add(EC.assign_mem_to_mem(stat_block_start+cur_level_offset,
                                  temp_addr, 1))
    )

    progression = _dynamic_gear_specs[char_id]
    num_entries = len(progression.keys())
    progression = {
        key: progression[key] for key in sorted(progression.keys())
    }

    for ind, (level, (weapon, helm, armor, accessory)) in enumerate(progression.items()):
        first_bytes = (armor << 8) + helm
        second_bytes = (accessory << 8) + weapon
        # assign_func = (
        #     EF()
        #     .add(EC.assign_val_to_mem(first_bytes, equip_addr, 2))
        #     .add(EC.assign_val_to_mem(second_bytes, equip_addr+2, 2))
        # )
        if ind == num_entries-1:
            (
                func
                .add(EC.assign_val_to_mem(first_bytes, equip_addr, 2))
                .add(EC.assign_val_to_mem(second_bytes, equip_addr + 2, 2))
            )
        else:
            func.add_if(
                EC.if_mem_op_value(temp_addr, OP.LESS_THAN, level),
                EF()
                .add(EC.assign_val_to_mem(first_bytes, equip_addr, 2))
                .add(EC.assign_val_to_mem(second_bytes, equip_addr+2, 2))
                .jump_to_label(EC.jump_forward(), "end")
        )

    func.set_label("end")
    func.add(EC.pause(0))

    # print(func)
    # input()

    return func


def get_level_techlevel_set_function(
        pc_id: ctenums.CharID,
        scale_level: bool,
        scale_techlevel: bool,
        scale_gear: bool,
        min_level: int = 1,
        min_techlevel: int = 0,
        temp_level_addr: int = 0x7F0304,
        temp_techlevel_addr: int = 0x7F0306,
):
    # print(scale_level, scale_techlevel, scale_gear)
    # input()
    # print(scale_level, scale_techlevel, min_level, min_techlevel)
    if scale_level or scale_techlevel:
        func = get_lead_pc_level_tech_level_func(temp_level_addr, temp_techlevel_addr)
    else:
        func = EF()

    if not scale_level:
        func.add(EC.assign_val_to_mem(min_level, temp_level_addr, 1))
    elif min_level > 1:
        func.append(
            EF()
            .add_if(
                EC.if_mem_op_value(temp_level_addr, OP.LESS_THAN, min_level),
                EF().add(EC.assign_val_to_mem(min_level, temp_level_addr, 1))
            )
        )

    if not scale_techlevel:
        func.add(EC.assign_val_to_mem(min_techlevel, temp_techlevel_addr, 1))
    elif min_techlevel > 0:
        func.append(
            EF()
            .add_if(
                EC.if_mem_op_value(temp_techlevel_addr, OP.LESS_THAN, min_techlevel),
                EF().add(EC.assign_val_to_mem(min_techlevel, temp_techlevel_addr, 1))
            )
        )

    func.add(EC.set_level_from_memory(pc_id, temp_level_addr))
    func.add(EC.set_tech_level_from_memory(pc_id, temp_techlevel_addr))

    if scale_gear:
        func.append(get_dynamic_gear_function(pc_id, temp_level_addr))

    return func

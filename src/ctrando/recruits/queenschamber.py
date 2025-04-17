"""Alter recruitable character in Guardia Castle 600 Queen's Chamber"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event
from ctrando.recruits import recruitassign as ra


def assign_pc_to_spot(
        char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
):
    """Put a recruitable character in the castle."""
    script = script_man[ctenums.LocID.QUEENS_ROOM_600]

    # Set the recruit's startup to be conditional on the recruit
    recruit_flag = memory.Flags.CASTLE_RECRUIT_OBTAINED
    recruit_startup = (
        EF().add_if_else(
            EC.if_flag(recruit_flag),
            EF().add(EC.load_pc_in_party(char_id)),
            EF().add(EC.load_pc_always(char_id))
        )
        .add(EC.return_cmd())
        .set_label('loop_st')
        .add_if_else(
            EC.if_flag(recruit_flag),
            # if
            EF().add(EC.set_controllable_infinite())
            .jump_to_label(EC.jump_forward(), 'end'),
            # else
            EF().add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'loop_st')
        ).set_label('end')
    )

    # Set recruit-specific functions.
    recruit_obj_id = 1 + char_id
    script.set_function(recruit_obj_id, FID.STARTUP, recruit_startup)

    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    pc3_addr = 0x7F0220
    marle_return_func = script.get_function(2, FID.ARBITRARY_1)
    recruit_join_func = (
        EF().add(EC.play_animation(0x17))
        .add(EC.pause(1))
        .add(EC.set_move_properties(True, True))
        .add(EC.set_move_destination(True, False))
        .add(EC.play_animation(6))
        .add(EC.set_move_speed(0x20))
        .add(EC.move_sprite(0x28, 0x2D))
        .add(EC.pause(1))
        .add(EC.play_animation(0x1D)).add(EC.pause(2))
        .add(EC.play_song(ra.get_char_music(char_id)))
        .add(EC.reset_animation())
        .add(EC.set_move_destination(True, True))
        .add(EC.set_own_facing_pc(0))
        .add(EC.set_move_speed(0x40))
        .add(EC.follow_pc_once(0))
        .add(EC.name_pc(char_id))
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .append(scale_block)
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, pc3_addr, 1))
        .add_if_else(
            EC.if_mem_op_value(pc3_addr, OP.GREATER_THAN, 6),
            # < 3 pc
            EF().add(EC.add_pc_to_active(char_id)),
            # full party
            EF().add(EC.add_pc_to_reserve(char_id))
        ).add(EC.load_pc_in_party(char_id))
        .add(EC.set_flag(recruit_flag)).add(EC.return_cmd())
    )

    script.set_function(recruit_obj_id, FID.ARBITRARY_0, marle_return_func)
    script.set_function(recruit_obj_id, FID.ARBITRARY_1, recruit_join_func)

    # Change the function that controls the return cutscene.
    return_scene_obj = 0x14  # After removal of unused objects.
    pos = script.get_object_start(return_scene_obj)

    # Remove the command to hide the objects
    pos = script.find_exact_command(EC.remove_object(return_scene_obj))
    script.delete_commands(pos, 3)

    pos = script.find_exact_command(
        EC.call_obj_function(2, FID.ARBITRARY_1, 4, FS.CONT), pos
    )
    repl_cmd = EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_0,
                                    4, FS.CONT)
    script.data[pos: pos+len(repl_cmd)] = repl_cmd.to_bytearray()

    pos = script.find_exact_command(
        EC.call_obj_function(3, FID.ARBITRARY_0, 5, FS.CONT),
        pos
    )
    script.delete_commands(pos, 4)

    pos = script.find_exact_command(
        EC.call_obj_function(2, FID.ARBITRARY_4, 4, FS.HALT),
        pos
    )
    end = script.find_exact_command(EC.party_follow())

    # You have to delete most of the old block before the new otherwise you
    # get an error for a jump being too long.
    script.delete_commands_range(pos, end)

    new_block = (
        EF().add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_1,
                                      4, FS.HALT))
        # You need the party switch to happen outside of the PC object.
        # Otherwise, the object goes dead if the new recruit is not active.
        .add_if(
            # pc3_addr does not auto-update, so it's set from before.
            EC.if_mem_op_value(pc3_addr, OP.LESS_THAN, 7),
            EF().add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        )
        .add(EC.reset_bit(0x7F00A1, 0x04))  # Would re-trigger recruit scene
        .add(EC.set_flag(recruit_flag))
        .add(EC.break_cmd())
        .add(EC.party_follow())
        .add(EC.set_controllable_infinite())
        .add(EC.return_cmd())
    )

    script.insert_commands(new_block.get_bytearray(), pos)
    script.delete_commands(pos+len(new_block), 1)

    add_spoiler_object(script, char_id)

def add_spoiler_object(script: Event,
                       recruit_char_id: ctenums.CharID):
    """
    Add an object that will warp out to spoil the queen's chamber character.
    """

    obj_id = script.append_empty_object()
    scene_obj_id = script.append_empty_object()

    script.set_function(
        obj_id, FID.STARTUP,
        EF().add(EC.load_pc_always(recruit_char_id))
        .add(EC.set_object_coordinates_tile(0x28, 0x2A))
        .add_if(
            EC.if_flag(memory.Flags.MARLE_DISAPPEARED),
            EF().add(EC.remove_object(obj_id))
        ).add_if(
            EC.if_flag(memory.Flags.MANORIA_BOSS_DEFEATED),
            EF().add(EC.remove_object(obj_id))
        ).add(EC.return_cmd())
        .add(EC.end_cmd())
    )

    script.set_function(
        obj_id, FID.ACTIVATE,
        EF()
        .add(EC.set_explore_mode(False))
        .add(get_command(bytes.fromhex("2E561070F006")))
        .add(EC.pause(0.25))
        .add(get_command(bytes.fromhex("88401F0804")))
        .add(EC.call_obj_function(scene_obj_id, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.return_cmd())
    )

    arb0 = (
        EF().add(EC.script_speed(1))
        .add(EC.assign_val_to_mem(1, 0x7F020C, 1))
        .set_label('start')
    )
    x_pos, y_pos = 0x28, 0x29
    for ind in range(8):
        arb0.add(EC.set_object_coordinates_tile(x_pos, y_pos))
        arb0.add(EC.pause(0.063))
        y_pos -= 1
        if ind == 6:
            y_pos = 0x2A

    arb0.add_if(
        EC.if_mem_op_value(0x7F020C, OP.EQUALS, 0),
        EF().add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd())
    ).jump_to_label(EC.jump_back(), 'start')
    script.set_function(obj_id, FID.ARBITRARY_0, arb0)


    script.set_function(
        scene_obj_id, FID.STARTUP,
        EF().add(EC.return_cmd()).add(EC.end_cmd())
    )
    script.set_function(
        scene_obj_id, FID.ACTIVATE,
        EF().add(EC.return_cmd())
    )

    scene_fn = (
        EF()
        .add(EC.play_sound(0x88))
        .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.pause(0.438))
        .add(EC.call_obj_function(0xE, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.pause(0.438))
        .add(EC.call_obj_function(0x10, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.pause(0.438))
        .add(EC.call_obj_function(0x12, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.pause(0.438))
        .add(EC.call_obj_function(obj_id, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.call_obj_function(0x13, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.pause(0.25))
    )

    for sparkle_id in range(0xC, 0x13):
        funcsync = FS.CONT
        if sparkle_id == 0x12:
            funcsync = FS.HALT
        scene_fn.add(EC.call_obj_function(sparkle_id, FID.ARBITRARY_0, 4, funcsync))
        scene_fn.add(EC.pause(0.25))

    scene_fn.add(EC.assign_val_to_mem(0, 0x7F020C, 1))
    scene_fn.add(EC.play_sound(0x89))
    for sparkle_id in range(0xC, 0x13):
        funcsync = FS.CONT
        if sparkle_id == 0x12:
            funcsync = FS.HALT
        scene_fn.add(EC.call_obj_function(sparkle_id, FID.ARBITRARY_0, 4, funcsync))

    (
        scene_fn
        .add(get_command(bytes.fromhex("2E5610700F08")))
        .add(EC.set_flag(memory.Flags.MARLE_DISAPPEARED))
        .add(EC.set_explore_mode(True))
        .add(EC.return_cmd())
    )

    script.set_function(scene_obj_id, FID.ARBITRARY_0, scene_fn)



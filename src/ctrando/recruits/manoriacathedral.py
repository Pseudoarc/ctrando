"""Alter recruitable character in Manoria Cathedral"""
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, \
    get_command

import ctrando.base.openworldutils as owu
import ctrando.base.openworld.manoriasanctuary as manoriasanctuary

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
    """Put a recruitable character in cathedral."""
    script = script_man[ctenums.LocID.MANORIA_SANCTUARY]

    # extend the post_battle scene
    pos = script.find_exact_command(
        EC.assign_val_to_mem(1, 0x7F0210, 1),
        script.get_function_start(0xF, FID.ACTIVATE)
    )
    del_pos = script.find_exact_command(EC.party_follow(), pos)
    script.delete_commands(del_pos, 1)
    script.insert_commands(
        get_post_battle_scene().get_bytearray(), pos
    )

    if char_id == ctenums.CharID.FROG:
        pc_obj_id = 4
    elif char_id == ctenums.CharID.ROBO:
        pc_obj_id = 5
    else:
        pc_obj_id = 1 + char_id

    script.set_function(pc_obj_id, FID.STARTUP,
                        get_recruit_startup(char_id))
    script.set_function(pc_obj_id, FID.ARBITRARY_0,
                        make_frog_entry_function(char_id, char_id, min_level,
                                                 min_techlevel, scale_level_to_lead,
                                                 scale_techlevel_to_lead, scale_gear))

    pos = script.find_exact_command(
        EC.call_obj_function(4, FID.ARBITRARY_0, 3, FS.HALT),
        script.get_function_start(0xF, FID.ACTIVATE)
    )
    script.data[pos+1] = pc_obj_id*2

    pos = script.find_exact_command(EC.play_song(0x10), pos)
    script.delete_commands(pos, 1)

    # Comment Below here to remove anim checker
    # obj_id = script.append_copy_object(pc_obj_id)
    # pos, _ = script.find_command([0x8B], script.get_object_start(obj_id))
    # script.data[pos+1:pos+3] = [0xA, 0x1B]
    #
    # pos = script.find_exact_command(EC.set_own_drawing_status(False), pos)
    # script.delete_commands(pos, 1)
    #
    # act_fn = EF()
    #
    # new_str = script.add_py_string("Anim: {value 8}{null}")
    #
    # for ind in range(0x40, 0x80):
    #     act_fn.add(EC.assign_val_to_mem(ind, 0x7E0200, 1))
    #     act_fn.add(EC.static_animation(ind))
    #     act_fn.add(EC.auto_text_box(new_str))
    #
    # act_fn.add(EC.return_cmd())
    #
    # script.set_function(obj_id, FID.ACTIVATE, act_fn)


def get_post_battle_scene() -> EF:
    """
    Get the post-battle scene where the recruit comes down.
    """
    char_mem_st = manoriasanctuary.EventMod.char_mem_st
    return (
        EF().add(EC.set_explore_mode(False))
        .append(owu.make_safe_pc_func_call(FID.ARBITRARY_3, 3,
                                           char_mem_st))
        .add(EC.play_song(0x16))
        .add(EC.play_sound(0x7B)).add(EC.play_sound(0x7B))
        .add(EC.play_sound(0x6F)).add(EC.play_sound(0x6F))
        .add(EC.call_obj_function(0x10, FID.ARBITRARY_2, 3, FS.HALT))
        .add(EC.call_pc_function(1, FID.ARBITRARY_4, 3, FS.HALT))
        .add(EC.generic_command(0xAD, 1))
        .add(EC.set_object_script_processing(0x18, True))
        .add(EC.call_obj_function(0x18, FID.ARBITRARY_0, 3, FS.CONT))
        .add(EC.call_pc_function(1, FID.ARBITRARY_5, 3, FS.HALT))
        .add(EC.call_pc_function(2, FID.ARBITRARY_5, 3, FS.CONT))
        .add(EC.call_pc_function(0, FID.ARBITRARY_5, 3, FS.HALT))
        .add(EC.call_obj_function(4, FID.ARBITRARY_0, 3, FS.HALT))
    )


def get_recruit_startup(recruit_identity: ctenums.CharID) -> EF:
    """
    Return the startup function for the recruit.
    """
    ret_func = (
        EF()
        # .add(EC.load_pc_in_party(recruit_identity))
        .add_if_else(
            EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
            EF().add(EC.load_pc_always(recruit_identity))
            .add(EC.set_object_coordinates_tile(0xB, 0))
            .add(EC.script_speed(4))
            .add(EC.set_own_facing('right'))
            .add(EC.generic_command(0x8E, 0x33))
            .add(EC.set_own_drawing_status(False)),
            EF().add(EC.load_pc_in_party(recruit_identity))
        ).add(EC.return_cmd())
        .set_label('loop_st')
        .add_if(
            EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
            EF().add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'loop_st')
        ).add(EC.set_controllable_infinite())
    )

    return ret_func


def get_recruit_block(
        char_identity: ctenums.CharID,
        min_level: int,
        min_techlevel: int,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
) -> EF:
    """
    Get the function that actually adds the PC to the party and sets the flag.
    """

    two_pc_recruit = (
        EF()
        .add(EC.party_follow())
        .add(EC.set_explore_mode(False))
        .add(EC.reset_animation())
        .add(EC.set_own_facing_pc(0))
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.generic_command(0x95, 0))  # Follow PC00 once
        .add(EC.add_pc_to_active(char_identity))
        .add(EC.load_pc_in_party(char_identity))
        .add(EC.assign_val_to_mem(1, 0x7F0210, 1))
        .add(EC.set_flag(memory.Flags.MANORIA_RECRUIT_OBTAINED))
    )

    three_pc_recruit = (
        EF()
        .add(EC.reset_animation())
        .add(EC.set_own_facing_pc(0))
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.generic_command(0x95, 0))  # Follow PC00 once
        .add(EC.party_follow())
        .add(EC.add_pc_to_reserve(char_identity))
        .add(EC.load_pc_in_party(char_identity))
        .add(EC.assign_val_to_mem(1, 0x7F0210, 1))
        .add(EC.set_flag(memory.Flags.MANORIA_RECRUIT_OBTAINED))
        .add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        .add(EC.switch_pcs())
        .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
    )

    scale_block = owu.get_level_techlevel_set_function(
        char_identity, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    recruit_func = (
        EF()
        .append(scale_block)
        .add(EC.name_pc(char_identity))
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .add_if_else(
            # PC3 is set to 0x7F0224 in the manoria openworld mod
            EC.if_mem_op_value(0x7F0224, OP.EQUALS, 0x80, 1, 0),
            two_pc_recruit,
            three_pc_recruit
        )
    )
    return recruit_func

    
def make_frog_entry_function(
        char_identity: ctenums.CharID,
        char_graphics: ctenums.CharID,
        min_level: int,
        min_techlevel: int,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
) -> EF:
    """
    Get the funtion that makes a recruit drop from the ceiling.
    """

    # Some char_graphics-specific animations to insert in the scene.
    fall_frame_dict: dict[ctenums.CharID, int] = {
        ctenums.CharID.AYLA: 167,
        ctenums.CharID.MAGUS: 93
    }
    
    attack_frame_dict: dict[ctenums.CharID, list[int]] = {
        ctenums.CharID.CRONO: [90, 91, 92],
        ctenums.CharID.MARLE: [140, 141, 141],
        ctenums.CharID.LUCCA: [162, 163, 163],
        ctenums.CharID.FROG: [0x8E, 0x8F, 0x90],
        ctenums.CharID.ROBO: [0x75, 0x76, 0x76],
        ctenums.CharID.AYLA: [146, 147, 148],
        ctenums.CharID.MAGUS: [118, 120, 121]
    }

    sheath_frame_dict: dict[ctenums.CharID, list[int]] = {
        ctenums.CharID.MARLE: [55, 54, 53, 52],
        ctenums.CharID.LUCCA: [57, 56, 55, 54],
        ctenums.CharID.FROG: [0x37, 0x36, 0x35, 0x34],
        ctenums.CharID.ROBO: [0xA2, 0xA3, 0xA3, 0xA2],
        ctenums.CharID.MAGUS: [47, 46, 45, 44]
    }

    sound_id_dict: dict[ctenums.CharID, list[int]] = {
        # Falling, generic sound
        ctenums.CharID.FROG: [0x53, 0x6E],
        ctenums.CharID.ROBO: [0x60, 0x3F],
    }

    falling_frame = fall_frame_dict.get(char_graphics, 0x97)

    attack_frames = attack_frame_dict.get(
        char_graphics, [0x8E, 0x8F, 0x90])
    sheath_frames = sheath_frame_dict.get(
        char_graphics, [0x37, 0x36, 0x35, 0x34])
    fall_sound, char_noise = sound_id_dict.get(
        char_graphics, [0x53, 0x3F]
    )

    ret_func = (
        EF()
        # Initial Part:  Same for all PCs
        .add(EC.set_own_drawing_status(True))
        .add(EC.script_speed(2))
        .add(EC.set_move_properties(True, True))
        .add(EC.static_animation(falling_frame))
        .add(EC.play_sound(0x02))
        .add(EC.set_move_speed(0x60))
        .add(EC.move_sprite(0xB, 0xA, is_animated=True))
        .add(EC.play_sound(fall_sound))
        .add(EC.play_animation(0x1D))
        .add(EC.generic_command(0xAD, 3))
        # memcpy88 that I don't handle correctly right now.
        .add(get_command(bytes.fromhex('888D0800FF7F0B6FFF01')))
        .add(EC.set_move_speed(0x40))
        .add(EC.play_animation(6))
        .add(EC.move_sprite(9, 9))
        .add(EC.play_animation(0x1D))
        .add(EC.set_own_facing_object(0x18))
        .add(EC.generic_command(0xAD, 4))
        .add(EC.script_speed(0x10))
        # End Initial Part
        .add(EC.static_animation(attack_frames[0]))
        .add(EC.play_sound(0x87))
        .add(EC.call_obj_function(0x18, FID.ARBITRARY_1, 2, FS.CONT))
        .add(EC.static_animation(attack_frames[1]))
        .add(EC.static_animation(attack_frames[2]))
        .add(EC.script_speed(2))
        .add(EC.play_song(0))
        .add(EC.remove_object(0x18))
        .add(EC.play_sound(char_noise)).add(EC.play_sound(char_noise))
        .add(EC.play_song(ra.get_char_music(char_identity)))
        .add(EC.static_animation(sheath_frames[0]))
        .add(EC.break_cmd())
        .add(EC.static_animation(sheath_frames[1]))
        .add(EC.break_cmd())
        .add(EC.static_animation(sheath_frames[2]))
        .add(EC.break_cmd())
        .add(EC.static_animation(sheath_frames[3]))
        .add(EC.generic_command(0xAD, 0x10))
        .add(EC.play_animation(0x1A))  # Laugh animation
        .add(EC.play_sound(char_noise))
        .add(EC.set_own_facing_pc(0))
        .add(EC.call_pc_function(2, FID.ARBITRARY_6, 5, FS.CONT))
        .add(EC.call_pc_function(0, FID.ARBITRARY_6, 5, FS.HALT))
        .add(EC.play_sound(char_noise))
        .add(EC.call_pc_function(1, FID.ARBITRARY_6, 5, FS.HALT))
        .add(EC.play_animation(0))
        .add(EC.set_own_facing('down'))
        .add(EC.play_sound(char_noise))
        .add(EC.set_move_speed(0x18))
        .add(EC.play_animation(1))
        .add(EC.move_sprite(0xA, 9))
        .add(EC.play_sound(char_noise))
        .add(EC.play_animation(1))
        .add(EC.move_sprite(0xA, 0xE))
        .add(EC.play_animation(0))
        .append(get_recruit_block(char_identity, min_level, min_techlevel,
                                  scale_level_to_lead, scale_techlevel_to_lead, scale_gear))
        .add(EC.return_cmd())
    )

    return ret_func

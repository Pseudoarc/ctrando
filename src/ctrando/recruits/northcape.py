"""Alter recruitable character in North Cape"""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, \
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, \
    get_command
import ctrando.recruits.recruitassign as ra
from ctrando.strings import ctstrings

# Idea is to have this be a boss spot + recruit/item spot
# If it's a recruit, then you fight a boss version of that character and get the
# recruit.  If it's an item, then you just fight a boss and get a KI on the ground
# like tne vanilla Amulet.

def assign_pc_to_spot(
        recruit_char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
):
    """Put a recruitable character in North Cape."""

    # The vanilla spot works like this:
    # 1) The Giant Blue Star (Obj10) is set to only appear at the right time.
    #    When activated, it calls out to Obj09, Activate, which does the Magus
    #    disappear and reappear trick.
    # 2) This sets a cutscene flag and plays the Magus flashback.
    # 3) Returning to the scene with the flag set, causes Obj00, Startup to call
    #    out to Obj09, Touch to complete the scene with the possible battle.

    # For recruitment, we just need to:
    # 1) Change the appearance condition of the Giant Blue Star (Obj10)
    # 2) Modify the cutscene in Obj09, Activate to go straight to recruitment.
    # 3) Make sure the PCs have the correct Arbs to do the scene.
    #    - Crono and Magus need the Arb0 stopping function.  Maybe more.
    #    - The recruit will need to copy some of Magus's Arbs.

    script = script_man[ctenums.LocID.NORTH_CAPE]
    recruit_obj_id = recruit_char_id + 1

    # Change the sparkle object.
    sparkle_obj = 0x10
    script.set_function(
        sparkle_obj, FID.STARTUP,
        EF().add(EC.load_npc(0x71))
        .add(EC.set_object_coordinates_tile(7, 6))
        .add_if(
            EC.if_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
            EF().add(EC.set_own_drawing_status(False)))
        .add(EC.return_cmd()).add(EC.end_cmd())
    )

    script.set_function(
        sparkle_obj, FID.ACTIVATE,
        EF().add_if(
            EC.if_not_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
            EF().add(EC.party_follow())
            .add(EC.call_obj_function(9, FID.ACTIVATE, 1, FS.HALT))
        ).add(EC.return_cmd())
    )

    # Mostly copying from the vanilla event with many omissions.
    temp_pc3_addr = 0x7F0240
    # Change the function it calls out to.
    new_function = (
        EF().add(EC.set_explore_mode(False))
        .add(EC.assign_val_to_mem(1, 0x7F020E, 1))  # Stop Fn
        .add(EC.call_pc_function(0, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.call_pc_function(1, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.call_pc_function(2, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.generic_command(0xE7, 0, 2))  # Scroll
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_0, 1, FS.HALT))
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_1, 1, FS.SYNC))
    )
    for pc_id in ctenums.CharID:
        if pc_id != recruit_char_id:
            obj_id = pc_id+1
            new_function.add(EC.set_object_facing(obj_id, 'down'))
    (
        new_function
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_2, 2, FS.HALT))
        .add(EC.call_pc_function(2, FID.ARBITRARY_1, 1, FS.CONT))
        .add(EC.call_pc_function(1, FID.ARBITRARY_1, 1, FS.CONT))
        .add(EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.HALT))
        .add(EC.move_party(0x07, 0x09,
                           0x05, 0x09,
                           0x09, 0x09))
        .add(EC.play_song(ra.get_char_music(recruit_char_id)))
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_3, 2, FS.HALT))
        .add(EC.pause(1))
        .add_if(
            EC.if_mem_op_value(temp_pc3_addr, OP.NOT_EQUALS, 0x80),
            EF().add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        ).add(EC.assign_val_to_mem(0, 0x7F020E, 1))  # Stop Fn
        .add(EC.party_follow()).add(EC.set_explore_mode(True))
        .add(EC.return_cmd())
    )

    script.set_function(
        9, FID.ACTIVATE, new_function
    )

    scale_block = owu.get_level_techlevel_set_function(
        recruit_char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    script.set_function(
        recruit_obj_id, FID.ARBITRARY_3,
        EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, temp_pc3_addr, 1))
        .add(EC.reset_animation())
        .add(EC.set_own_facing_pc(0))
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.follow_pc_once(0))
        .add(EC.name_pc(recruit_char_id))
        .append(scale_block)
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .add_if_else(
            EC.if_mem_op_value(temp_pc3_addr, OP.EQUALS, 0x80),
            EF().add(EC.add_pc_to_active(recruit_char_id)),
            EF().add(EC.add_pc_to_reserve(recruit_char_id))
        ).add(EC.load_pc_in_party(recruit_char_id))
        .add(EC.set_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED))
        .add(EC.return_cmd())
    )

    # Save functions before messing with the pc objects
    stopping_arb = script.get_function(2, FID.ARBITRARY_0)
    surprise_arb = script.get_function(2, FID.ARBITRARY_1)

    repl_anim_dict: dict[ctenums.CharID, tuple[int, int]] ={
        ctenums.CharID.MARLE: (0x13, 0x14),
    }

    anims = repl_anim_dict.get(recruit_char_id, (0x1A, 0x23))
    first_anim_id, second_anim_id = anims[0], anims[1]

    # recruit_arb0 = script.get_function(7, FID.ARBITRARY_0)
    recruit_arb0 = (
        EF().add(EC.play_animation(0x26))
        .add(EC.play_sound(2))
        .add(EC.set_own_drawing_status(True))
        .add(EC.generic_command(0xAD, 2))
        .add(EC.play_animation(first_anim_id))
        .add(EC.set_own_facing('down'))
        .add(EC.return_cmd())
    )
    # recruit_arb1 = script.get_function(7, FID.ARBITRARY_1)
    recruit_arb1 = (
        EF().add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd())
    )
    recruit_arb2 = (
        EF().add(EC.play_sound(2))
        .add(EC.set_object_coordinates_tile(7, 5))
        .add(EC.set_own_drawing_status(True))
        .add(EC.play_animation(second_anim_id))
        .add(EC.set_object_drawing_status(0x10, False))
        .add(EC.generic_command(0xAD, 4))
        .add(EC.play_animation(0))
        .add(EC.auto_text_box(0))
        .add(EC.set_own_facing('up'))
        .add(EC.play_animation(0x22))
        .add(EC.return_cmd())
    )
    # Change name of string
    if recruit_char_id == ctenums.CharID.CRONO:
        script.strings[0] = ctstrings.CTString.from_str(
            "{Crono}: ... {null}"
        )
    else:
        script.strings[0][0] = 0x13 + recruit_char_id

    # Recruit startup
    script.set_function(
        recruit_obj_id, FID.STARTUP,
        EF().add_if_else(
            EC.if_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
            EF().add(EC.load_pc_in_party(recruit_char_id)),
            EF().add(EC.load_pc_always(recruit_char_id))
            .add(EC.set_object_coordinates_tile(7, 0xB))
            .add(EC.set_own_drawing_status(False))
            .add(EC.set_own_facing('up'))
        ).add(EC.return_cmd())
        .set_label('loop_st')
        .add_if(
            EC.if_not_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
            EF().jump_to_label(EC.jump_back(), 'loop_st')
        ).add(EC.set_controllable_infinite())
        .add(EC.end_cmd())
    )

    if recruit_char_id != ctenums.CharID.MAGUS:
        script.set_function(recruit_obj_id, FID.ARBITRARY_0, recruit_arb0)
        script.set_function(recruit_obj_id, FID.ARBITRARY_1, recruit_arb1)
        script.set_function(recruit_obj_id, FID.ARBITRARY_2, recruit_arb2)


    for pc_id in ctenums.CharID:
        if pc_id != recruit_char_id:
            obj_id = pc_id + 1
            script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.ARBITRARY_0, stopping_arb)
            script.set_function(obj_id, FID.ARBITRARY_1, surprise_arb)


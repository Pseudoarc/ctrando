"""Alter recruitable character in Proto Dome"""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
import ctrando.recruits.recruitassign as ra

def assign_pc_to_spot(
        char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
):
    """
    Assign a PC to the Proto Dome Spot
    """

    script = script_man[ctenums.LocID.PROTO_DOME]
    obj_id = char_id + 1

    # Add pc-tracking to activate
    pos = script.get_function_start(0, FID.ACTIVATE)
    pc3_addr = 0x7F0230

    # Replace the recruit object with the usual conditional load/controllable
    startup_fn = (
        EF().add_if_else(
            EC.if_flag(memory.Flags.PROTO_DOME_RECRUIT_OBTAINED),
            EF().add(EC.load_pc_in_party(char_id)),
            EF().add(EC.load_pc_always(char_id))
            .add(EC.set_object_coordinates_tile(0x38, 0x16))
            .add(EC.play_animation(0x1D))
        ).add(EC.return_cmd())
        .set_label('loop')
        .add_if(
            EC.if_not_flag(memory.Flags.PROTO_DOME_RECRUIT_OBTAINED),
            EF().add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'loop')
        ).add(EC.set_controllable_infinite())
        .add(EC.end_cmd())
    )
    script.set_function(obj_id, FID.STARTUP, startup_fn)

    # The enertron functions mess with move speed/properties.  Reset them
    # when the enertron is done to avoid messing up the recruit scene.
    pos = script.get_function_start(1, FID.ARBITRARY_2)
    script.insert_commands(
        EF().add(EC.set_move_speed(0x10))
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, False))
        .get_bytearray(), pos
    )

    script.set_function(
        obj_id, FID.ARBITRARY_4,
        EF().add_if_else(
            EC.if_mem_op_value(pc3_addr, OP.EQUALS, 0x80),
            EF().add(EC.add_pc_to_active(char_id)),
            EF().add(EC.add_pc_to_reserve(char_id))
        ).add(EC.load_pc_in_party(char_id))
        .add(EC.return_cmd())
    )

    # Set arb4 for non-recruit PCs
    for pc_id in ctenums.CharID:
        pc_obj_id = pc_id + 1
        if pc_obj_id == obj_id:
            continue

        script.set_function(
            pc_obj_id, FID.ARBITRARY_4,
            EF().add(EC.play_animation(0x9)).add(EC.pause(0.5))
            .add(EC.play_animation(0))
            .add(EC.return_cmd())
        )

    # Repurpose object 8 for performing the actual character adding.
    extra_recruit_obj = 8

    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    activate_fn = (
        EF().add(EC.set_explore_mode(False))
        .add(EC.assign_val_to_mem(0, 0x7F0240, 1))
        .add(EC.break_cmd())
        .add(EC.move_party(0x36, 0x19, 0x38, 0x19, 0x3A | 0x80, 0x16))
        .add(EC.play_song(ra.get_char_music(char_id)))
        .add(EC.generic_command(0xEB, 0x50, 0xFF))
        .add(EC.play_animation(0xE))
        .add(EC.assign_val_to_mem(0, 0x7F0226, 1))
        .set_label('spark_loop')
        .add_if(
            EC.if_mem_op_value(0x7F0226, OP.LESS_THAN, 2),
            EF().add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.generic_command(0xAD, 3))
            .add(EC.call_pc_function(0, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.play_sound(0x7B))
            .add(EC.call_obj_function(0xB, FID.ARBITRARY_1, 2, FS.CONT))
            .add(EC.generic_command(0xAD, 1))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.generic_command(0xAD, 3))
            .add(EC.call_pc_function(1, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_obj_function(0xC, FID.ARBITRARY_1, 2, FS.CONT))
            .add(EC.generic_command(0xAD, 1))
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.generic_command(0xAD, 3))
            .add(EC.call_pc_function(2, FID.ARBITRARY_4, 4, FS.CONT))
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_1, 2, FS.CONT))
            .add(EC.generic_command(0xAD, 1))
            .add(EC.add(0x7F0226, 1))
            .jump_to_label(EC.jump_back(), 'spark_loop')
        ).add(EC.remove_object(0xB)).add(EC.remove_object(0xC))
        .add(EC.remove_object(0xD))
        .add(EC.set_own_facing('down'))
        .add(EC.set_move_speed(0x20))
        .add(EC.play_animation(0x24))
        .add(EC.set_move_properties(True, True))
        .add(EC.move_sprite(0x35, 0x16)).add(EC.set_move_destination(True, False))
        .add(EC.move_sprite(0x38, 0x16)).add(EC.set_own_facing('down'))
        .add(EC.set_move_speed(0x18))
        .add(EC.play_animation(0x1A))
        .add(EC.pause(2))
        .add(EC.reset_animation())
        .add(EC.follow_pc_once(0))
        .add(EC.name_pc(char_id))
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .append(scale_block)
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, pc3_addr, 1))
        .add_if_else(
            EC.if_mem_op_value(pc3_addr, OP.EQUALS, 0x80),
            EF().add(EC.add_pc_to_active(char_id)),
            EF().add(EC.add_pc_to_reserve(char_id))
        ).add(EC.load_pc_in_party(char_id))
        .add(EC.set_flag(memory.Flags.PROTO_DOME_RECRUIT_OBTAINED))
        .add(EC.call_obj_function(extra_recruit_obj, FID.ARBITRARY_0, 5, FS.CONT))
        .add(EC.return_cmd())
    )
    script.set_function(obj_id, FID.ACTIVATE, activate_fn)
    script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))

    script.set_function(
        extra_recruit_obj, FID.ARBITRARY_0,
        EF().add_if(
            EC.if_mem_op_value(pc3_addr, OP.NOT_EQUALS, 0x80),
            EF().add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        ).add(EC.party_follow())
        .add(EC.set_explore_mode(True))
        .add(EC.assign_val_to_mem(0, 0x7F0224, 1))
        .add(EC.return_cmd())
    )


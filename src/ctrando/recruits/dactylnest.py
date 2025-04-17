"""Alter recruitable character in Dactyl Nest"""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
import ctrando.recruits.recruitassign as ra
from ctrando.base.openworld import dactylsummit

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
    Assign a PC to the Dactyl Nest Spot.
    - Modify the scene that plays to have a recruit call the dactyls and join.
    """
    script = script_man[ctenums.LocID.DACTYL_NEST_SUMMIT]
    dactylmod = dactylsummit.EventMod

    recruit_obj_id = char_id + 2
    pos = script.find_exact_command(
        EC.call_obj_function(0xD, FID.ARBITRARY_0, 1, FS.CONT)
    )
    end = script.find_exact_command(EC.pause(1))

    repl_block = (
        EF()
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_2, 1, FS.CONT))
        .add(EC.call_obj_function(0x9, FID.ACTIVATE, 1, FS.CONT))
        .add_if(
            EC.if_mem_op_value(dactylmod.pc2_addr, OP.NOT_EQUALS, 0x80),
            EF()
            .add(EC.call_obj_function(0xA, FID.ACTIVATE, 1, FS.CONT))
        ).add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 1, FS.CONT))
        .add(EC.move_party(8, 0xF, 8, 0xF, 8, 0xF))
        .add(EC.move_party(6, 0xB, 7, 0xB, 5, 0xB))
        # Recruit stuff
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .add(EC.play_song(ra.get_char_music(char_id)))
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_3, 1, FS.HALT))
        .add_if_else(
            EC.if_pc_active(char_id),
            EF(),
            EF()
            .add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        )
    )
    script.delete_commands_range(pos, end)
    script.insert_commands(repl_block.get_bytearray(), pos)

    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    script.set_function(
        recruit_obj_id, FID.ARBITRARY_3,
        EF()
        .add(EC.set_move_properties(True, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.set_move_speed(0x40))
        .add(EC.reset_animation())
        .append(scale_block)
        .add_if_else(
            EC.if_mem_op_value(dactylmod.pc3_addr, OP.GREATER_THAN, 6),
            EF().add(EC.add_pc_to_active(char_id))
            .add(EC.follow_pc_once(0)),
            EF().add(EC.add_pc_to_reserve(char_id))
        )
        .add(EC.name_pc(char_id))
        .add(EC.set_flag(memory.Flags.OBTAINED_DACTYLS))
        .add(EC.load_pc_in_party(char_id))
        .add(EC.return_cmd())
    )

    remove_keeper(script)
    modify_pc_functions(script, char_id)

def remove_keeper(script: LocationEvent):
    """
    Remove the Keeper from the scene when there's a recruit.
    """
    pos = script.get_object_start(0xD)
    script.insert_commands(
        EF().add(EC.return_cmd()).add(EC.end_cmd()).get_bytearray(),
        pos
    )

def modify_pc_functions(script: LocationEvent,
                        recruit_char_id: ctenums.CharID):
    """
    Modify the recruit's functions:
    - Conditional load depending on whether the recruit has been found.
    - Add a function for calling the dactyl.
    """
    recruit_obj_id = recruit_char_id + 2

    new_startup = (
        EF().add_if_else(
            EC.if_flag(memory.Flags.OBTAINED_DACTYLS),
            EF().add(EC.load_pc_in_party(recruit_char_id)),
            EF().add(EC.load_pc_always(recruit_char_id))
            .add(EC.set_object_coordinates_pixels(0x68, 0x92))
            .add(EC.set_own_facing('up'))
        ).add(EC.return_cmd())
        .add_if(
            EC.if_flag(memory.Flags.OBTAINED_DACTYLS),
            EF().add(EC.set_controllable_infinite())
        ).add(EC.end_cmd())
    )
    script.set_function(recruit_obj_id, FID.STARTUP, new_startup)

    new_arb2 = (
        EF()
        .add(EC.set_own_facing('up'))
        .add(EC.play_animation(0x15))
        .add(EC.return_cmd())
    )
    script.set_function(recruit_obj_id, FID.ARBITRARY_2, new_arb2)


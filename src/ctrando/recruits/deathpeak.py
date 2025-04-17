"""Alter recruitable character in Death Peak."""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP,\
    FuncSync as FS, get_command, Facing
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.common.randostate import ScriptManager
import ctrando.recruits.recruitassign as ra

def assign_pc_to_spot(char_id: ctenums.CharID,
                      script_man: ScriptManager,
                      min_level: int = 1,
                      min_techlevel: int = 0,
                      scale_level_to_lead: bool = False,
                      scale_techlevel_to_lead: bool = False,
                      scale_gear: bool = False
                      ):
    """Put a recruitable character in Death Peak."""

    # This one is easy since we're skipping the time freeze scene.
    script = script_man[ctenums.LocID.DEATH_PEAK_SUMMIT]

    pos, _ = script.find_command([0xE1])
    repl_cmd = bytes.fromhex("DFAD010808")
    script.data[pos:pos+len(repl_cmd)] = repl_cmd
    script.insert_commands(
        EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1).to_bytearray(),
        pos
    )

    # temp_addr = 0x7F0220
    # new_block = (
    #     EF()
    #     .append(scale_block)
    #     .add(EC.name_pc(char_id))
    #     .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3,
    #                               temp_addr, 1))
    #     .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
    #     .add_if_else(
    #         EC.if_mem_op_value(temp_addr, OP.GREATER_THAN, 6),
    #         EF().add(EC.add_pc_to_active(char_id)),
    #         EF().add(EC.add_pc_to_reserve(char_id))
    #         .add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
    #         .add(EC.switch_pcs())
    #         .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
    #     )
    # )

    # script.insert_commands(new_block.get_bytearray(), pos)
    modify_reunion_scene(char_id, script_man, min_level, min_techlevel,
                         scale_level_to_lead, scale_techlevel_to_lead)


def modify_reunion_scene(char_id: ctenums.CharID,
                         script_man: ScriptManager,
                         min_level: int,
                         min_techlevel: int,
                         scale_level_to_lead: bool = False,
                         scale_techlevel_to_lead: bool = False,
                         scale_gear: bool = False):
    script = script_man[ctenums.LocID.DEATH_PEAK_SUMMIT_AFTER]

    modify_reunion_pc_objs(char_id, script)
    modify_strings(char_id, script)

    recruit_obj_id = char_id + 1

    pos = script.find_exact_command(
        EC.call_obj_function(1, FID.ARBITRARY_0, 3, FS.HALT)
    )
    repl_cmd = EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_0, 3, FS.HALT)
    script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()

    pos = script.find_exact_command(
        EC.call_obj_function(2, FID.ARBITRARY_0, 3, FS.CONT),
        pos
    )
    del_end = script.find_exact_command(
        EC.get_result(0x7F0216), pos
    )
    script.delete_commands_range(pos, del_end)
    script.insert_commands(
        EF().add(EC.call_pc_function(0, FID.ARBITRARY_0, 3, FS.CONT))
        .add(EC.pause(0.125))
        .add(EC.call_pc_function(1, FID.ARBITRARY_0, 3, FS.CONT))
        .add(EC.pause(0.125))
        .add(EC.call_pc_function(2, FID.ARBITRARY_0, 3, FS.CONT))
        .add(EC.pause(0.125)).get_bytearray(),
        pos
    )

    scale_to_lead = scale_level_to_lead or scale_techlevel_to_lead
    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    pos = script.find_exact_command(
        EC.call_obj_function(1, FID.ARBITRARY_1, 3, FS.HALT)
    )
    ins_block = (
        EF()
        .add(EC.play_song(ra.get_char_music(char_id)))
        .add(EC.generic_command(0xEB, 0x80, 0xFF))
        .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_1, 3, FS.HALT))
        .add(EC.pause(0.5))
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, 0x7F0220, 1))
        .append(scale_block)
        .add(EC.name_pc(char_id))
        .add_if_else(
            EC.if_mem_op_value(0x7F0220, OP.GREATER_THAN, 6),
            EF().add(EC.add_pc_to_active(char_id)),
            EF().add(EC.add_pc_to_reserve(char_id))
        ).add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1))
    )
    script.insert_commands(ins_block.get_bytearray(), pos)
    pos += len(ins_block)
    script.delete_commands(pos, 1)

    pos = script.find_exact_command(EC.get_result(0x7F0216), pos)
    del_end, _ = script.find_command([0xDF], pos)

    script.delete_commands_range(pos, del_end)
    end_block = (
        EF().add(EC.darken(0xA))
        .add(EC.fade_screen())
        .add(EC.pause(2))
    )
    script.insert_commands(end_block.get_bytearray(), pos)
    pos += len(end_block)

    peak_entrance = script_man[ctenums.LocID.DEATH_PEAK_ENTRANCE]
    _, new_changeloc_cmd = peak_entrance.find_command(EC.change_loc_commands, script.get_object_start(0))

    script.data[pos:pos+len(new_changeloc_cmd)] = new_changeloc_cmd.to_bytearray()


def modify_strings(char_id: ctenums.CharID,
                   script: LocationEvent):
    """
    Change {crono} to the {char_id} in strings.
    """
    repl_byte = bytes([0x13 + char_id])

    for ind, string in enumerate(script.strings):
        script.strings[ind] = string.replace(b'\x13', repl_byte)


def modify_reunion_pc_objs(char_id: ctenums.CharID,
                           script: LocationEvent):
    """
    Update coordinates and drawing to account for a different recruit.
    """

    pos = script.get_object_start(0)

    new_block = (
        EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC1,
                                      0x7F0216, 1))
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC2,
                                  0x7F0218, 1))
    )
    script.insert_commands(new_block.get_bytearray(), pos)

    pos += len(new_block)
    script.delete_commands(pos, 2)

    for pc_id in ctenums.CharID:
        obj_id = pc_id + 1
        if pc_id == char_id:
            script.set_function(
                obj_id, FID.STARTUP,
                EF().add(EC.load_pc_always(pc_id))
                .add(EC.set_object_coordinates_tile(0x8, 0))
                .add(EC.play_animation(0x22))
                .add(EC.set_move_properties(True, True))
                .add(EC.return_cmd())
                .add(get_command(bytes.fromhex('88400F0F01')))
                .add(EC.generic_command(0x8E, 0x15))
                .add(EC.end_cmd())
            )

            script.set_function(
                obj_id, FID.ARBITRARY_0,
                EF().add(EC.set_move_speed(0x10))
                .add(EC.generic_command(0x8E, 0x33))
                .add(EC.move_sprite(0x8, 0xB))
                .add(get_command(bytes.fromhex('E600040150')))
                .add(EC.generic_command(0xEB, 0x80, 0))
                .add(EC.move_sprite(0x8, 0xD))
                .add(EC.play_animation(0x12))
                .add(get_command(bytes.fromhex("88400FF008")))
                .add(EC.return_cmd())
            )

            script.set_function(
                obj_id, FID.ARBITRARY_1,
                EF().add(EC.reset_animation())
                .add(EC.set_own_facing('left'))
                .add(EC.return_cmd()),
            )
        else:
            script.set_function(
                obj_id, FID.STARTUP,
                EF().add(EC.load_pc_in_party(pc_id))
                .add(EC.set_object_coordinates_tile(0x7, 0xE))
                .add_if(
                    EC.if_mem_op_value(0x7F0216, OP.EQUALS, pc_id),
                    EF().add(EC.set_object_coordinates_tile(0x6, 0xC))
                    .add(EC.set_own_facing('right'))
                ).add_if(
                    EC.if_mem_op_value(0x7F0218, OP.EQUALS, pc_id),
                    EF().add(EC.set_object_coordinates_tile(0x9, 0xD))
                    .add(EC.set_own_facing('up'))
                ).add(EC.play_animation(0x1D))
                .add(EC.return_cmd())
                .add(get_command(bytes.fromhex('88400F0F01')))
                .add(EC.generic_command(0x8E, 0x15))
                .add(EC.end_cmd())
            )

            script.set_function(
                obj_id, FID.ARBITRARY_0,
                EF().add(EC.generic_command(0x8E, 0x80))
                .add(get_command(bytes.fromhex("88400FF001")))
                .add(EC.return_cmd())
            )


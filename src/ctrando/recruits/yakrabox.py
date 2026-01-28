"""Add recruitable character to the Yakra Key box"""
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
    Assign a PC to the Yakra Key box.
    """
    pc_obj_id = 1 + char_id
    script = script_man[ctenums.LocID.GUARDIA_LAWGIVERS_TOWER]

    startup_fn = (
        EF().add_if_else(
            EC.if_flag(memory.Flags.RESCUE_CHANCELLOR_1000),
            EF().add(EC.load_pc_in_party(char_id)),
            EF().add(EC.load_pc_always(char_id))
            .add(EC.set_object_coordinates_tile(0xB, 0x2C))
            .add(EC.set_own_drawing_status(False))
        ).add(EC.return_cmd())
        .set_label('loop')
        .add_if(
            EC.if_not_flag(memory.Flags.RESCUE_CHANCELLOR_1000),
            EF().add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'loop')
        ).add(EC.set_controllable_infinite())
        .add(EC.end_cmd())
    )
    script.set_function(pc_obj_id, FID.STARTUP, startup_fn)

    jump_fn = (
        EF()
        .add(EC.play_animation(9))
        .add(EC.set_own_drawing_status(True))
        .add(EC.generic_command(0x7A, 0x07, 0x2C, 0x02)) # jump
        .add(EC.reset_animation())
        .add(EC.return_cmd())
    )

    script.set_function(pc_obj_id, FID.ARBITRARY_3, jump_fn)

    scale_block =  owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    temp_pc3_addr = 0x7F0220
    join_fn = (
        EF()
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.set_own_facing_pc(0))
        .add(EC.play_animation(1))
        #.add(EC.move_sprite(0xA, 0x2C, True))
        .add(EC.follow_pc_once(0))
        #.add(EC.reset_animation())
        .add(EC.name_pc(char_id))
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, temp_pc3_addr, 1))
        .add_if_else(
            EC.if_mem_op_value(temp_pc3_addr, OP.GREATER_THAN, 6),
            EF()
            .add(EC.add_pc_to_active(char_id))
            .add(EC.set_flag(memory.Flags.RESCUE_CHANCELLOR_1000))
            .add(EC.play_animation(0))
            .add(EC.load_pc_in_party(char_id)),
            EF()
            .add(EC.add_pc_to_reserve(char_id))
            .add(EC.load_pc_in_party(char_id))
            .add(EC.set_flag(memory.Flags.RESCUE_CHANCELLOR_1000))
            .add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        )
        .add(EC.return_cmd())
    )

    script.set_function(pc_obj_id, FID.ARBITRARY_4, join_fn)

    pos = script.find_exact_command(
        EC.call_obj_function(9, FID.ARBITRARY_0, 4, FS.HALT)
    )
    script.replace_command_at_pos(
        pos,
        EC.call_obj_function(pc_obj_id, FID.ARBITRARY_3, 4, FS.HALT)
    )

    pos = script.find_exact_command(
        EC.call_obj_function(9, FID.ARBITRARY_1, 4, FS.HALT)
    )
    script.delete_commands(pos, 8)
    script.insert_commands(
        EF()
        .add(EC.call_obj_function(pc_obj_id, FID.ARBITRARY_4, 4, FS.HALT))
        .get_bytearray(), pos
    )


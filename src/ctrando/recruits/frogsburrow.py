"""Alter recruitable character in Frog's Burrow."""
import typing

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP,\
    FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.common.randostate import ScriptManager

# noinspection DuplicatedCode
_char_objs: dict[ctenums.CharID, int] = {
    ctenums.CharID.CRONO: 1,
    ctenums.CharID.MARLE: 2,
    ctenums.CharID.LUCCA: 3,
    ctenums.CharID.FROG: 4,
    ctenums.CharID.ROBO: 5,
    ctenums.CharID.AYLA: 6,
    ctenums.CharID.MAGUS: 7
}

_char_music: dict[ctenums.CharID, int] = {
    ctenums.CharID.CRONO: 0x18,
    ctenums.CharID.MARLE: 0x7,
    ctenums.CharID.LUCCA: 0x1B,
    ctenums.CharID.FROG: 0x2A,
    ctenums.CharID.ROBO: 0xE,
    ctenums.CharID.AYLA: 0xB,
    ctenums.CharID.MAGUS: 0x28

}


def determine_scene_status(status_addr: int) -> EF:
    """Determine where the recruit should be positioned."""

    ret_ef = (
        EF().add_if(
            EC.if_flag(memory.Flags.HAS_BURROW_RECRUIT),
            EF().add(EC.assign_val_to_mem(2, status_addr, 1))
            .jump_to_label(EC.jump_forward(), 'end')
        ).add_if(
            EC.if_flag(memory.Flags.HAS_SHOWN_MEDAL),
            EF().add(EC.assign_val_to_mem(1, status_addr, 1))
            .jump_to_label(EC.jump_forward(), 'end')
        ).add(EC.assign_val_to_mem(1, status_addr, 1))
        .set_label('end')
        .add(EC.pause(0))
    )

    return ret_ef


def write_recruit_checks(script: LocationEvent):
    """Write check for masamune to Obj00"""
    pos = script.find_exact_command(EC.return_cmd())

    new_startup = EF().append(determine_scene_status(0x7F0214))
    new_startup.append(
        owu.get_has_equipment_func(ctenums.ItemID.HERO_MEDAL, 0x7F0210)
    )
    new_startup.append(
        owu.get_has_equipment_func(ctenums.ItemID.MASAMUNE_1, 0x7F0212)
    )
    script.insert_commands(new_startup.get_bytearray(), pos)


def write_recruit_startup(
        script: LocationEvent,
        char_id: ctenums.CharID):
    """Write the recruit's startup function."""
    startup = (
        EF().add_if_else(
            EC.if_flag(memory.Flags.HAS_BURROW_RECRUIT),
            EF().add(EC.load_pc_in_party(char_id)),
            EF().add(EC.load_pc_always(char_id))
            .add_if_else(
                EC.if_flag(memory.Flags.HAS_SHOWN_MEDAL),
                EF().add(EC.set_object_coordinates_tile(5, 9))
                .add(EC.set_own_facing('right')),
                EF().add(EC.set_object_coordinates_tile(2, 7))
                .add(EC.set_own_facing('up'))
            )
        ).add(EC.return_cmd())
        .set_label('loop')
        .add_if_else(
            EC.if_flag(memory.Flags.HAS_BURROW_RECRUIT),
            EF().add(EC.set_controllable_infinite()),
            EF().add(EC.break_cmd())
            .jump_to_label(EC.jump_back(), 'loop')
        )
        .add(EC.end_cmd())
    )

    obj_id = _char_objs[char_id]
    script.set_function(obj_id, FID.STARTUP, startup)


def write_recruit_activate(script: LocationEvent,
                           char_id: ctenums.CharID,
                           min_level: typing.Optional[int] = None,
                           min_techlevel: typing.Optional[int] = None,
                           has_medal_addr: int = 0x7F0210,
                           has_masa_addr: int = 0x7F0212,
                           scale_level_to_lead: bool = False,
                           scale_techlevel_to_lead: bool = False,
                           scale_gear: bool = False
                           ):
    """
    Write the recruit's activation function which holds most of the recruit
    logic.
    """

    # Make a separate object to handle the recruitment because the pc object
    # may go dead if the new recruit is not added to the party.
    recruit_obj_id = script.append_empty_object()
    script.set_function(
        recruit_obj_id, FID.STARTUP,
        EF().add(EC.return_cmd()).add(EC.end_cmd())
    )

    script.set_function(recruit_obj_id, FID.TOUCH,
                        EF().add(EC.return_cmd()))

    # Make a separate object for the masamune
    masa_obj = script.append_empty_object()
    script.set_function(
        masa_obj, FID.STARTUP,
        EF().add(EC.load_npc(0x8B))
        .add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd())
        .add(EC.end_cmd())
    )
    script.link_function(masa_obj, FID.ARBITRARY_0,
                         0xB, FID.ARBITRARY_1)

    obj_id = _char_objs[char_id]
    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )

    pc3_addr = 0x7F0300
    recruit_block = (
        EF()
        # .add(EC.call_obj_function(obj_id, FID.ARBITRARY_0, 3, FS.CONT))
        .append(scale_block)
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .add(EC.name_pc(char_id))
        .add_if(
            EC.if_mem_op_value(pc3_addr, OP.LESS_THAN, 7),
            EF().add(EC.set_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
            .add(EC.switch_pcs())
            .add(EC.reset_flag(memory.Flags.KEEP_SONG_ON_SWITCH))
        )
        .add(EC.party_follow())
        .add_if(
            EC.if_not_flag(memory.Flags.OBTAINED_BURROW_LEFT_ITEM),
            EF().add(EC.call_obj_function(9, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 5, FS.CONT))
        )
        .add(EC.return_cmd())
    )

    script.set_function(recruit_obj_id, FID.ARBITRARY_0, recruit_block)

    # noinspection SpellCheckingInspection
    for str_id in (5,     # The hero I am not
                   6,     # Thee hath returned?  The Hero Medal?
                   9,     # The legendary Masamune is required...
                   0x17,  # This sword... Tis the masa
                   0xB,   # Nary a soul remains to mend'eth the Masamune
                   0x1A   # Though we may fail...
                   ):
        script.strings[str_id] = \
            script.strings[str_id].replace(b'\x17', bytes([char_id+0x13]))

    arb_0 = (
        EF().add(EC.load_pc_in_party(char_id))
        .add(EC.return_cmd())
    )
    script.set_function(obj_id, FID.ARBITRARY_0, arb_0)

    activate = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.HAS_BURROW_RECRUIT),
            EF().add(EC.return_cmd())
        )
        .add_if(
            EC.if_mem_op_value(has_masa_addr, OP.EQUALS, 1),
            EF().add(EC.move_party(0x89, 0x8, 0x87, 0x7, 0x87, 0xA))
            .add_if(
                EC.if_not_flag(memory.Flags.HAS_SHOWN_MEDAL),
                EF().add(EC.move_sprite(2, 9))
                .add(EC.move_sprite(5, 9))
            ).add(EC.call_obj_function(masa_obj, FID.ARBITRARY_0, 4, FS.HALT))
            .add(EC.play_animation(9))
            .add(EC.set_move_speed(0x28))
            .add(EC.vector_move(270, 4, False))
            .add(EC.vector_move(90, 4, False))
            .add(EC.auto_text_box(0x17))
            .add(EC.play_animation(0x29)).add(EC.pause(1))
            .add(EC.play_animation(0x2A)).add(EC.pause(1))
            .add(EC.play_animation(0))
            .add(EC.generic_command(0xEB, 20, 00))
            .add(EC.generic_command(0xED))
            .add(EC.play_song(_char_music[char_id]))
            .add(EC.generic_command(0xEB, 88, 0xFF))
            .add(EC.auto_text_box(0x1A))
            .add(EC.set_object_drawing_status(masa_obj, False))
            .add(EC.play_animation(1))
            .add(EC.set_move_destination(True, True))
            .add(EC.set_move_properties(True, True))
            .add(EC.follow_pc_once(0))
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, pc3_addr, 1))
            .add_if_else(
                EC.if_mem_op_value(pc3_addr, OP.LESS_THAN, 7),
                EF().add(EC.add_pc_to_reserve(char_id)),
                EF().add(EC.add_pc_to_active(char_id))
            ).add(EC.load_pc_in_party(char_id))
            .add(EC.set_flag(memory.Flags.HAS_BURROW_RECRUIT))
            .add(EC.set_flag(memory.Flags.HAS_SHOWN_MEDAL))
            .add(EC.call_obj_function(recruit_obj_id, FID.ARBITRARY_0,
                                      5, FS.CONT))
            .jump_to_label(EC.jump_forward(), 'end')
        ).add_if(
            EC.if_not_flag(memory.Flags.HAS_SHOWN_MEDAL),
            EF().add_if_else(
                EC.if_mem_op_value(has_medal_addr, OP.EQUALS, 1),
                EF().add(EC.auto_text_box(6))
                .add(EC.move_sprite(2, 9))
                .add(EC.move_sprite(5, 9))
                .add(EC.auto_text_box(9))
                .add(EC.set_flag(memory.Flags.HAS_SHOWN_MEDAL))
                .add(EC.call_obj_function(9, FID.ARBITRARY_0, 5, FS.CONT))
                .add(EC.call_obj_function(0xA, FID.ARBITRARY_0, 5, FS.CONT)),
                EF().add(EC.auto_text_box(5))
            ).jump_to_label(EC.jump_forward(), 'end')
        )
        .add(EC.auto_text_box(0xB))
        .set_label('end')
        .add(EC.return_cmd())
    )
    script.set_function(obj_id, FID.ACTIVATE, activate)
    script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))


def assign_pc_to_spot(
        char_id: ctenums.CharID,
        script_man: ScriptManager,
        min_level: int = 1,
        min_techlevel: int = 0,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
):
    """Put a recruitable character in Frog's Burrow."""
    script = script_man[ctenums.LocID.FROGS_BURROW]

    # No-recruit default sets this flag so that the chest can open.
    # Remove it if a recruit is present.
    pos = script.find_exact_command(EC.set_flag(memory.Flags.HAS_SHOWN_MEDAL))
    script.delete_commands(pos, 1)

    write_recruit_checks(script)
    write_recruit_startup(script, char_id)
    write_recruit_activate(script, char_id,
                           min_level=min_level,
                           min_techlevel=min_techlevel,
                           scale_level_to_lead=scale_level_to_lead,
                           scale_techlevel_to_lead=scale_techlevel_to_lead,
                           scale_gear=scale_gear)

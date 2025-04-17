"""Alter recruitable character in Leene Square"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.randostate import ScriptManager
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
from ctrando.recruits import recruitassign

from ctrando.strings import ctstrings


def shuffle_pc_arbs(
        script: LocationEvent
):
    """
    Crono and Ayla have specific arbs that should not be overwritten if they
    are the recruit character.
    """

    # Crono Arbs:
    # Arb0 - Collision
    # Arb1 - Movement before drinking game
    # Arb2 - Some waiting function used in drinking game.
    # Arb3 - Drinking animation
    # Arb4 - Candy (REMOVE)
    # Arb5 - Candy (REMOVE)
    # Arb6 - Candy related, calls removed by openworld
    # Arb7 - Not ever called

    # Ayla Arbs:
    # Uses 0, 1, 2 the same as Crono's 1, 2, 3 for drinking

    # The recruit only uses touch, activate, and three arbs.  So the plan
    # is to put them in Crono's Arb4, Arb5, and Arb6 and then link everyone
    # else to those.

    # Then every PC needs a collision function, so we'll use everyone's Arb7.

    # script.set_function(1, FID.ARBITRARY_4, EF())
    # script.set_function(1, FID.ARBITRARY_5, EF())

    script.set_function(1, FID.ARBITRARY_7, EF())
    pc_obj_ids = (1, 2, 4, 5, 6, 7, 8)
    for obj_id in pc_obj_ids:
        script.link_function(obj_id, FID.ARBITRARY_7,
                             1, FID.ARBITRARY_0) 


def change_recruit_item(item: ctenums.ItemID,
                        recruit_char: ctenums.CharID,  # to find obj
                        script_man: ScriptManager):
    """Change the item that the recruit wants.  AFTER assignment."""
    script = script_man[ctenums.LocID.LEENE_SQUARE]
    obj_id = 1 + recruit_char
    func_id = FID.ACTIVATE

    result_addr = 0x7F0250
    check_addr = 0x7F0252

    pos = script.get_function_start(0, FID.ACTIVATE)
    check_item_func = owu.get_has_equipment_func(item, result_addr, check_addr)
    script.insert_commands(check_item_func.get_bytearray(), pos)

    pos = script.get_function_start(obj_id, func_id)
    pos = script.find_exact_command(EC.if_has_item(ctenums.ItemID.PENDANT), pos)
    script.replace_jump_cmd(
        pos, EC.if_mem_op_value(result_addr, OP.EQUALS, 1)
    )
    script.insert_commands(
        EC.call_obj_function(0, FID.ACTIVATE, 1, FS.HALT)
        .to_bytearray(), pos
    )

    for _ in range(2):
        pos, cmd = script.find_command([0xC1], pos)
        str_id = cmd.args[-1]

        ct_str = script.strings[str_id]
        py_str = ctstrings.CTString.ct_bytes_to_ascii(ct_str)
        py_str = py_str.replace('pendant', str(item))
        script.strings[str_id] = ctstrings.CTString.from_str(py_str)

        pos += len(cmd)


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
    Assign a PC to the Milennial Fair spot.
    """

    script = script_man[ctenums.LocID.LEENE_SQUARE]

    # By default, the pendant is always on the ground.  Remove this so the
    # recruit can drop it.
    pos = script.find_exact_command(
        EC.if_not_flag(memory.Flags.FAIR_PENDANT_PICKED_UP)
    )
    script.delete_jump_block(pos)

    char_obj_id = 1+char_id
    if char_id > ctenums.CharID.MARLE:  # Skip over the dummy NPC Marle
        char_obj_id += 1

    # Track the recruit's coordinates instead of Dummy Marle's
    pos = script.find_exact_command(
        EC.get_object_coordinates(3, 0x7F021A, 0x7F021C)
    )
    script.data[pos+1] = 2*char_obj_id

    pos = script.find_exact_command(
        EC.call_obj_function(3, FID.ARBITRARY_2, 3, FS.CONT)
    )
    repl_cmd = EC.call_obj_function(char_obj_id, FID.ARBITRARY_4, 3, FS.CONT)
    script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()

    script.set_function(
        0, FID.ARBITRARY_0,
        EF()
        .add(EC.call_obj_function(char_obj_id, FID.ARBITRARY_5, 1, FS.CONT))
        .add(EC.return_cmd())
    )

    if char_id in (ctenums.CharID.MARLE, ctenums.CharID.LUCCA, ctenums.CharID.AYLA):
        name_part = "GIRL: "
    elif char_id in(ctenums.CharID.CRONO, ctenums.CharID.MAGUS):
        name_part = "BOY: "
    elif char_id == ctenums.CharID.FROG:
        name_part = "FROG: "
    else:
        name_part = "ROBOT: "

    has_item_id = script.add_py_string(
        name_part + "Oh thank goodness!{line break}"
        "My pendant!{null}"
    )
    no_item_id = script.add_py_string(
        name_part + "Uh oh...{line break}"
                    "My pendant!{null}"
    )

    scale_block = owu.get_level_techlevel_set_function(
        char_id, scale_level_to_lead, scale_techlevel_to_lead, scale_gear,
        min_level, min_techlevel
    )
    scale_block.add(EC.return_cmd())
    script.set_function(0, FID.ARBITRARY_1, scale_block)

    script.set_function(char_obj_id, FID.STARTUP,
                        build_recruit_startup(char_id))
    script.set_function(char_obj_id, FID.ACTIVATE,
                        build_recruit_activate(char_id,
                                               ctenums.ItemID.PENDANT,
                                               has_item_id,
                                               no_item_id,
                                               min_level,
                                               min_techlevel,
                                               scale_level_to_lead,
                                               scale_techlevel_to_lead,
                                               scale_gear))
    script.set_function(char_obj_id, FID.TOUCH,
                        build_recruit_touch(char_obj_id))
    script.set_function(char_obj_id, FID.ARBITRARY_4,
                        build_recruit_arb_0())
    script.set_function(char_obj_id, FID.ARBITRARY_5,
                        build_recruit_arb_1())

    shuffle_pc_arbs(script)


def build_recruit_startup(char_id: ctenums.CharID) -> EF:
    """
    Builds the startup function for the pc who should be the fair recruit.
    """
    startup_ef = (
        EF()
        .add_if_else(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            (  # Normal party load
                EF()
                .add(EC.load_pc_in_party(char_id))
            ),
            (  # Else set the npc Marle's initial position
                EF()
                .add(EC.load_pc_always(char_id))
                .add(EC.set_move_speed(0x40))
                .add(EC.set_object_coordinates_tile(0x21, 0x08))
                .add_if(
                    EC.if_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT),
                    (
                        EF()
                        .add(EC.set_object_coordinates_tile(0x1C, 0x0D))
                    )
                )
            )
        )
        .add(EC.return_cmd())
        .set_label('post_return')
        .add_if(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            (  # Normal controllable infinite
                EF()
                .add(EC.set_controllable_infinite())
                .add(EC.end_cmd())
            )
        )
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            (
                EF()
                .add(EC.move_sprite(0x1B, 0x0D))
                .add(EC.set_own_facing('up'))
                .add(EC.loop_animation(0x17, 4))
                .add(EC.move_sprite(0x17, 0x0D))
                .add(EC.loop_animation(0x17, 4))
            )
        )
        .jump_to_label(EC.jump_back(), 'post_return')
    )

    return startup_ef


def build_recruit_activate(
        char_id: ctenums.CharID,
        required_item: ctenums.ItemID,
        has_item_str_id: int,
        no_item_str_id: int,
        min_level: int,
        min_techlevel: int,
        scale_level_to_lead: bool = False,
        scale_techlevel_to_lead: bool = False,
        scale_gear: bool = False
) -> EF:
    """Ask for item or join party."""


    prelim_ef = (
        EF()
        .add(EC.reset_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT))
        .add(EC.call_obj_function(0, FID.ARBITRARY_1, 1,  FS.HALT))
        # .add(EC.break_cmd())
    )

    act_ef = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.HAS_FAIR_RECRUIT),
            EF().add(EC.return_cmd())
        )
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            EF().add(EC.return_cmd())
        )
        .add_if_else(
            EC.if_has_item(required_item),
            EF()
            .add(EC.set_explore_mode(False))
            .add(EC.break_cmd())
            .add(EC.generic_command(0xAE))
            .add(EC.text_box(has_item_str_id))
            .add(EC.play_song(6))  # Fair Song
            .append(prelim_ef)
            .append(
                recruitassign.build_recruit_function(
                    char_id, memory.Flags.HAS_FAIR_RECRUIT, 0x7F0300)
            ),
            EF().add(EC.text_box(no_item_str_id))
        )
        .add(EC.return_cmd())
    )
   
    return act_ef


def build_recruit_touch(recruit_obj_id: int) -> EF:
    """Copied from vanilla.  Collision + item flying"""
    touch_ef = (
        EF()
        .add_if(
            EC.if_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE),
            EF()
            .add(EC.reset_flag(memory.Flags.FAIR_HAS_NOT_BUMPED_MARLE))
            .add(EC.set_explore_mode(False))
            # Make Sparkle fly off
            .add(EC.call_obj_function(0x0E, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.play_song(0))
            # Call to obj 0 -> call to obj 3
            # Will need to keep this object straight in char rando.
            .add(EC.call_obj_function(0, FID.ARBITRARY_0, 1, FS.CONT))
            .add(EC.pause(0.750))
            # Make the cat run away if it's following.
            .add(EC.call_obj_function(0xD, FID.ARBITRARY_0, 3, FS.CONT))
            # Make the bell ring
            .add(EC.call_obj_function(0x12, FID.ARBITRARY_0, 3, FS.CONT))
            .add(EC.pause(0.5))
            .add(EC.set_own_facing('up'))
            .add(EC.loop_animation(0x13, 2))
            .add(EC.set_move_speed(0x20))
            .add(EC.reset_animation())
            .add(EC.follow_pc_once(0))
            .add(EC.set_own_facing_pc(0))
            .add(EC.play_animation(0x1D))
            # .add(EC.static_animation(0x4A))
            .add(EC.pause(0.5))
            .add(EC.reset_animation())
            .add(EC.vector_move(0, 8, False))
            # .add(EC.static_animation(0x53))
            .add(EC.play_animation(0x19))
            .add(EC.pause(0.5))
            .add(EC.pause(0.5))
            .add(EC.reset_animation())
            # .add(EC.set_explore_mode(True))  # Done when Crono wakes
            .add(EC.set_flag(memory.Flags.FAIR_PENDANT_NOT_FOUND))
            .add(EC.set_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT))
            .add(EC.call_obj_function(recruit_obj_id,
                                      FID.ARBITRARY_4, 5, FS.CONT))
                                      # FID.ARBITRARY_0, 5, FS.CONT))
        )
        .add(EC.return_cmd())
    )

    return touch_ef


def build_recruit_arb_0():
    """wander after bump"""
    arb_0 = (
        EF()
        .set_label('start')
        .add_if(
            EC.if_flag(memory.Flags.FAIR_NOT_GIVEN_PENDANT),
            EF()
            .add(EC.move_sprite(0x18, 0xF))
            .add(EC.loop_animation(0x17, 0x3))
            .add(EC.move_sprite(0x1C, 0xD))
            .add(EC.loop_animation(0x17, 0x3))
            .jump_to_label(EC.jump_back(), 'start')
        )
        .add(EC.return_cmd())
    )

    return arb_0


def build_recruit_arb_1():
    """collision w/ PC00"""
    arb_1 = (
        EF()
        # Moved collision to Arb6
        .add(EC.call_pc_function(0, FID.ARBITRARY_7, 3, FS.CONT))
        .add(EC.set_move_speed(0x80))
        .add(EC.generic_command(0xE8, 0x8E))  # sound collision
        # .add(EC.static_animation(0x6A))
        .add(EC.set_own_facing('left'))
        .add(EC.play_animation(5))
        .add(EC.vector_move(0, 4, True))
        .add(EC.pause(1))
        # .add(EC.static_animation(0x49))
        .add(EC.set_own_facing('down'))
        .add(EC.play_animation(0x1D))
        .add(EC.return_cmd())
    )

    return arb_1


def build_recruit_arb_2():
    """collision w/ PC00"""
    arb_2 = (
        EF()
        .add(EC.call_pc_function(0, FID.ARBITRARY_7, 3, FS.CONT))
        .add(EC.set_move_speed(0x80))
        .add(EC.generic_command(0xE8, 0x8E))  # sound collision
        .add(EC.static_animation(0x6A))
        .add(EC.vector_move(0, 4, True))
        .add(EC.pause(1))
        .add(EC.static_animation(0x49))
        .add(EC.return_cmd())
    )

    return arb_2

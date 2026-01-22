"""Make modifications to maps, usually for boss randomization."""
import copy

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationtypes as lt, scriptmanager as sm
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventfunction import EventFunction as EF


def copy_map_data(
        script_manager: sm.ScriptManager,
        loc_exit_dict: dict[ctenums.LocID, list[lt.LocationExit]],
        loc_data_dict: dict[ctenums.LocID, lt.LocationData],
        from_loc_id: ctenums.LocID,
        to_loc_id: ctenums.LocID
):
    """Copy from one location to another.  Keep separate script pointers."""
    to_loc_data = loc_data_dict[to_loc_id]
    orig_event_id = to_loc_data.event_id
    new_to_loc_data = loc_data_dict[from_loc_id].get_copy()
    new_to_loc_data.event_id = orig_event_id

    script_manager[to_loc_id] = copy.deepcopy(script_manager[from_loc_id])
    loc_data_dict[to_loc_id] = new_to_loc_data
    loc_exit_dict[to_loc_id] = copy.deepcopy(loc_exit_dict[from_loc_id])


def make_heckran_boss_map(
        script_manager: sm.ScriptManager,
        loc_exit_dict: dict[ctenums.LocID, list[lt.LocationExit]],
        loc_data_dict: dict[ctenums.LocID, lt.LocationData],
):
    copy_map_data(
        script_manager, loc_exit_dict, loc_data_dict,
        from_loc_id=ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS,
        to_loc_id=ctenums.LocID.HECKRAN_CAVE_BOSS
    )

    # Change the exit from underground river to the boss map
    # This one happens to be exit 4
    river_exits = loc_exit_dict[ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER]
    river_exits[4].destination = ctenums.LocID.HECKRAN_CAVE_BOSS

    # Modify the new map's script to not have the extra enemy objects.
    delete_objs = [0x18, 0x17, 0x16, 0x15, 0x14, 0x13, 0x12, 0x11, 0x10, 0xF,
                   0xE, 0xC, 2, 1]
    delete_objs.sort(reverse=True)

    script = script_manager[ctenums.LocID.HECKRAN_CAVE_BOSS]
    for obj_id in delete_objs:
        script.remove_object(obj_id)

def make_zenan_boss_map(
        script_manager: sm.ScriptManager,
        loc_exit_dict: dict[ctenums.LocID, list[lt.LocationExit]],
        loc_data_dict: dict[ctenums.LocID, lt.LocationData],
):
    """Copy Zenan Bridge to give Zombor his own map.  After base patch."""
    copy_map_data(
        script_manager, loc_exit_dict, loc_data_dict,
        ctenums.LocID.ZENAN_BRIDGE_600,
        ctenums.LocID.ZENAN_BRIDGE_BOSS,
    )

    # Add a warp to the boss location in place of the old cutscene
    orig_zenan_script = script_manager[ctenums.LocID.ZENAN_BRIDGE_600]

    coord_cmd = EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0xB)
    pos = orig_zenan_script.find_exact_command(
        coord_cmd,
        orig_zenan_script.get_function_start(1, FID.STARTUP)
    )
    orig_zenan_script.replace_jump_cmd(
        pos,
        EC.if_mem_op_value(0x7F0212, OP.EQUALS, 0x13)
    )
    pos += len(coord_cmd)

    new_block = (
        EF()
        .add(EC.move_party(0x86, 0x08, 0x88, 0x7, 0x89, 0x0A))
        .add(EC.darken(1))
        .add(EC.fade_screen())
        .add(EC.change_location(ctenums.LocID.ZENAN_BRIDGE_BOSS, 0xB, 0x8))
    )
    orig_zenan_script.insert_commands(
        new_block.get_bytearray(), pos
    )
    pos += len(new_block)
    del_end = orig_zenan_script.find_exact_command(EC.set_explore_mode(True)) + 2
    orig_zenan_script.delete_commands_range(pos, del_end)

    # Remove objects from the boss script
    zenan_boss_script = script_manager[ctenums.LocID.ZENAN_BRIDGE_BOSS]
    del_objs = sorted(
        (0x0D, 0x0E, 0x0F, 0x10, 0x11, 0x12, 0x15, 0x16, 0x17, 0x1D, 0x1E),
        reverse=True
    )
    for obj_id in del_objs:
        zenan_boss_script.remove_object(obj_id)


def make_dream_devourer_map(
        script_manager: sm.ScriptManager,
        loc_exit_dict: dict[ctenums.LocID, list[lt.LocationExit]],
        loc_data_dict: dict[ctenums.LocID, lt.LocationData],
):
    copy_map_data(
        script_manager, loc_exit_dict, loc_data_dict,
        from_loc_id=ctenums.LocID.LAVOS,
        to_loc_id=ctenums.LocID.DARKNESS_BEYOND_TIME
    )

    script = script_manager[ctenums.LocID.DARKNESS_BEYOND_TIME]
    for char_id in ctenums.CharID:
        obj_id = char_id + 1
        func = (
            EF()
            .add(EC.load_pc_in_party(char_id))
            .add_if(
                EC.if_mem_op_value(0x7F020E, OP.EQUALS, char_id),
                EF()
                .add(EC.set_object_coordinates_tile(0x8, 0xD))
            ).add_if(
                EC.if_mem_op_value(0x7F0210, OP.EQUALS, char_id),
                EF()
                .add(EC.set_object_coordinates_tile(0x3, 0xC))
            ).add_if(
                EC.if_mem_op_value(0x7F0212, OP.EQUALS, char_id),
                EF()
                .add(EC.set_object_coordinates_tile(0xD, 0xC))
            )
            .add(EC.set_move_destination(True, False))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )
        script.set_function(obj_id, FID.STARTUP, func)
        pos = script.get_function_start(obj_id, FID.ARBITRARY_3)
        script.insert_commands(
            EF()
            .add(EC.generic_command(0x8E, 0x00))
            .get_bytearray(), pos
        )  # priority

    pos = script.get_object_start(0)
    script.delete_jump_block(pos)
    pos = script.find_exact_command(EC.return_cmd()) + 1
    # script.insert_commands(
    #     EF()
    #     .get_bytearray(), pos
    # )

    num_objs = script.num_objects
    for obj_id in reversed(range(9, num_objs)):
        script.remove_object(obj_id)

    dd_obj_id = script.append_empty_object()
    script.set_function(
        dd_obj_id, FID.STARTUP,
        EF()
        .add(EC.load_enemy(ctenums.EnemyID.DREAM_DEVOURER, 3, True))
        .add(EC.set_object_coordinates_pixels(0x7F, 0x8F))
        .add(EC.generic_command(0x8E, 0x33))
        .add(EC.return_cmd())
        .add(EC.end_cmd())
    )
    script.set_function(
        dd_obj_id, FID.ARBITRARY_0,
        EF()
        .add(EC.generic_command(0xAB, 0x06))
        .add(EC.static_animation(2))
        .add(EC.return_cmd())
    )

    schala_obj_id = script.append_empty_object()
    script.dummy_object_out(schala_obj_id)

    schala_npc_obj_id = script.append_empty_object()
    script.dummy_object_out(schala_npc_obj_id)

    closed_portal_id = owu.insert_portal(
        script, 0x6E, 0x98, 0x70, 0xC0,
        FID.ARBITRARY_3,
        EC.change_location(
            ctenums.LocID.TELEPOD_EXHIBIT, 0x7, 0xC,
        ), None
    )
    pos = script.find_exact_command(
        EC.return_cmd(),
        script.get_function_start(closed_portal_id, FID.STARTUP)
    )
    script.insert_commands(EC.set_own_drawing_status(False).to_bytearray(), pos)

    script.set_function(
        schala_obj_id, FID.STARTUP,
        EF()
        .add(EC.load_enemy(ctenums.EnemyID.SCHALA, 6, True))
        .add(EC.set_object_coordinates_pixels(0x7F, 0x5F))
        .add(EC.generic_command(0x8E, 0x33))
        .add(EC.return_cmd())
        .add(EC.set_own_facing('right'))
        .add(EC.play_animation(6))
        .add(EC.end_cmd())
    )

    script.set_function(
        schala_obj_id, FID.ACTIVATE,
        EF().add(EC.return_cmd())
    )

    script.set_function(
        schala_obj_id, FID.ARBITRARY_0,
        EF()
        .add(EC.shake_screen(True))
        .add(EC.call_obj_function(dd_obj_id, FID.ARBITRARY_0, 4, FS.CONT))
        .add(EC.play_animation(5))
        .add(EC.pause(1))
        .add(EC.set_own_drawing_status(False))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, True))
        .add(EC.pause(0.1))
        .add(EC.set_own_drawing_status(True))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, False))
        .add(EC.pause(0.3))
        .add(EC.set_own_drawing_status(False))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, True))
        .add(EC.pause(0.1))
        .add(EC.set_own_drawing_status(True))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, False))
        .add(EC.pause(0.1))
        .add(EC.set_own_drawing_status(False))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, True))
        .add(EC.pause(0.05))
        .add(EC.set_own_drawing_status(True))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, False))
        .add(EC.pause(0.1))
        .add(EC.set_own_drawing_status(False))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, True))
        .add(EC.set_own_drawing_status(True))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, False))
        .add(EC.set_own_drawing_status(False))
        .add(EC.set_object_drawing_status(schala_npc_obj_id, True))
        .add(EC.shake_screen(False))
        .add(EC.call_obj_function(schala_npc_obj_id, FID.ARBITRARY_0, 4, FS.HALT))
        .add(EC.return_cmd())
    )

    script.set_function(
        schala_npc_obj_id, FID.STARTUP,
        EF()
        .add(EC.load_npc(ctenums.NpcID.SCHALA_TIME_FREEZE))
        .add(EC.set_object_coordinates_pixels(0x7F, 0x5F))
        .add(EC.play_animation(5))
        .add(EC.set_own_drawing_status(False))
        .add(EC.return_cmd())
        .add(EC.end_cmd())
    )
    script.set_function(
        schala_npc_obj_id, FID.ACTIVATE, EF().add(EC.return_cmd())
    )
    script.set_function(
        schala_npc_obj_id, FID.ARBITRARY_0,
        EF()
        .add(EC.reset_animation())
        .add(EC.set_own_facing("down"))
        .add(
            EC.text_box(script.add_py_string(
                "SCHALA: Oi! Why am I blonde? {line break}"
                "And Australian? {null}"
            ), top=False)
        ).add(
            EC.text_box(script.add_py_string(
                "SCHALA: I can't hold it back much longer.{line break}"
                "Get outta here!{null}"
            ), top=False)
        ).add(EC.play_animation(7))
        .add(EC.set_object_drawing_status(closed_portal_id, True))
        .add(EC.call_obj_function(closed_portal_id, FID.ACTIVATE, 4, FS.HALT))
        .add(EC.return_cmd())
    )

    battle_func = (
        EF()
        .add(EC.set_explore_mode(False))
        .add(EC.return_cmd())
        .add(EC.darken(0xF8))
        .add(EC.play_song(0x39))
        .add(EC.fade_screen())
        .add(EC.generic_command(0xD8, 0x91, 0xE0))
        .add(EC.assign_mem_to_mem(memory.Memory.LAST_BATTLE_STATUS, 0x7F0216, 1))
        .add_if(
            EC.if_mem_op_value(0x7F0216, OP.EQUALS, 0),
            EF()
            .add(EC.play_song(0x3A))
            .add(EC.call_obj_function(schala_obj_id, FID.ARBITRARY_0, 4, FS.HALT))
            # .add(EC.party_follow())
            # .add(EC.set_explore_mode(True))
            .add(EC.end_cmd())
        )
        .add(EC.play_song(0x26))
        .add(EC.darken(0x08))
        .add(EC.fade_screen())
        .add(EC.change_location(
            ctenums.LocID.TELEPOD_EXHIBIT, 7, 0xC, wait_vblank=True
        ))
        .add(EC.return_cmd())

    )
    script.set_function(8, FID.STARTUP, battle_func)

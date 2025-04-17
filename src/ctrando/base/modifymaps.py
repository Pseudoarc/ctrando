"""Make modifications to maps, usually for boss randomization."""
import copy

from ctrando.common import ctenums
from ctrando.locations import locationtypes as lt, scriptmanager as sm
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
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


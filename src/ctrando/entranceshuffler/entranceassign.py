"""Assign updated entrance data based on assignment."""
import copy
from dataclasses import dataclass

from ctrando.arguments import entranceoptions
from ctrando.locations import locationtypes, locexitdata, scriptmanager, eventcommand
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.common import ctenums, ctrom, cttypes, memory
from ctrando.entranceshuffler import regionmap
from ctrando.overworlds import owmanager, owexits, oweventcommand, oweventcommandhelper
from ctrando.overworlds.owexitdata import OWExitClass as OWExit


def copy_ow_exit_target(
        from_exit: owexits.OverworldExit,
        to_exit: owexits.OverworldExit
):
    to_exit.dest_facing = from_exit.dest_facing
    to_exit.dest_x = from_exit.dest_x
    to_exit.dest_y = from_exit.dest_y
    to_exit.location = from_exit.location
    to_exit.location_name = from_exit.location_name
    to_exit.half_tile_above = from_exit.half_tile_above
    to_exit.half_tile_left = from_exit.half_tile_left


class ChangeLocCommandBytes(cttypes.BinaryData):
    SIZE = 5

    cmd_id = cttypes.byte_prop(0, 0xFF)
    dest_loc_id = cttypes.bytes_prop(1, 2, 0x01FF,
                                     ret_type=ctenums.LocID)
    facing = cttypes.byte_prop(2, 0x06)
    dest_x = cttypes.byte_prop(3, 0xFF)
    dest_y = cttypes.byte_prop(4, 0xFF)
    half_tile_x = cttypes.byte_prop(2, 0x10)
    half_tile_y = cttypes.byte_prop(2, 0x08)


@dataclass
class ExitTargetData:
    dest_loc_id: ctenums.LocID
    dest_x: int
    dest_y: int
    half_tile_x: bool
    half_tile_y: bool
    facing: eventcommand.Facing

    @classmethod
    def from_event_command(cls, cmd: eventcommand.EventCommand):
        if cmd.command not in eventcommand.EventCommand.change_loc_commands:
            raise TypeError

        cmd_b = ChangeLocCommandBytes(cmd.to_bytearray())

        return cls(
            cmd_b.dest_loc_id, cmd_b.dest_x, cmd_b.dest_y,
            cmd_b.half_tile_x, cmd_b.half_tile_y, cmd_b.facing
        )


def assign_ow_exit_target(
        ow_exit_id: OWExit,
        target_data: owexits.OverworldExit,
        ow_manager: owmanager.OWManager
):
    # Special case for Vortex Pt: Go into the script and change the command.
    if ow_exit_id == OWExit.VORTEX_PT:
        if target_data.location == ctenums.LocID(0x1FF):
            return

        exit_id = OWExit.VORTEX_PT.value[0].value.exit_id
        present = ow_manager[ctenums.OverWorldID.PRESENT]
        exit_data = present.exit_data.exits[exit_id]
        exit_data.location_name = target_data.location_name

        event = present.event

        ptr_id = exit_data.dest_x
        pos = event.labels[present.get_code_ptr_label(ptr_id)]
        pos, cmd = event.find_next_command(oweventcommand.ChangeLocation, pos)
        if not isinstance(cmd, oweventcommand.ChangeLocation):
            raise TypeError

        # Standard exit parameters
        cmd.location = target_data.location
        cmd.x_coord = target_data.dest_x
        cmd.y_coord = target_data.dest_y
        cmd.facing = target_data.dest_facing
        cmd.half_tile_x = target_data.half_tile_left
        cmd.half_tile_y = target_data.half_tile_above
        # Remove the flag for whirlpool entrance in Underground River.
        event.commands[pos] = cmd
        event.delete_commands(pos-1)
    else:  # The usual exit data overwriting.
        for ow_exit in ow_exit_id.value:
            era = ow_exit.value.overworld_id
            index = ow_exit.value.exit_id
            source_exit_data = ow_manager[era].exit_data.exits[index]
            copy_ow_exit_target(target_data, source_exit_data)


def extract_script_exit_target(
        script_exit_info: locexitdata.ScriptExitInfo,
        script_manager: scriptmanager.ScriptManager
) -> ExitTargetData:
    script = script_manager[script_exit_info.loc_id]
    pos = script.get_function_start(
        script_exit_info.obj_id, script_exit_info.func_id
    )

    # print(
    #     script_exit_info.loc_id,
    #     script_exit_info.obj_id,
    #     script_exit_info.func_id
    # )
    # print(script.get_function(script_exit_info.obj_id, script_exit_info.func_id))
    pos, cmd = script.find_command(
        eventcommand.EventCommand.change_loc_commands, pos
    )
    for _ in range(script_exit_info.cmd_id):
        pos += len(cmd)
        pos, cmd = script.find_command(
            eventcommand.EventCommand.change_loc_commands, pos
        )
    return ExitTargetData.from_event_command(cmd)


def gather_loc_exit_data(
        script_manager: scriptmanager.ScriptManager,
        loc_exit_dict: dict[ctenums.LocID, list[locationtypes.LocationExit]]
) -> dict[locexitdata.LocOWExits, ExitTargetData]:

    ret_dict: dict[locexitdata.LocOWExits, ExitTargetData] = dict()
    for loc_exit in locexitdata.LocOWExits:
        # print(f"Trying: {loc_exit}")
        if isinstance(loc_exit.value, locexitdata.LocExitInfo):
            exit_data = loc_exit_dict[loc_exit.value.loc_id][loc_exit.value.index]
            ret_dict[loc_exit] = ExitTargetData(
                exit_data.destination,
                exit_data.dest_x, exit_data.dest_y,
                exit_data.half_left, exit_data.half_above,
                exit_data.destination_facing
            )
        elif isinstance(loc_exit.value, locexitdata.ScriptExitInfo):
            data = extract_script_exit_target(loc_exit.value, script_manager)
            ret_dict[loc_exit] = data
        else:
            raise TypeError
    return ret_dict


def do_actual_loc_ow_assignment(
        loc_exit_id: locexitdata.LocOWExits,
        new_data: ExitTargetData,
        script_manager: scriptmanager.ScriptManager,
        loc_exits: dict[ctenums.LocID, list[locationtypes.LocationExit]]
):
    if isinstance(loc_exit_id.value, locexitdata.LocExitInfo):
        loc_exit = loc_exits[loc_exit_id.value.loc_id][loc_exit_id.value.index]
        loc_exit.destination = new_data.dest_loc_id
        loc_exit.dest_x = new_data.dest_x
        loc_exit.dest_y = new_data.dest_y
        loc_exit.destination_facing = new_data.facing
        loc_exit.half_left = new_data.half_tile_x
        loc_exit.half_above = new_data.half_tile_y
    elif isinstance(loc_exit_id.value, locexitdata.ScriptExitInfo):
        script = script_manager[loc_exit_id.value.loc_id]

        pos, cmd = script.find_command(
            eventcommand.EventCommand.change_loc_commands,
            script.get_function_start(loc_exit_id.value.obj_id, loc_exit_id.value.func_id)
        )
        for _ in range(loc_exit_id.value.cmd_id):
            pos += len(cmd)
            pos, cmd = script.find_command(eventcommand.EventCommand.change_loc_commands, pos)

        # if loc_exit_id.value.loc_id == ctenums.LocID.NORTHERN_RUINS_ENTRANCE:
        #     print(loc_exit_id, "assign"),
        #     print(cmd)

        loc_id = cmd.args[0] & 0x1FFF
        existing_data = ChangeLocCommandBytes(cmd.to_bytearray())
        existing_data.dest_loc_id = new_data.dest_loc_id
        existing_data.dest_x = new_data.dest_x
        existing_data.dest_y = new_data.dest_y
        existing_data.facing = new_data.facing
        # existing_data.half_tile_x = new_data.half_tile_x
        # existing_data.half_tile_y = new_data.half_tile_y
        script.data[pos:pos+existing_data.SIZE] = existing_data

    else:
        raise TypeError


def assign_loc_ow_exit(
        loc_exit_id: locexitdata.LocOWExits,
        new_data: ExitTargetData,
        script_manager: scriptmanager.ScriptManager,
        loc_exits: dict[ctenums.LocID, list[locationtypes.LocationExit]]
):
    loc_exit_class = locexitdata.get_loc_exit_class(loc_exit_id)
    for loc_exit in loc_exit_class:
        do_actual_loc_ow_assignment(loc_exit, new_data, script_manager, loc_exits)


def update_ow_exit_names(ow_manager: owmanager.OWManager):
    """Disambiguate Sun Keeps"""

    name_dict = {
        OWExit.SUN_KEEP_600: "Sun Keep 600",
        OWExit.SUN_KEEP_1000: "Sun Keep 1000",
        OWExit.SUN_KEEP_2300: "Sun Keep 2300",
        OWExit.SUN_KEEP_PREHISTORY: "Sun Keep 65M",
        OWExit.SUN_KEEP_LAST_VILLAGE: "Sun Keep LV",
        OWExit.CHORAS_CARPENTER_600: "Carpenter 600",
        OWExit.CHORAS_CARPENTER_1000: "Carpenter 1000",
        OWExit.DARK_AGES_PORTAL: "Dark Ages Portal",
        OWExit.MEDINA_PORTAL: "Medina Portal"
    }

    for ow_exit_class, name in name_dict.items():
        new_name_id = ow_manager.add_ow_exit_name(name)
        for ow_exit in ow_exit_class.value:
            ow_id = ow_exit.value.overworld_id
            exit_data = ow_manager[ow_id].exit_data.exits[ow_exit.value.exit_id]
            exit_data.location_name = new_name_id


def assign_entrances(
        ow_manager: owmanager.OWManager,
        script_manager: scriptmanager.ScriptManager,
        ow_assign_dict: dict[OWExit, OWExit],
        loc_exits: dict[ctenums.LocID, list[locationtypes.LocationExit]]
):

    update_ow_exit_names(ow_manager)

    orig_ow_manager = copy.deepcopy(ow_manager)

    for source_class, target_class in ow_assign_dict.items():
        if source_class == target_class:
            continue

        target_exit = target_class.value[0]
        target_era = target_exit.value.overworld_id
        target_exit_id = target_exit.value.exit_id
        target_exit_data = orig_ow_manager[target_era].exit_data.exits[target_exit_id]
        if target_class == OWExit.VORTEX_PT:
            target_exit_data.dest_facing = 0
            target_exit_data.location = ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER
            target_exit_data.dest_x = 0x27
            target_exit_data.dest_y = 0x29

        assign_ow_exit_target(source_class, target_exit_data, ow_manager)

        # For now:
        # - Do NOT treat the ends of Zenan 600 as a separate exit class.  In the future
        #   this might change.
        # - Manually assign Zenan 600 South with the same data as North
        if source_class == OWExit.ZENAN_BRIDGE_600_NORTH:
            assign_ow_exit_target(OWExit.ZENAN_BRIDGE_600_SOUTH, target_exit_data, ow_manager)

    vanilla_exit_connectors = regionmap.get_default_exit_connectors()
    vanilla_exit_dict = {
        connector.from_exit: connector.to_exit
        for connector in vanilla_exit_connectors
    }
    vanilla_loc_exit_data = gather_loc_exit_data(script_manager, loc_exits)

    for ow_exit_src, ow_exit_target in ow_assign_dict.items():
        # print(f"{ow_exit_src} -> {ow_exit_target}")
        src_loc_exit = vanilla_exit_dict[ow_exit_src]
        target_loc_exit = vanilla_exit_dict[ow_exit_target]

        source_ow = vanilla_loc_exit_data[src_loc_exit]
        assign_loc_ow_exit(target_loc_exit, source_ow, script_manager, loc_exits)


def post_assignment_update_scripts(
        ow_exit_assign_dict: dict[OWExit ,OWExit],
        script_manager: scriptmanager.ScriptManager
):
    """
    Update scripts which force back to the world map.
    - Remove OW flag setting from Denadoro wind exit (unless vanilla)
    - Remove alternate exits from DA portal
    - Epoch Reborn needs to exit to the proper overworld.
    - Dactyl nest should place dactyls in prehistory but not set them as active.
    - NR needs to set load contingent on new exit overworlds
    - Tyrano Lair needs to just return to the entrance.
    - Clean up Magus Lair end scene (keepsong)
    - Make Robo only appear in Fiona's shrine after Desert (?)
    - Remove recruit scene from post-manoria castle 600
    """

    # Denadoro Wind Exit
    wind_exit_dat = locexitdata.LocOWExits.DENADORO_WIND.value
    script = script_manager[wind_exit_dat.loc_id]
    pos = script.get_function_start(wind_exit_dat.obj_id, wind_exit_dat.func_id)
    pos = script.find_exact_command(EC.set_flag(memory.Flags.OW_RIDE_WIND))
    script.delete_commands(pos, 1)

    # Dark Ages Portal
    da_portal_exit_dat = locexitdata.LocOWExits.DARK_AGES_PORTAL_DEFAULT.value
    script = script_manager[da_portal_exit_dat.loc_id]
    pos = script.get_function_start(da_portal_exit_dat.obj_id, da_portal_exit_dat.func_id)
    pos = script.find_exact_command(EC.if_not_flag(memory.Flags.ZEAL_HAS_FALLEN), pos)
    script.delete_commands(pos)
    pos, _ = script.find_command([0x10], pos)
    end, _ = script.find_command([0x11], pos)
    script.delete_commands_range(pos, end)

    # Epoch Reborn -- Always flight on Present
    script = script_manager[ctenums.LocID.REBORN_EPOCH]
    pos = script.get_function_start(9, FID.ACTIVATE)
    cmd = EC.set_flag(memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS)
    pos = script.find_exact_command(cmd, pos)
    pos = script.find_exact_command(EC.if_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD), pos)
    script.delete_jump_block(pos)
    script.delete_commands(pos, 2)
    script.insert_commands(
        EF()
        .add(EC.assign_val_to_mem(
            ctenums.LocID.OW_PRESENT, memory.Memory.EPOCH_MAP_LO, 2)
         ).add(EC.change_location(ctenums.LocID.OW_PRESENT, 0x7F, 0x38,
                                  0, 0, True))
        .get_bytearray(), pos
    )

    # Dactyl Nest -  Set Dactyl on map, but return to (randomized) entrance
    script = script_manager[ctenums.LocID.DACTYL_NEST_SUMMIT]
    cmd = EC.set_flag(memory.Flags.OBTAINED_DACTYLS)
    pos = script.find_exact_command(EC.set_flag(memory.Flags.OBTAINED_DACTYLS))
    pos += len(cmd)
    script.delete_commands(pos, 7)
    script.insert_commands(
        EF()
        .add(EC.assign_val_to_mem(0x80, memory.Memory.DACTYL_STATUS, 1))
        .add(EC.assign_val_to_mem(0x0218, memory.Memory.DACTYL_X_COORD_LO, 2))
        .add(EC.assign_val_to_mem(0x0128, memory.Memory.DACTYL_Y_COORD_LO, 2))
        .get_bytearray(), pos
    )

    # print(script.get_function(0x0, FID.STARTUP))
    # input()

    nr_1000_era = nr_600_era = None
    for ow_exit_src, ow_exit_target in ow_exit_assign_dict.items():
        if ow_exit_target == OWExit.NORTHERN_RUINS_1000:
            nr_1000_era = ow_exit_src.value[0].value.overworld_id
        elif ow_exit_target == OWExit.NORTHERN_RUINS_600:
            nr_600_era = ow_exit_src.value[0].value.overworld_id

    if nr_1000_era is None or nr_600_era is None:
        raise ValueError

    script = script_manager[ctenums.LocID.NORTHERN_RUINS_ENTRANCE]
    script_addr = 0x7F0200 + 0x0B*2
    pos = script.find_exact_command(
        EC.if_mem_op_value(script_addr, OP.EQUALS, ctenums.LocID.OW_PRESENT,2 )
    )
    script.replace_jump_cmd(
        pos,
        EC.if_mem_op_value(script_addr, OP.EQUALS, 0x1F0 + nr_1000_era, 2)
    )
    pos += len(EC.if_mem_op_value(script_addr, OP.EQUALS, 0x1F0 + nr_1000_era, 2))

    pos = script.find_exact_command(
        EC.if_mem_op_value(script_addr, OP.EQUALS, ctenums.LocID.OW_MIDDLE_AGES, 2),
        pos
    )
    script.replace_jump_cmd(
        pos,
        EC.if_mem_op_value(script_addr, OP.EQUALS, 0x1F0 + nr_600_era, 2)
    )

    # Tyrano Lair - No cutscene, just return to the entrance.
    # The entrance shuffler does this, but we need to remove a keepsong and add a fade.
    tyrano_end_exit = locexitdata.LocOWExits.TYRANO_LAIR_END_SCENE
    script = script_manager[tyrano_end_exit.value.loc_id]
    obj_id, fn_id = tyrano_end_exit.value.obj_id, tyrano_end_exit.value.func_id
    pos = script.find_exact_command(
        EC.assign_val_to_mem(1, memory.Memory.KEEPSONG, 1),
        script.get_function_start(obj_id, fn_id)
    )
    script.delete_commands(pos, 2)
    script.insert_commands(EC.darken(0x01).to_bytearray(), pos)

    # For whatever reason, the 0xDF changelocation will mess up the next transition
    # Something about skipping the cutscene/prehistoric canyon.
    # Changing to a 0xE1 changeloc works.
    pos, _ = script.find_command([0xDF], pos)
    script.data[pos] = 0xE1

    # Magus Castle - Clean up ending cutscene
    magus_end_exit = locexitdata.LocOWExits.MAGUS_LAIR_END_SCENE_EPOCH
    script = script_manager[magus_end_exit.value.loc_id]
    obj_id, fn_id = magus_end_exit.value.obj_id, magus_end_exit.value.func_id
    pos = script.get_function_start(obj_id, fn_id)
    pos, cmd = script.find_command(eventcommand.EventCommand.change_loc_commands, pos)
    for __ in range(magus_end_exit.value.cmd_id):
        pos += len(cmd)
        pos, cmd = script.find_command(eventcommand.EventCommand.change_loc_commands, pos)

    script.insert_commands(
        EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1).to_bytearray(),
        pos
    )
    # print(script.get_function(obj_id, fn_id))
    # input()

    # Guardia Throne 600 -- Remove the scene that plays upon return
    script = script_manager[ctenums.LocID.GUARDIA_THRONEROOM_600]
    pos = script.get_object_start(0)
    script.insert_commands(EC.set_flag(memory.Flags.MANORIA_RETURN_SCENE_COMPLETE)
                           .to_bytearray(), pos)

    remove_epoch_teleports(script_manager)


def update_overworlds(
        ow_manager: owmanager.OWManager
):
    """
    - Never disable the Magus castle exit.
    - Never disable the Sunken Desert exit
    - NO: Default Lavos Crash in Preshistory.  Do this with starting rewards.
    - Break up Zenan Bridge 1000 (?)
    """

    # Magus Castle Exit
    script = ow_manager[ctenums.OverWorldID.MIDDLE_AGES].event

    pos = script.find_next_exact_command(
        oweventcommand.SetExitInactive(exit_index=9)
    )
    script.delete_commands(pos-1, pos+1)

    # Sunken Desert Exit
    pos = script.find_next_exact_command(
        oweventcommandhelper.branch_if_flag_set(memory.Flags.OW_SUNKEN_DESERT_COMPLETE)
    )
    script.delete_commands(pos, pos+1)


def remove_epoch_teleports(
        script_manager: scriptmanager.ScriptManager
):
    """
    Remove blocks which change the Epoch's map or coordinates.
    - Heckran's Cave (Boss version of Passageways)
    - Fiona's Villa after Desert Quest
    - Magus's Castle Inner Sanctum after boss
    - Manoria Command after Yakra
    - Sun Keep 2300 after Sunstone pickup
    - Prehistoric Canyon not needed because the scene is skipped
    - Reborn Epoch already taken care of
    """

    # Heckran Cave
    script = script_manager[ctenums.LocID.HECKRAN_CAVE_BOSS]
    pos = script.get_object_start(1)
    pos = script.find_exact_command(
        EC.assign_val_to_mem(0x1F0, memory.Memory.EPOCH_MAP_LO, 2),
        pos
    )
    script.delete_commands(pos, 4)

    # Fiona's Villa
    script = script_manager[ctenums.LocID.FIONAS_VILLA]
    pos = script.get_object_start(8)
    pos = script.find_exact_command(
        EC.assign_mem_to_mem(memory.Memory.EPOCH_STATUS, 0x7F0220, 1),
        pos
    )
    script.delete_commands(pos, 8)

    # Magus's Castle Inner Sanctum
    script = script_manager[ctenums.LocID.MAGUS_CASTLE_INNER_SANCTUM]
    pos = script.get_function_start(9, FID.ACTIVATE)
    pos = script.find_exact_command(
        EC.assign_val_to_mem(0x1F4, memory.Memory.EPOCH_MAP_LO, 2)
    )
    script.delete_commands(pos, 4)

    # Manoria Command
    script = script_manager[ctenums.LocID.MANORIA_COMMAND]
    pos = script.find_exact_command(
        EC.assign_val_to_mem(0x1F1, memory.Memory.EPOCH_MAP_LO, 2),
        script.get_function_start(0xC, FID.ACTIVATE)
    )
    script.delete_commands(pos, 4)

    # Sun Keep 2300 after Sun Stone
    script = script_manager[ctenums.LocID.SUN_KEEP_2300]
    pos = script.find_exact_command(
        EC.assign_val_to_mem(0x1F0, memory.Memory.EPOCH_MAP_LO, 2),
        script.get_function_start(8, FID.ACTIVATE)
    )
    script.delete_commands(pos, 3)


def apply_entrance_rando(
        entrance_settings: entranceoptions.EntranceShufflerOptions,
        overworld_manager: owmanager.OWManager,
        script_manager: scriptmanager.ScriptManager,
        ow_exit_assignment_dict: dict[OWExit, OWExit],
        loc_exit_dict: dict[ctenums.LocID, list[locationtypes.LocationExit]]
):
    if not entrance_settings.shuffle_entrances:
        return

    assign_entrances(
        overworld_manager, script_manager, ow_exit_assignment_dict, loc_exit_dict
    )
    post_assignment_update_scripts(ow_exit_assignment_dict, script_manager)
    update_overworlds(overworld_manager)

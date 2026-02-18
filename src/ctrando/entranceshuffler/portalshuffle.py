"""Module for shuffling portal destinations"""
import dataclasses
from collections.abc import Sequence
import copy
import itertools

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory, random
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID, get_command
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locexitdata import PortalExits, ScriptExitInfo
from ctrando.logic import logictypes
from ctrando.entranceshuffler import regionmap

from ctrando.strings import ctstrings

_portal_region_dict: dict[PortalExits, str] = {
    PortalExits.TELEPOD_EXHIBIT: "millennial_fair",
    PortalExits.TRUCE_CANYON: "truce_canyon",
    PortalExits.GUARDIA_FOREST: "guardia_forest_1000",
    PortalExits.BANGOR_DOME: "bangor_dome",
    PortalExits.MEDINA_CLOSET: "medina_portal",
    PortalExits.MYSTIC_MTS: "mystic_mts",
    PortalExits.DARK_AGES_CAVE: "dark_ages_portal",
    PortalExits.LAIR_RUINS: "lair_ruins_portal",
    PortalExits.PROTO_DOME: "proto_dome_portal"
}


def verify_portal_dict(
        portal_dict: dict[PortalExits, PortalExits]
):
    proto_found = False

    for portal, target in portal_dict.items():
        if target == PortalExits.PROTO_DOME:
            if proto_found:
                raise ValueError("Multiple self-portals")
            proto_found = True
        elif portal_dict[target] != portal:
            raise ValueError("Portals must be paired")

    if len(set(portal_dict.values())) != len(PortalExits):
        raise ValueError("Unassigned Portals")


def get_random_portal_assignment(
        rng: random.RNGType
) -> dict[PortalExits, PortalExits]:
    pool = list(PortalExits)
    assignment: dict[PortalExits, PortalExits] = {}
    rng.shuffle(pool)

    it = itertools.batched(pool, 2)
    for item in it:
        if len(item) == 2:
            x, y = item
            assignment[x] = y
            assignment[y] = x
        elif len(item) == 1:
            x = item[0]
            assignment[x]=x

    verify_portal_dict(assignment)
    return assignment


def update_portal_activation(
        script: LocationEvent,
        script_exit_info: ScriptExitInfo,
        orig_flag: memory.Flags | None,
        new_flags: Sequence[memory.Flags],
        new_change_location_cmd: EC,
        num_del_commands: int = 1,
):

    pos, end = script.get_function_bounds(
        script_exit_info.obj_id, script_exit_info.func_id)

    # If there is no old flag to delete, insert the flags when the portal appears
    if orig_flag is None:
        # The first 0xFF command opens the portal.
        # Guaranteed to be a successful portal activation
        pos, _ = script.find_command([0xFF], pos, end)
    else:
        pos = script.find_exact_command(EC.set_flag(orig_flag), pos, end)

    new_block = EF()
    for flag in new_flags:
        new_block.add(EC.set_flag(flag))

    script.insert_commands(new_block.get_bytearray(), pos)
    pos += len(new_block)
    script.delete_commands(pos, num_del_commands)

    pos = script.get_function_start(script_exit_info.obj_id, script_exit_info.func_id)
    for ind in range(script_exit_info.cmd_id+1):
        pos, cmd = script.find_command(EC.change_loc_commands, pos)
        if ind == script_exit_info.cmd_id:
            script.replace_command_at_pos(pos, new_change_location_cmd)
        else:
            pos += len(cmd)


@dataclasses.dataclass()
class PortalFlagData:
    flag: memory.Flags | None
    num_delete: int


_orig_flag_data_dict: dict[PortalExits, PortalFlagData] = {
    PortalExits.PROTO_DOME: PortalFlagData(None, 0),
    PortalExits.MYSTIC_MTS: PortalFlagData(None, 0),
    PortalExits.MEDINA_CLOSET: PortalFlagData(None, 0),
    PortalExits.TRUCE_CANYON: PortalFlagData(memory.Flags.HAS_TRUCE_PORTAL, 1),
    PortalExits.TELEPOD_EXHIBIT: PortalFlagData(memory.Flags.HAS_TRUCE_PORTAL, 1),
    PortalExits.GUARDIA_FOREST: PortalFlagData(memory.Flags.HAS_BANGOR_PORTAL, 1),
    PortalExits.BANGOR_DOME: PortalFlagData(memory.Flags.HAS_BANGOR_PORTAL, 1),
    PortalExits.DARK_AGES_CAVE: PortalFlagData(memory.Flags.HAS_DARK_AGES_PORTAL, 1),
    PortalExits.LAIR_RUINS: PortalFlagData(memory.Flags.HAS_LAIR_RUINS_PORTAL, 2)
}

def update_portal_activation_scripts(
        script_manager: ScriptManager,
        portal_pairs: list[tuple[PortalExits, PortalExits]],
        flags: Sequence[memory.Flags | None]
):
    """
    Modify the script to change from_portal to have to_portal's target.
    Will trigger the given pillar in EoT.
    """

    # These are commands for going TO the specified portal.
    change_loc_commands_dict = collect_change_loc_commands(script_manager)
    eot_command = get_command(bytes.fromhex("DDD0030D0A"))

    eot_portal: PortalExits = PortalExits.PROTO_DOME

    for (portal1, portal2), pillar_flag in zip(portal_pairs, flags):
        new_flags: list[memory.Flags] = []
        if pillar_flag is not None:
            new_flags.append(pillar_flag)

        if portal1 == portal2:  # EoT
            script = script_manager[portal1.value.loc_id]
            flag_data = _orig_flag_data_dict[portal1]
            update_portal_activation(
                script, portal1.value,
                flag_data.flag, new_flags,
                eot_command,
                flag_data.num_delete
            )
            if portal1 != PortalExits.PROTO_DOME:
                eot_portal = portal1
        else:
            it = itertools.permutations((portal1, portal2))
            for (source, target) in it:
                script = script_manager[source.value.loc_id]
                source_flags = list(new_flags)
                if source == PortalExits.LAIR_RUINS:
                    source_flags.append(memory.Flags.HAS_LAIR_RUINS_PORTAL)

                flag_data = _orig_flag_data_dict[source]
                update_portal_activation(
                    script, source.value,
                    flag_data.flag, source_flags,
                    change_loc_commands_dict[target],
                    flag_data.num_delete
                )
    if eot_portal != PortalExits.PROTO_DOME:
        make_proto_portal_normal(script_manager, eot_command)
        pillar_flag = _portal_enter_flag_dict[eot_portal]
        script = script_manager[eot_portal.value.loc_id]
        fix_new_eot_portal(script, eot_portal.value, pillar_flag)


def collect_change_loc_commands(
        script_manager: ScriptManager
) -> dict[PortalExits, EC]:
    """Get commands for going TO each portal"""
    ret_dict: dict[PortalExits, EC] = {}
    for portal_exit in PortalExits:
        if portal_exit == PortalExits.PROTO_DOME:
            # Manually read the command to Bangor
            ret_dict[portal_exit] = get_command(bytes.fromhex("DDE3021805"))
        else:
            script = script_manager[portal_exit.value.loc_id]

            pos = script.get_function_start(
                portal_exit.value.obj_id, portal_exit.value.func_id
            )

            for ind in range(portal_exit.value.cmd_id+1):
                pos, cmd = script.find_command(EC.change_loc_commands, pos)
                if ind == portal_exit.value.cmd_id:
                    ret_dict[portal_exit] = cmd
                    break
                else:
                    pos += len(cmd)

    vanilla_pairs = (
        (PortalExits.MEDINA_CLOSET, PortalExits.MYSTIC_MTS),
        (PortalExits.TRUCE_CANYON, PortalExits.TELEPOD_EXHIBIT),
        (PortalExits.GUARDIA_FOREST, PortalExits.BANGOR_DOME),
        (PortalExits.LAIR_RUINS, PortalExits.DARK_AGES_CAVE)
    )

    # dict contains going OUT change location.
    # So read the command from the opposite gate.
    for (x, y) in vanilla_pairs:
        ret_dict[x], ret_dict[y] = ret_dict[y], ret_dict[x]

    return ret_dict


_portal_enter_flag_dict = {
        PortalExits.PROTO_DOME: memory.Flags.ENTERING_EOT_FACTORY,
        PortalExits.MEDINA_CLOSET: memory.Flags.ENTERING_EOT_MEDINA,
        PortalExits.MYSTIC_MTS: memory.Flags.ENTERING_EOT_MYSTIC_MTS,
        PortalExits.TELEPOD_EXHIBIT: memory.Flags.ENTERING_EOT_FAIR,
        PortalExits.TRUCE_CANYON: memory.Flags.ENTERING_EOT_TRUCE,
        PortalExits.GUARDIA_FOREST: memory.Flags.ENTERING_EOT_FOREST,
        PortalExits.BANGOR_DOME: memory.Flags.ENTERING_EOT_BANGOR,
        PortalExits.LAIR_RUINS: memory.Flags.ENTERING_EOT_TYRANO_RUINS,
        PortalExits.DARK_AGES_CAVE: memory.Flags.ENTERING_EOT_DARK_AGES
    }


def rewrite_eot_pillars(
        script_manager: ScriptManager,
        pairs: list[tuple[PortalExits, PortalExits]],
        flags: Sequence[memory.Flags],
):
    script = script_manager[ctenums.LocID.END_OF_TIME]

    copy_tiles_cmd_id = 0xE4
    pos = script.find_exact_command(
        EC.if_flag(memory.Flags.HAS_LAIR_RUINS_PORTAL),
        script.get_function_start(0, FID.ACTIVATE)
    )
    script.replace_jump_cmd(
        pos,
        EC.if_flag(memory.Flags.HAS_DARK_AGES_PORTAL)
    )

    # proto, medina, mystic, leene, truce, forest, bangor, tyran, earthbound
    # From object 0xF
    pos = script.get_function_start(0xF, FID.ACTIVATE)
    portals = [
        PortalExits.PROTO_DOME,
        PortalExits.MEDINA_CLOSET, PortalExits.MYSTIC_MTS,
        PortalExits.TELEPOD_EXHIBIT, PortalExits.TRUCE_CANYON,
        PortalExits.GUARDIA_FOREST, PortalExits.BANGOR_DOME,
        PortalExits.LAIR_RUINS, PortalExits.DARK_AGES_CAVE,
    ]

    @dataclasses.dataclass
    class PillarData:
        dec_box_cmd: EC
        change_loc_cmd: EC

    pillar_data_dict: dict[PortalExits, PillarData] = {}

    for portal, obj_id in zip(portals, range(0xF, 0x18)):
        pos = script.get_function_start(obj_id, FID.STARTUP)
        pos, cmd = script.find_command([0xC3], pos)
        dec_box_cmd = cmd

        pos, loc_cmd = script.find_command(EC.change_loc_commands, pos)
        pillar_data_dict[portal] = PillarData(dec_box_cmd, loc_cmd)

    flag_obj_dict: dict[memory.Flags | None, int] = {
        None: 0x10,
        memory.Flags.HAS_TRUCE_PORTAL: 0x12,
        memory.Flags.HAS_BANGOR_PORTAL: 0x14,
        memory.Flags.HAS_DARK_AGES_PORTAL: 0x16
    }

    pillar_order = (
        memory.Flags.ENTERING_EOT_FACTORY,
        memory.Flags.ENTERING_EOT_MEDINA, None, memory.Flags.ENTERING_EOT_MYSTIC_MTS,
        memory.Flags.ENTERING_EOT_FAIR, memory.Flags.ENTERING_EOT_TRUCE,
        memory.Flags.ENTERING_EOT_FOREST, memory.Flags.ENTERING_EOT_BANGOR,
        memory.Flags.ENTERING_EOT_TYRANO_RUINS, memory.Flags.ENTERING_EOT_DARK_AGES
    )

    # entering flag order
    # proto, medina, [bucket], mystic, telepod, truce, forest, bangor, tyrano, dark
    pillar_flag_enter_flag_dict: dict[memory.Flags | None, tuple[memory.Flags, memory.Flags]] = {
        memory.Flags.HAS_BANGOR_PORTAL: (memory.Flags.ENTERING_EOT_FOREST,
                                         memory.Flags.ENTERING_EOT_BANGOR),
        memory.Flags.HAS_TRUCE_PORTAL: (memory.Flags.ENTERING_EOT_FAIR,
                                        memory.Flags.ENTERING_EOT_TRUCE),
        memory.Flags.HAS_DARK_AGES_PORTAL: (memory.Flags.ENTERING_EOT_TYRANO_RUINS,
                                            memory.Flags.ENTERING_EOT_DARK_AGES),
        None: (memory.Flags.ENTERING_EOT_MEDINA, memory.Flags.ENTERING_EOT_MYSTIC_MTS)
    }

    pillar_reassign_dict: dict[memory.Flags | None, memory.Flags | None] = {
        x: None for x in pillar_order
    }

    for ind, ((part1, part2), flag) in enumerate(zip(pairs, flags)):
        if part1 == part2:  # Proto -> EoT reassign
            objs = [0xF]
            data = [pillar_data_dict[part1]]
            orig_flags = [_portal_enter_flag_dict[part1]]
            new_flags = [memory.Flags.ENTERING_EOT_FACTORY]
        else:
            start_obj = flag_obj_dict[flag]
            objs = [start_obj, start_obj+1]
            data = [pillar_data_dict[part1], pillar_data_dict[part2]]
            orig_flags = [
                _portal_enter_flag_dict[part] for part in (part1, part2)
            ]
            new_flags = pillar_flag_enter_flag_dict[flag]

        for orig_flag, new_flag in zip(orig_flags, new_flags):
            pillar_reassign_dict[new_flag] = orig_flag

        for obj, datum in zip(objs, data):
            pos = script.get_function_start(obj, FID.STARTUP)
            pos, cmd = script.find_command([0xC3], pos)
            script.replace_command_at_pos(pos, datum.dec_box_cmd)

            pos, _ = script.find_command(EC.change_loc_commands, pos)
            script.replace_command_at_pos(pos, datum.change_loc_cmd)

    # Reassign pillar entries
    pos = script.find_exact_command(
        EC.if_flag(memory.Flags.ENTERING_EOT_FACTORY),
        script.get_function_start(0, FID.ACTIVATE)
    )

    for flag in pillar_order:
        pos, cmd = script.find_command([0x16], pos)

        if flag is not None:
            old_cmd = EC.if_flag(flag)
            new_flag = pillar_reassign_dict[flag]
            script.replace_jump_cmd(pos, EC.if_flag(new_flag))

            pos, _ = script.find_command([0x66], pos)
            script.replace_command_at_pos(pos, EC.reset_flag(new_flag))
        else:
            pos += len(cmd)



def fix_new_eot_portal(
        script: LocationEvent,
        script_exit_info: ScriptExitInfo,
        pillar_flag: memory.Flags
):
    pos = script.get_function_start(script_exit_info.obj_id, script_exit_info.func_id)
    for ind in range(script_exit_info.cmd_id + 1):
        pos, cmd = script.find_command(EC.change_loc_commands, pos)
        if ind == script_exit_info.cmd_id:
            script.insert_commands(EC.set_flag(pillar_flag).to_bytearray(), pos)
            break
        else:
            pos += len(cmd)


def make_proto_portal_normal(
        script_man: ScriptManager,
        change_loc_eot_cmd: EC
):
    """
    change_loc_eot_cmd is the command going to EoT.
    """
    script = script_man[ctenums.LocID.PROTO_DOME_PORTAL]
    can_eot_addr = 0x7F0234
    temp_addr = 0x7F0236

    can_eot_block = owu.get_can_eot_func(temp_addr, can_eot_addr)
    script.insert_commands(
        can_eot_block.get_bytearray(), script.get_object_start(0)
    )

    pos = script.get_function_start(
        PortalExits.PROTO_DOME.value.obj_id,
        PortalExits.PROTO_DOME.value.func_id
    )
    pos, cmd = script.find_command(EC.change_loc_commands, pos)

    new_block = (
        EF()
        .add_if_else(
            EC.if_mem_op_value(can_eot_addr, OP.EQUALS, 0),
            EF().add(cmd),
            EF().add(change_loc_eot_cmd)
        )
    )
    script.insert_commands(new_block.get_bytearray(), pos)
    pos += len(new_block)
    script.delete_commands(pos, 1)


def get_portal_pairs(
        portal_assignment: dict[PortalExits, PortalExits]
) -> list[tuple[PortalExits, PortalExits]]:
    eot_portal = [portal for portal, target in portal_assignment.items()
                  if target == portal][0]
    portal_pool = list(PortalExits)
    used_portals = [eot_portal]

    portal_pairs: list[tuple[PortalExits, PortalExits]] = []
    for portal, target in portal_assignment.items():
        if portal in used_portals:
            continue

        used_portals += [portal, target]
        portal_pairs.append((portal, target))

    portal_pairs.append((eot_portal, eot_portal))

    return portal_pairs


def get_pair_flags(
        portal_pairs: list[tuple[PortalExits, PortalExits]],
        region_map: regionmap.RegionMap
) -> tuple[memory.Flags | None, ...]:
    """Read the pillar pair flags from the region_map"""
    flags: list[memory.Flags | None] = []
    possible_flags = [memory.Flags.HAS_TRUCE_PORTAL, memory.Flags.HAS_BANGOR_PORTAL,
                      memory.Flags.HAS_DARK_AGES_PORTAL, memory.Flags.HAS_LAIR_RUINS_PORTAL]

    def get_portal_flag(rewards: list) -> memory.Flags | None:
        portal_flags = [x for x in rewards if x in possible_flags]
        if len(portal_flags) > 1:
            raise ValueError
        if len(portal_flags) == 0:
            return None
        return portal_flags[0]

    for (portal1, portal2) in portal_pairs:
        name1 = _portal_region_dict[portal1]
        name2 = _portal_region_dict[portal2]

        flag1 = get_portal_flag(region_map.loc_region_dict[name1].region_rewards)
        flag2 = get_portal_flag(region_map.loc_region_dict[name2].region_rewards)

        if flag1 != flag2:
            raise ValueError("Region flag mismatch.")

        flags.append(flag1)

    return tuple(flags)


def shuffle_map_portals(
        region_map: regionmap.RegionMap,
        portal_assignment: dict[PortalExits, PortalExits],
):
    """
    Modify regions and connectors to reflect new portal pairings.
    Should be part of config generation.
    """

    portal_pairs = get_portal_pairs(portal_assignment)
    assigned_portal_flags: tuple[memory.Flags | None, ...] = (
        memory.Flags.HAS_TRUCE_PORTAL,
        memory.Flags.HAS_BANGOR_PORTAL,
        memory.Flags.HAS_DARK_AGES_PORTAL,
        None, None
    )

    # get the normal portal and EoT portal rules
    portal_rule: logictypes.LogicRule | None = None
    normal_eot_rule: logictypes.LogicRule | None = None
    proto_eot_rule: logictypes.LogicRule | None = None

    # Use fair -> canyon to read the right logic rules for normal portals
    # Could depend on settings such as locked gates.
    connectors = region_map.name_connector_dict["millennial_fair"]
    for connector in connectors:
        if connector.to_region_name == "truce_canyon":
            portal_rule = copy.deepcopy(connector.rule)
        elif connector.to_region_name == "end_of_time":
            normal_eot_rule = copy.deepcopy(connector.rule)

    # Use proto -> eot to read the logic rule for eot
    connectors = region_map.name_connector_dict["proto_dome_portal"]
    for connector in connectors:
        if connector.to_region_name == "end_of_time":
            proto_eot_rule = copy.deepcopy(connector.rule)

    if any(x is None for x in (portal_rule, normal_eot_rule, proto_eot_rule)):
        raise ValueError("Failed to find all portal rules")


    total_portal_flags = [
        memory.Flags.HAS_TRUCE_PORTAL, memory.Flags.HAS_BANGOR_PORTAL,
        memory.Flags.HAS_DARK_AGES_PORTAL, memory.Flags.HAS_LAIR_RUINS_PORTAL,
        memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS
    ]

    # Note Dark Ages/Lair Ruins portal flags are combined now.
    # Traveling to Lair Ruins portal may require a house warp to escape if
    # the lair is not yet destroyed.
    portal_target_regions = set(_portal_region_dict.values())
    portal_target_regions.add("end_of_time")

    pillar_connectors: list[regionmap.RegionConnector] = []
    portal_target_names = ["end_of_time"] + list(_portal_region_dict.values())

    for pair, portal_flag in zip(portal_pairs, assigned_portal_flags):
        true_len = len(list(set(pair)))
        for ind, portal in enumerate(pair[:true_len]):
            # Gather a new pillar connector
            portal_region_name = _portal_region_dict[portal]
            if portal_flag is None:
                rule = logictypes.LogicRule()
            else:
                rule = logictypes.LogicRule([portal_flag])

            pillar_connectors.append(
                regionmap.RegionConnector(
                    "end_of_time", portal_region_name,
                    f"eot_pillar_to_{portal_region_name}",
                    rule, reversible=False
                )
            )

            # Rewrite region rewards for the correct EoT pillar flag
            map_region_name = _portal_region_dict[portal]
            loc_region = region_map.loc_region_dict[map_region_name]
            loc_region.region_rewards = [
                x for x in loc_region.region_rewards if x not in total_portal_flags
            ]
            if portal_flag is not None:
                loc_region.region_rewards.append(portal_flag)

            # Remove all portal connectors
            region_map.name_connector_dict[map_region_name] = [
                x for x in region_map.name_connector_dict[map_region_name]
                if x.to_region_name not in portal_target_names
            ]

            # Add new portal connectors
            target_portal = pair[(ind + 1) % true_len]
            target_region_name = _portal_region_dict[target_portal]

            normal_rule = portal_rule
            if target_portal == PortalExits.LAIR_RUINS:
                normal_rule = portal_rule & logictypes.LogicRule([memory.Flags.OW_LAVOS_HAS_FALLEN])

            if portal == target_portal:  #
                new_connectors = [
                    regionmap.RegionConnector(
                        portal_region_name, "end_of_time",
                        f"portal_{portal_region_name}_to_eot",
                        proto_eot_rule, reversible=False,
                    )
                ]
            else:
                new_connectors = [
                    regionmap.RegionConnector(
                        portal_region_name, "end_of_time",
                        f"portal_{portal_region_name}_to_eot",
                        normal_eot_rule, reversible=False,
                    ),
                    regionmap.RegionConnector(
                        portal_region_name, target_region_name,
                        f"portal_{portal_region_name}_to_{target_region_name}",
                        normal_rule, reversible=False
                    )
                ]
            region_map.name_connector_dict[map_region_name].extend(new_connectors)

    # Remove all old pillar connectors and add the new ones
    region_map.name_connector_dict["end_of_time"] = [
        x for x in region_map.name_connector_dict["end_of_time"]
        if x.to_region_name not in _portal_region_dict.values()
    ]
    region_map.name_connector_dict["end_of_time"] += pillar_connectors


def find_portal_assignment(
        region_map: regionmap.RegionMap,
) -> dict[PortalExits, PortalExits]:
    ret_dict: dict[PortalExits, PortalExits] = {}

    _portal_region_inv_dict: dict[str, PortalExits] = {
        x:y for y,x in _portal_region_dict.items()
    }

    for portal, region_name in _portal_region_dict.items():
        if portal in ret_dict:
            continue

        connectors = region_map.name_connector_dict[region_name]
        for connector in connectors:
            target_portal: PortalExits | None = None
            if connector.to_region_name in _portal_region_inv_dict:
                target_portal = _portal_region_inv_dict[connector.to_region_name]
                if portal in ret_dict:
                    raise ValueError("Duplicate Portal Assignment")
                ret_dict[portal] = target_portal

    missing_portals = [x for x in PortalExits if x not in ret_dict]
    if len(missing_portals) != 1:
        raise ValueError("Missing Assignment")

    ret_dict[missing_portals[0]] = missing_portals[0]
    verify_portal_dict(ret_dict)
    return ret_dict


def modify_all_portal_scripts(
        region_map: regionmap.RegionMap,
        script_manager: ScriptManager
):
    """Apply portal shuffle to scripts (PostConfig)."""

    # portal_assignment = {
    #     PortalExits.PROTO_DOME: PortalExits.BANGOR_DOME,
    #     PortalExits.MEDINA_CLOSET: PortalExits.DARK_AGES_CAVE,
    #     PortalExits.MYSTIC_MTS: PortalExits.MYSTIC_MTS,
    #     PortalExits.TELEPOD_EXHIBIT: PortalExits.GUARDIA_FOREST,
    #     PortalExits.TRUCE_CANYON: PortalExits.LAIR_RUINS,
    #     PortalExits.GUARDIA_FOREST: PortalExits.TELEPOD_EXHIBIT,
    #     PortalExits.BANGOR_DOME: PortalExits.PROTO_DOME,
    #     PortalExits.LAIR_RUINS: PortalExits.TRUCE_CANYON,
    #     PortalExits.DARK_AGES_CAVE: PortalExits.MEDINA_CLOSET,
    # }
    portal_assignment = find_portal_assignment(region_map)
    portal_pairs = get_portal_pairs(portal_assignment)
    assigned_portal_flags = get_pair_flags(portal_pairs, region_map)

    update_portal_activation_scripts(script_manager, portal_pairs, assigned_portal_flags)
    rewrite_eot_pillars(script_manager, portal_pairs, assigned_portal_flags)

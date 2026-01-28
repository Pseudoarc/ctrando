"""Module for writing recruits to the RewardStructure"""
from dataclasses import dataclass
import typing

from ctrando.arguments.arguments import Settings
from ctrando.arguments.recruitoptions import RecruitData
from ctrando.common import ctenums, ctrom
from ctrando.common.ctenums import CharID, RecruitID, ItemID
from ctrando.common.random import RNGType
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.logic.logictypes import LogicRule
from ctrando.logic.logicfactory import get_fair_recruit_item
from ctrando.recruits import (
    starter, dactylnest, deathpeak, frogsburrow, guardiaprison,
    leenesquare, manoriacathedral, northcape, protodome, queenschamber,
    yakrabox
)

# _fair_recruit_item: dict[CharID, ItemID] = {
#     CharID.CRONO: ItemID.BIKE_KEY,
#     CharID.MARLE: ItemID.PENDANT,
#     CharID.LUCCA: ItemID.GATE_KEY,
#     CharID.ROBO: ItemID.SEED,
#     CharID.FROG: ItemID.HERO_MEDAL,
#     CharID.AYLA: ItemID.DREAMSTONE,
#     CharID.MAGUS: ItemID.PENDANT_CHARGE
# }

@dataclass
class RecruitSpotData:
    level: int
    techlevel: int

_recruit_spot_data_dict = {
    RecruitID.STARTER: RecruitSpotData(1, 0),
    RecruitID.MILLENNIAL_FAIR: RecruitSpotData(1, 0),
    RecruitID.CATHEDRAL: RecruitSpotData(5, 0),
    RecruitID.CASTLE: RecruitSpotData(5, 1),
    RecruitID.CRONO_TRIAL: RecruitSpotData(7, 1),
    RecruitID.PROTO_DOME: RecruitSpotData(10, 0),
    RecruitID.NORTH_CAPE: RecruitSpotData(37, 3),
    RecruitID.FROGS_BURROW: RecruitSpotData(18, 2),
    RecruitID.DACTYL_NEST: RecruitSpotData(20, 2),
    RecruitID.DEATH_PEAK: RecruitSpotData(37, 8)
}


def get_recruit_spot_data(recruit_spot: RecruitID) -> RecruitSpotData:
    return _recruit_spot_data_dict[recruit_spot]


def get_random_recruit_assignment_dict(
        plando_dict: dict[ctenums.RecruitID, list[typing.Any]],
        rng: RNGType
) -> dict[RecruitID, list[CharID]]:
    """Random Except Starter Filled"""
    temp_dict: dict[RecruitID, list[CharID | None]] = {spot: [] for spot in RecruitID}
    char_pool = list(ctenums.CharID)
    rng.shuffle(char_pool)

    # First handle forced assignment
    for spot, recruit_list in plando_dict.items():
        forced_recruits = [x for x in recruit_list if x in ctenums.CharID]
        for forced_recruit in forced_recruits:
            temp_dict[spot].append(forced_recruit)
            char_pool.remove(forced_recruit)

    # Now handle randoms/Nones
    for spot, recruit_list in plando_dict.items():
        for recruit_type in recruit_list:
            if recruit_type == "random":
                temp_dict[spot].append(char_pool.pop())
            elif recruit_type is None:
                temp_dict[spot].append(None)

    remaining_spots = [spot for spot, val in temp_dict.items() if not val]
    rng.shuffle(remaining_spots)

    for char_id, spot in zip(char_pool, remaining_spots):
        temp_dict[spot].append(char_id)

    # Clean up None placeholders
    ret_dict: dict[RecruitID, list[CharID]] = dict()
    for spot, recruit_list in temp_dict.items():
        ret_dict[spot] = [x for x in recruit_list if x in ctenums.CharID]

    return ret_dict


RecruitAssigner: typing.Callable[[CharID, ScriptManager], None]


def write_recruits_to_ct_rom(
        recruit_dict: dict[RecruitID, CharID | None],
        script_manager: ScriptManager,
        settings: Settings = Settings()
):

    recruit_writer_dict: dict[RecruitID, RecruitAssigner] = {
        RecruitID.STARTER: starter.assign_pc_to_spot,
        RecruitID.CRONO_TRIAL: guardiaprison.assign_pc_to_spot,
        RecruitID.CATHEDRAL: manoriacathedral.assign_pc_to_spot,
        RecruitID.PROTO_DOME: protodome.assign_pc_to_spot,
        RecruitID.MILLENNIAL_FAIR: leenesquare.assign_pc_to_spot,
        RecruitID.DACTYL_NEST: dactylnest.assign_pc_to_spot,
        RecruitID.CASTLE: queenschamber.assign_pc_to_spot,
        RecruitID.DEATH_PEAK: deathpeak.assign_pc_to_spot,
        RecruitID.FROGS_BURROW: frogsburrow.assign_pc_to_spot,
        RecruitID.NORTH_CAPE: northcape.assign_pc_to_spot,
        RecruitID.YAKRA_BOX: yakrabox.assign_pc_to_spot,
    }

    spot_levels_dict: dict[RecruitID, RecruitData] = {
        RecruitID.STARTER: settings.recruit_options.starter_data,
        RecruitID.CRONO_TRIAL: settings.recruit_options.trial_data,
        RecruitID.CATHEDRAL: settings.recruit_options.cathedral_data,
        RecruitID.PROTO_DOME: settings.recruit_options.proto_data,
        RecruitID.MILLENNIAL_FAIR: settings.recruit_options.fair_data,
        RecruitID.DACTYL_NEST: settings.recruit_options.dactyl_data,
        RecruitID.CASTLE: settings.recruit_options.castle_data,
        RecruitID.DEATH_PEAK: settings.recruit_options.death_peak_data,
        RecruitID.FROGS_BURROW: settings.recruit_options.burrow_data,
        RecruitID.NORTH_CAPE: settings.recruit_options.north_cape_data,
        RecruitID.YAKRA_BOX: settings.recruit_options.yakra_box_data
    }

    for spot, writer in recruit_writer_dict.items():
        recruits = recruit_dict[spot]
        spot_data = spot_levels_dict[spot]

        if spot == ctenums.RecruitID.STARTER:
            writer(
                recruits, script_manager,
                spot_data.min_level, spot_data.min_tech_level,
                settings.recruit_options.scale_level_to_leader,
                settings.recruit_options.scale_techlevel_to_leader,
                settings.recruit_options.scale_gear
            )
        elif recruits:
            if len(recruits) != 1:
                raise ValueError(f"Multiple Assignment to {spot}")
            recruit = recruits[0]
            writer(recruit, script_manager,
                   spot_data.min_level, spot_data.min_tech_level,
                   settings.recruit_options.scale_level_to_leader,
                   settings.recruit_options.scale_techlevel_to_leader,
                   settings.recruit_options.scale_gear)

            if spot == RecruitID.MILLENNIAL_FAIR:
                item = get_fair_recruit_item(recruit)
                leenesquare.change_recruit_item(item, recruit, script_manager)

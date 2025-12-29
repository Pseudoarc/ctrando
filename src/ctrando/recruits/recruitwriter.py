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
    leenesquare, manoriacathedral, northcape, protodome, queenschamber
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
        plando_dict: dict[ctenums.RecruitID, ctenums.CharID],
        rng: RNGType
) -> dict[RecruitID, CharID]:
    """Random Except Starter Filled"""
    ret_dict: dict[RecruitID, CharID | None] = {spot: None for spot in RecruitID}
    ret_dict.update(plando_dict)

    characters = list(x for x in CharID if x not in plando_dict.values())
    assignable_spots = list(x for x in RecruitID if x not in plando_dict.keys())
    rng.shuffle(characters)

    for spot in (RecruitID.STARTER,):
        if spot in assignable_spots:
            ret_dict[spot] = characters.pop()
            assignable_spots.remove(spot)

    rng.shuffle(assignable_spots)
    for char in characters:
        spot = assignable_spots.pop()
        ret_dict[spot] = char

    return ret_dict


# def write_recruits_to_reward_structure(reward_structure: RewardStructure):
#     """Completely random except Crono's Trial and Starter must be filled."""
#
#     characters = list(CharID)
#     random.shuffle(characters)
#     assignable_spots = list(RecruitID)
#
#     for spot in (RecruitID.STARTER,):
#         print(f"{spot}: {characters[-1]}")
#         reward_structure.assign_recruit(spot, characters.pop())
#         assignable_spots.remove(spot)
#
#     random.shuffle(assignable_spots)
#     for char in characters:
#         spot = assignable_spots.pop()
#         reward_structure.assign_recruit(spot, char)
#         print(f"{spot}: {char}")
#
#     fair_char_entry = reward_structure.recruit_dict[RecruitID.MILLENNIAL_FAIR]
#     if fair_char_entry.reward is not None:
#         fair_item = _fair_recruit_item[fair_char_entry.reward]
#         fair_group = fair_char_entry.group_name
#
#         reward_structure.group_dict[fair_group].access_rule = LogicRule([fair_item])
#
#     prison_char_entry = reward_structure.recruit_dict[RecruitID.CRONO_TRIAL]
#     if prison_char_entry is not None:
#         prison_group = prison_char_entry.group_name
#         reward_structure.group_dict[prison_group].access_rule = LogicRule()


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
    }

    for spot, writer in recruit_writer_dict.items():
        recruit = recruit_dict[spot]
        if recruit is None and spot in (RecruitID.STARTER,):
            raise ValueError("{spot} reward can not be None")

        if recruit is not None:
            spot_data = spot_levels_dict[spot]
            writer(recruit, script_manager,
                   spot_data.min_level, spot_data.min_tech_level,
                   settings.recruit_options.scale_level_to_leader,
                   settings.recruit_options.scale_techlevel_to_leader,
                   settings.recruit_options.scale_gear)

            if spot == RecruitID.MILLENNIAL_FAIR:
                item = get_fair_recruit_item(recruit)
                leenesquare.change_recruit_item(item, recruit, script_manager)

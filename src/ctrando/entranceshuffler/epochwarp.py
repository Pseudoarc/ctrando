"""Module for finding Epoch Warp Coordinates"""
import typing
from collections.abc import Sequence
from dataclasses import dataclass

from ctrando.common import ctenums, memory
from ctrando.entranceshuffler import maptraversal, regionmap
from ctrando.treasures import treasuretypes


@dataclass
class OWCoords:
    """
    Data for doing a changeloc to overworld.
    """
    loc_id: ctenums.LocID
    x_coord: int
    y_coord: int


_region_coord_dict: dict[str, OWCoords] = {
    "truce_1000_overworld": OWCoords(ctenums.LocID.OW_PRESENT, 0x198, 0x118),
    "guardia_castle_1000_overworld": OWCoords(ctenums.LocID.OW_PRESENT, 0x118, 0xE8),
    "porre_1000_overworld": OWCoords(ctenums.LocID.OW_PRESENT, 0x270, 0x258),
    "medina_1000_overworld": OWCoords(ctenums.LocID.OW_PRESENT, 0x398, 0x198),
    "choras_1000_overworld": OWCoords(ctenums.LocID.OW_PRESENT, 0x470, 0x330),
    # "sun_keep_1000_overworld": ,
    "truce_600_overworld": OWCoords(ctenums.LocID.OW_MIDDLE_AGES, 0x198, 0x118),
    "guardia_castle_600_overworld": OWCoords(ctenums.LocID.OW_MIDDLE_AGES, 0x118, 0xE8),
    # "sunken_desert_overworld": ,
    "porre_600_overworld": OWCoords(ctenums.LocID.OW_MIDDLE_AGES, 0x270, 0x258),
    "choras_600_overworld": OWCoords(ctenums.LocID.OW_MIDDLE_AGES, 0x470, 0x330),
    # "magus_lair_overworld": ,
    # "ozzies_fort_overworld": ,
    # "sun_keep_600_overworld": ,
    # "giants_claw_overworld": ,
    "trann_bangor_overworld": OWCoords(ctenums.LocID.OW_FUTURE, 0xD8, 0x1E8),
    "arris_overworld": OWCoords(ctenums.LocID.OW_FUTURE, 0x1D8, 0x188),
    "proto_overworld": OWCoords(ctenums.LocID.OW_FUTURE, 0x388, 0x158),
    "keepers_overworld": OWCoords(ctenums.LocID.OW_FUTURE, 0x298, 0x248),
    # "sun_keep_2300_overworld": ,
    # "geno_overworld": ,
    # "sun_palace_overworld": ,
    "ioka_overworld": OWCoords(ctenums.LocID.OW_PREHISTORIC, 0x279, 0x258),
    "reptite_lair_overworld": OWCoords(ctenums.LocID.OW_PREHISTORIC, 0x238, 0x338),
    # "sun_keep_prehistory_overworld": ,
    # "tyrano_lair_overworld": ,
    # "lair_ruins_overworld": ,
    "dark_ages_portal_overworld": OWCoords(ctenums.LocID.OW_DARK_AGES, 0x198, 0x118),
    "dark_ages_skyway_island_overworld": OWCoords(ctenums.LocID.OW_DARK_AGES, 0x451, 0xF8),
    # "enhasa_overworld": ,
    # "kajar_overworld": ,
    # "zeal_palace_overworld": ,
    "last_village_overworld": OWCoords(ctenums.LocID.OW_LAST_VILLAGE, 0x488, 0x198),
    # "last_village_portal_overworld": ,
    # "last_village_sun_keep_overworld": ,
}


def get_nearest_ow_coords(
        region_map: regionmap.RegionMap,
        starting_rewards: Sequence[typing.Any],
        treasure_dict: dict[ctenums.TreasureID, treasuretypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, list[ctenums.CharID]],
        starting_region = "starting_rewards",
) -> OWCoords:
    starting_rewards = list(starting_rewards)
    good_ow_regions = set(_region_coord_dict.keys())

    rewards_to_skip = {memory.Flags.OBTAINED_EPOCH_FLIGHT}
    traverser = maptraversal.MapTraverser(region_map, starting_region, starting_rewards)
    reached_regions = {starting_region}

    connector_queue: list[regionmap.RegionConnector] = list(
        region_map.name_connector_dict[starting_region]
    )
    cur_ind = 0

    while True:

        connector = connector_queue[cur_ind]
        if connector.rule(traverser.game):
            to_region = connector.to_region_name

            if to_region in reached_regions:
                continue

            if to_region in good_ow_regions:
                return _region_coord_dict[to_region]

            traverser.add_region_rewards(to_region, rewards_to_skip)
            traverser.add_region_treasures(to_region, treasure_dict, recruit_dict, rewards_to_skip)
            reached_regions.add(to_region)
            connector_queue.extend(region_map.name_connector_dict[to_region])
        else:
            if cur_ind == len(connector_queue) - 1:
                raise ValueError
            connector_queue.append(connector)

        cur_ind += 1

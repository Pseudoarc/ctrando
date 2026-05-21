"""Actually Shuffle the Entrances"""
from collections.abc import Iterable
from typing import Sequence

from ctrando.arguments import entranceoptions
from ctrando.common import ctenums, memory
from ctrando.common.random import RNGType
from ctrando.entranceshuffler import regionmap, maptraversal
from ctrando.entranceshuffler.locregions import LocExit, get_all_loc_regions
from ctrando.entranceshuffler.owregions import OWExit, get_ow_regions


class MapGenerationException(Exception):
    ...


def get_random_exit_connectors(
        entrance_options: entranceoptions.EntranceShufflerOptions,
        rng: RNGType
) -> list[regionmap.ExitConnector]:
    if entrance_options.shuffle_entrances is False:
        return regionmap.get_default_exit_connectors()
    else:
        return get_shuffled_exit_connectors(
            regionmap.get_default_exit_connectors(),
            entrance_options.preserve_groups,
            entrance_options.vanilla_spots,
            rng
        )


def get_shuffled_map(
        preserve_dungeons: bool,
        preserve_shops: bool,
        pre_flight_percent: float = 0.5
) -> regionmap.RegionMap:
    """Return a map with shuffled overworld exits."""
    region_connectors = regionmap.get_default_region_connectors()

    for iter_num in range(100):
        default_exit_connectors = regionmap.get_default_exit_connectors()
        exit_connectors = get_shuffled_exit_connectors(default_exit_connectors,
                                                       preserve_dungeons,
                                                       preserve_shops)
        candidate_map = regionmap.RegionMap(
            get_ow_regions(), get_all_loc_regions(),
            exit_connectors, region_connectors
        )
        if is_map_viable(candidate_map, pre_flight_percent):
            return candidate_map
    else:
        raise MapGenerationException("Failed to Generate Map")


def is_map_viable(
        region_map: regionmap.RegionMap,
        pre_flight_percent: float = 0.5
) -> bool:
    """
    Before items and recruits are placed, determine whether a map is viable.
    """
    rewards_to_skip = {memory.Flags.OBTAINED_EPOCH_FLIGHT}

    interesting_regions = {
        "snail_stop", "millennial_fair", "manoria_cathedral", "denadoro_mts",
        "arris_dome", "giants_claw", "geno_dome", "reptite_lair",
        "mt_woe",
    }

    traverser = maptraversal.MapTraverser(region_map, "starting_rewards")
    fake_treasure_dict = {tid: ctenums.ItemID.NONE for tid in ctenums.TreasureID}
    fake_recruit_dict = {rid: [] for rid in ctenums.RecruitID}
    traverser.maximize(fake_treasure_dict, fake_recruit_dict, rewards_to_skip)
    if len(traverser.reached_regions.intersection(interesting_regions)) < 2:
        return False

    useful_items = traverser.useful_items
    useful_keys = [x for x in useful_items if isinstance(x, ctenums.ItemID)] + [ctenums.ItemID.JERKY]
    traverser.game.key_items = useful_keys
    traverser.game.characters = {x for x in ctenums.CharID}
    traverser.maximize(fake_treasure_dict, fake_recruit_dict, rewards_to_skip)

    reached_ow_regions = {
        name for name in traverser.reached_regions if name in region_map.ow_region_dict
    }
    ow_coverage = len(reached_ow_regions)/len(region_map.ow_region_dict.keys())
    if ow_coverage < pre_flight_percent:
        # print(f"Failed Pre-Flight: {ow_coverage} < {pre_flight_percent}")
        return False

    flight_regions = {"blackbird_scaffolding_epoch", "blackbird"}
    if not flight_regions.intersection(traverser.reached_regions):
        # print("Flight unavailable.")
        return False

    # print("No Flight Regions:")
    # for region in get_ow_regions():
    #     if region.name not in traverser.reached_regions:
    #         print(f"\t{region.name}")
    #
    # input()

    # For return via reset, epoch needs to be walkable
    if "porre_1000_overworld" not in traverser.reached_regions:
        # print("no porre 1000")
        return False

    traverser.game.other_rewards.add(memory.Flags.OBTAINED_EPOCH_FLIGHT)
    traverser.maximize(fake_treasure_dict, fake_recruit_dict)
    if len(traverser.reached_regions) != len(region_map.name_connector_dict.keys()):
        # print("Failed Reachability")
        # for region in region_map.name_connector_dict:
        #     if region not in traverser.reached_regions:
        #         print(f"\t{region}")

        return False

    # input("end viable")
    return True


def get_ow_exit_assign_dict(
        shuffled_connectors: Iterable[regionmap.ExitConnector]
) -> dict[OWExit, OWExit]:
    vanilla_exit_connectors = regionmap.get_default_exit_connectors()

    assign_dict: dict[OWExit, OWExit] = dict()
    for connector in shuffled_connectors:
        for van_connector in vanilla_exit_connectors:
            if van_connector.to_exit == connector.to_exit:
                assign_dict[connector.from_exit] = van_connector.from_exit
                break
        else:
            raise ValueError("failed to find assignment")

    return assign_dict


def get_shuffled_map_from_connectors(
        exit_connectors: Iterable[regionmap.ExitConnector],
        region_connectors: Iterable[regionmap.RegionConnector]
):
    loc_regions = get_all_loc_regions()
    avail_loc_exits = {
        x.to_exit for x in exit_connectors
    }
    trimmed_loc_regions = [
        x for x in loc_regions
        if not x.loc_exits or any(loc_exit in avail_loc_exits for loc_exit in x.loc_exits)
    ]

    return regionmap.RegionMap(
        get_ow_regions(), trimmed_loc_regions,
        exit_connectors, region_connectors
    )

_known_dead_ends_alt: list[LocExit] = [
    LocExit.NORTHERN_RUINS_1000,
    LocExit.FIONAS_SHRINE,
    LocExit.CRONOS_HOUSE,
    LocExit.TRUCE_SINGLE_RESIDENCE,
    LocExit.TRUCE_INN_1000,
    LocExit.TRUCE_SCREAMING_RESIDENCE,
    LocExit.TRUCE_MARKET_1000,
    LocExit.TRUCE_MAYOR,
    LocExit.LUCCAS_HOUSE,
    LocExit.PORRE_INN_1000,
    LocExit.PORRE_MARKET_1000,
    LocExit.SNAIL_STOP,
    LocExit.PORRE_MAYOR_1000,
    LocExit.PORRE_RESIDENCE_1000,
    LocExit.MEDINA_ELDER,
    LocExit.MEDINA_INN,
    LocExit.MELCHIORS_HUT,
    LocExit.MEDINA_MARKET,
    LocExit.MEDINA_SQUARE,
    LocExit.CHORAS_MAYOR_1000,
    LocExit.CHORAS_INN_1000,
    LocExit.CHORAS_CARPTENTER_1000,
    LocExit.FOREST_RUINS,
    LocExit.SUN_KEEP_1000,
    LocExit.WEST_CAPE,
    LocExit.ZENAN_BRIDGE_600_NORTH,
    LocExit.SUNKEN_DESERT_ENTRANCE,
    LocExit.GIANTS_CLAW,
    LocExit.TRUCE_COUPLE_RESIDENCE_600,
    LocExit.TRUCE_SMITH_RESIDENCE,
    LocExit.TRUCE_INN_600,
    LocExit.TRUCE_MARKET_600,
    LocExit.MANORIA_CATHEDRAL,
    LocExit.DORINO_BROMIDE_RESIDENCE,
    LocExit.DORINO_ELDER,
    LocExit.DORINO_INN,
    LocExit.DORINO_MARKET,
    LocExit.TATAS_HOUSE,
    LocExit.PORRE_ELDER_600,
    LocExit.PORRE_CAFE_600,
    LocExit.PORRE_INN_600,
    LocExit.PORRE_MARKET_600,
    LocExit.FIONAS_VILLA,
    LocExit.CHORAS_OLD_RESIDENCE_600,
    LocExit.CHORAS_INN_600,
    LocExit.CHORAS_CAFE_600,
    LocExit.CHORAS_CARPTENTER_600,
    LocExit.CHORAS_MARKET_600,
    LocExit.CURSED_WOODS,
    LocExit.DENADORO_MTS,
    LocExit.OZZIES_FORT,
    LocExit.SUN_KEEP_600,
    LocExit.TRANN_DOME,
    LocExit.ARRIS_DOME,
    LocExit.FACTORY_RUINS,
    LocExit.SUN_KEEP_2300,
    LocExit.GENO_DOME,
    LocExit.SUN_PALACE,
    LocExit.TYRANO_LAIR,
    LocExit.REPTITE_LAIR,
    LocExit.DACTYL_NEST,
    LocExit.SUN_KEEP_PREHISTORY,
    LocExit.CHIEFS_HUT,
    LocExit.TRADING_POST,
    LocExit.IOKA_SW_HUT,
    LocExit.IOKA_SWEET_WATER_HUT,
    LocExit.HUNTING_RANGE,
    LocExit.LARUBA_RUINS,
    LocExit.TERRA_CAVE,
    LocExit.ZEAL_PALACE,
    LocExit.ENHASA,
    LocExit.KAJAR,
    LocExit.BLACKBIRD,
    LocExit.NORTH_CAPE,
    LocExit.LAST_VILLAGE_COMMNONS,
    LocExit.LAST_VILLAGE_EMPTY_HUT,
    LocExit.LAST_VILLAGE_SHOP,
    LocExit.LAST_VILLAGE_RESIDENCE,
    LocExit.SUN_KEEP_LAST_VILLAGE,
]


_known_dead_ends: list[LocExit] = [
    LocExit.CRONOS_HOUSE, LocExit.TRUCE_MAYOR, LocExit.TRUCE_MARKET_1000,
    LocExit.TRUCE_INN_1000, LocExit.PORRE_INN_1000,
    LocExit.GUARDIA_CASTLE_1000, LocExit.PORRE_MAYOR_1000,
    LocExit.PORRE_MARKET_1000, LocExit.SNAIL_STOP, LocExit.MEDINA_INN,
    LocExit.MEDINA_SQUARE, LocExit.MEDINA_ELDER,
    LocExit.FOREST_RUINS, LocExit.LUCCAS_HOUSE,
    LocExit.GUARDIA_CASTLE_600, LocExit.MANORIA_CATHEDRAL,
    LocExit.TRUCE_MARKET_600, LocExit.DENADORO_MTS, LocExit.DORINO_BROMIDE_RESIDENCE,
    LocExit.DORINO_MARKET, LocExit.DORINO_INN, LocExit.FIONAS_VILLA,
    LocExit.CURSED_WOODS, LocExit.PORRE_CAFE_600, LocExit.PORRE_INN_600,
    LocExit.DEATH_PEAK, LocExit.ARRIS_DOME, LocExit.FACTORY_RUINS,
    # LocExit.DACTYL_NEST  # ??
    LocExit.HUNTING_RANGE, LocExit.LARUBA_RUINS,
    LocExit.TRADING_POST, LocExit.CHIEFS_HUT, LocExit.IOKA_SW_HUT,
    LocExit.IOKA_SWEET_WATER_HUT, LocExit.CHORAS_MAYOR_1000, LocExit.CHORAS_INN_1000,
    LocExit.CHORAS_CARPTENTER_1000, LocExit.WEST_CAPE,
    LocExit.NORTHERN_RUINS_1000, LocExit.PORRE_ELDER_600,
    LocExit.MELCHIORS_HUT, LocExit.TRUCE_INN_600, LocExit.TRANN_DOME,
    LocExit.ZENAN_BRIDGE_600_NORTH, LocExit.TATAS_HOUSE,
    LocExit.SUN_KEEP_600, LocExit.CHORAS_CAFE_600, LocExit.CHORAS_MARKET_600,
    LocExit.CHORAS_CARPTENTER_600, LocExit.NORTHERN_RUINS_600,
    LocExit.GIANTS_CLAW, LocExit.OZZIES_FORT, LocExit.MAGUS_LAIR,
    LocExit.SUNKEN_DESERT_ENTRANCE,
    LocExit.FIONAS_SHRINE, LocExit.SUN_KEEP_2300, LocExit.SUN_KEEP_PREHISTORY,
    LocExit.SUN_PALACE, LocExit.GENO_DOME, LocExit.REPTITE_LAIR, LocExit.TYRANO_LAIR,
    LocExit.NORTH_CAPE, LocExit.LAST_VILLAGE_SHOP, LocExit.LAST_VILLAGE_COMMNONS,
    LocExit.BLACKBIRD,
    # LocExit.ZEAL_PALACE  # ??
    LocExit.ENHASA, LocExit.KAJAR,
    LocExit.TERRA_CAVE,  # Eventually cut Woe from Beast Cave
    LocExit.TRUCE_SINGLE_RESIDENCE, LocExit.TRUCE_SCREAMING_RESIDENCE,
    LocExit.TRUCE_SMITH_RESIDENCE, LocExit.TRUCE_COUPLE_RESIDENCE_600,
    LocExit.LAST_VILLAGE_RESIDENCE, LocExit.LAST_VILLAGE_EMPTY_HUT, LocExit.SUN_KEEP_LAST_VILLAGE
]
_known_dead_ends_set = set(_known_dead_ends)
_flag_ow_exits = (OWExit.SUNKEN_DESERT, OWExit.FIONAS_SHRINE, OWExit.GIANTS_CLAW)

_desolate_ow_exits: set[OWExit] = {
    OWExit.SUN_KEEP_600, OWExit.SUN_KEEP_1000, OWExit.SUN_KEEP_2300,
    OWExit.SUN_PALACE, OWExit.SUN_KEEP_LAST_VILLAGE,
    OWExit.SUN_KEEP_PREHISTORY, OWExit.LAIR_RUINS,
    OWExit.GENO_DOME, OWExit.OZZIES_FORT,
}

def get_shuffled_group(
        base_assignment: dict[OWExit, LocExit],
        group_ow_exits: Sequence[OWExit],
        rng: RNGType,
) -> dict[OWExit, LocExit]:
    """
    Takes the exit connectors with overworld exit in group_ow_exists and ow_exit_pool
    and returns a list of ExitConnectors with randomized location exit targets.
    """

    ow_exit_pool_set = set(base_assignment.keys())
    group_ow_exits_set = set(group_ow_exits)
    available_ow_exits = ow_exit_pool_set.intersection(group_ow_exits_set)

    loc_exit_targets = list(base_assignment[x] for x in group_ow_exits)

    def get_era(ow_exit: OWExit):
        return ow_exit.value[0].value.overworld_id

    # Rules:
    # 1) Island Exits with no other exit can't lead to Crono's house.
    # 2) Exits opened by a flag must be assigned to a dead end

    while True:
        assign_dict: dict[OWExit, LocExit] = {
            # x: None for x in group_ow_exits_set
        }

        temp_ow_exit_pool = set(available_ow_exits)
        temp_loc_exit_pool = set(loc_exit_targets)

        # Most restrictive is dead ends for flags
        flag_ow_exits = [
            x for x in (OWExit.SUNKEN_DESERT, OWExit.FIONAS_SHRINE, OWExit.GIANTS_CLAW)
            if x in temp_ow_exit_pool
        ]
        if flag_ow_exits:
            flag_target_pool = _known_dead_ends_set.intersection(temp_loc_exit_pool)
            available_dead_ends: list[LocExit] = [
                x for x in LocExit
                if x in flag_target_pool and x != LocExit.CRONOS_HOUSE
            ]

            flag_assignments = rng.sample(available_dead_ends, k=len(flag_ow_exits))

            temp_ow_exit_pool.difference_update(flag_ow_exits)
            temp_loc_exit_pool.difference_update(flag_assignments)
            assign_dict.update(zip(flag_ow_exits, flag_assignments))

        # Now do Crono's House
        if OWExit.CRONOS_HOUSE in temp_ow_exit_pool:
            possible_house_ow_exits = [
                x for x in OWExit
                if x in temp_ow_exit_pool and x not in _desolate_ow_exits
            ]

            if not possible_house_ow_exits:
                continue

            house_ow_exit = rng.choice(possible_house_ow_exits)
            assign_dict[house_ow_exit] = LocExit.CRONOS_HOUSE
            temp_ow_exit_pool.remove(house_ow_exit)
            temp_loc_exit_pool.remove(LocExit.CRONOS_HOUSE)

        remaining_ow_exits = [
            x for x in OWExit if x in temp_ow_exit_pool
        ]
        remaining_loc_exits = [
            x for x in LocExit if x in temp_loc_exit_pool
        ]
        rng.shuffle(remaining_ow_exits)

        assign_dict.update(zip(remaining_ow_exits, remaining_loc_exits, strict=True))
        return assign_dict


def get_shuffled_exit_connectors(
        exit_connectors: list[regionmap.ExitConnector],
        preserve_groups: list[Sequence[OWExit]],
        vanilla_pool: list[OWExit],
        rng: RNGType
) -> list[regionmap.ExitConnector]:
    """
    Shuffle the exit connectors, obeying a few rules.
    - Leave the Dorino side of the Magic Cave as in vanilla.
    -
    """
    exit_connectors = [
        connector for connector in exit_connectors
        if connector.from_exit != OWExit.TYRANO_LAIR
    ]

    base_assignment: dict[OWExit, LocExit] = {
        connector.from_exit: connector.to_exit
        for connector in exit_connectors if connector.from_exit != OWExit.TYRANO_LAIR
    }

    # 1) Remove Tyrano Lair exit (always ruined)
    # 2) Remove the LV version of the portal area.
    base_assignment[OWExit.LAIR_RUINS] = LocExit.TYRANO_LAIR
    base_assignment[OWExit.LAST_VILLAGE_PORTAL] = LocExit.LAIR_RUINS

    assign_dict: dict[OWExit, LocExit] = dict()

    for ow_exit in vanilla_pool:
        if ow_exit in base_assignment:
            assign_dict[ow_exit] = base_assignment[ow_exit]

    for group in preserve_groups:
        group_assign = get_shuffled_group(base_assignment, group, rng)
        assign_dict.update(group_assign)

    for connector in exit_connectors:
        connector.to_exit = assign_dict[connector.from_exit]

    return list(exit_connectors)


def main():
    ...


if __name__ == "__main__":
    main()











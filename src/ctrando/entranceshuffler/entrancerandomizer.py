"""Actually Shuffle the Entrances"""
from collections.abc import Iterable

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
            entrance_options.preserve_spots,
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
    fake_recruit_dict = {rid: None for rid in ctenums.RecruitID}
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
    return regionmap.RegionMap(
        get_ow_regions(), get_all_loc_regions(),
        exit_connectors, region_connectors
    )


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


def get_shuffled_exit_connectors(
        exit_connectors: list[regionmap.ExitConnector],
        preserve_pool: list[OWExit],
        vanilla_pool: list[OWExit],
        rng: RNGType
) -> list[regionmap.ExitConnector]:
    """
    Shuffle the exit connectors, obeying a few rules.
    - Leave the Dorino side of the Magic Cave as in vanilla.
    -
    """
    ow_exit_pool = [connector.from_exit for connector in exit_connectors]
    loc_exit_pool = [connector.to_exit for connector in exit_connectors]

    #   print(vanilla_pool)
    # input()

    # 1) Remove Tyrano Lair exit (always ruined)
    ow_exit_pool.remove(OWExit.TYRANO_LAIR)
    # 2) Remove the LV version of the portal area.
    loc_exit_pool.remove(LocExit.DARK_AGES_PORTAL_LAST_VILLAGE)

    exit_connectors = [connector for connector in exit_connectors
                       if connector.from_exit in ow_exit_pool]

    assign_dict: dict[OWExit, LocExit] = dict()

    # Keep the Dorino side of magic cave vanilla.
    vanilla_pool = list(vanilla_pool)
    for ow_exit in (OWExit.MAGIC_CAVE_OPEN, OWExit.MAGIC_CAVE_CLOSED):
        if ow_exit not in vanilla_pool:
            vanilla_pool.append(ow_exit)

    for connector in exit_connectors:
        if connector.from_exit == OWExit.LAIR_RUINS:
            connector.to_exit = LocExit.TYRANO_LAIR
        if connector.from_exit == OWExit.LAST_VILLAGE_PORTAL:
            connector.to_exit = LocExit.LAIR_RUINS

        # pre-fill assignment with specified vanilla spots
        if connector.from_exit in vanilla_pool:
            assign_dict[connector.from_exit] = connector.to_exit
            ow_exit_pool.remove(connector.from_exit)
            loc_exit_pool.remove(connector.to_exit)

    dungeon_exits = [x for x in preserve_pool if x not in vanilla_pool]
    if OWExit.TYRANO_LAIR in dungeon_exits:
        dungeon_exits.remove(OWExit.TYRANO_LAIR)

    dungeon_targets = [connector.to_exit for connector in exit_connectors
                       if connector.from_exit in dungeon_exits]

    usable_dead_ends = [
        connector.to_exit for connector in exit_connectors
        if connector.from_exit not in assign_dict and connector.to_exit in _known_dead_ends
    ]
    if LocExit.CRONOS_HOUSE in usable_dead_ends:
        usable_dead_ends.remove(LocExit.CRONOS_HOUSE)

    flag_ow_exits = [
        x for x in (OWExit.SUNKEN_DESERT, OWExit.FIONAS_SHRINE, OWExit.GIANTS_CLAW)
        if x not in assign_dict.keys()
    ]

    # Make sure flag exits can't be back doored by making them always dead ends
    for ow_exit in flag_ow_exits:
        if ow_exit in dungeon_exits:
            pool = [x for x in usable_dead_ends
                    if x in dungeon_targets and x != LocExit.NORTHERN_RUINS_1000]
            target = rng.choice(pool)
            dungeon_exits.remove(ow_exit)
            dungeon_targets.remove(target)
        else:
            pool = [x for x in usable_dead_ends if x not in dungeon_targets]
            target = rng.choice(pool)

        usable_dead_ends.remove(target)
        loc_exit_pool.remove(target)
        ow_exit_pool.remove(ow_exit)
        assign_dict[ow_exit] = target

    # Give Crono's house a good exit to avoid dead-ending
    if LocExit.CRONOS_HOUSE in loc_exit_pool and LocExit.CRONOS_HOUSE not in dungeon_targets:
        bad_ow_exits = [
            OWExit.SUN_KEEP_600, OWExit.SUN_KEEP_1000, OWExit.SUN_KEEP_2300,
            OWExit.SUN_PALACE, OWExit.SUN_KEEP_LAST_VILLAGE,
            OWExit.SUN_KEEP_PREHISTORY, OWExit.LAIR_RUINS,
            OWExit.GENO_DOME, OWExit.OZZIES_FORT,
        ]

        bad_ow_exits += [x for x in dungeon_exits if x not in bad_ow_exits]
        bad_ow_exits = [
            x for x in bad_ow_exits if x not in assign_dict.keys()
        ]
        # bad_ow_exits = bad_ow_exits.union(dungeon_exits).difference(assign_dict.keys())
        starting_ow_exit = rng.choice(
            [ow_exit for ow_exit in ow_exit_pool
             if ow_exit not in bad_ow_exits]
        )
        assign_dict[starting_ow_exit] = LocExit.CRONOS_HOUSE
        ow_exit_pool.remove(starting_ow_exit)
        loc_exit_pool.remove(LocExit.CRONOS_HOUSE)

    while True:
        # Need to make sure that the NR exits are in different eras.

        temp_assign_dict = dict(assign_dict)
        if len(dungeon_exits) != len(dungeon_targets):
            raise ValueError

        dungeon_target_list = list(dungeon_targets)
        rng.shuffle(dungeon_target_list)
        temp_assign_dict.update(zip(dungeon_exits, dungeon_target_list))

        remaining_ow_exits = [x for x in ow_exit_pool if x not in temp_assign_dict.keys()]
        remaining_loc_exits = [x for x in loc_exit_pool if x not in temp_assign_dict.values()]

        rng.shuffle(remaining_loc_exits)
        temp_assign_dict.update(zip(remaining_ow_exits, remaining_loc_exits))

        for connector in exit_connectors:
            connector.to_exit = temp_assign_dict[connector.from_exit]

        nr_1000_era = ctenums.OverWorldID(0)
        nr_600_era = ctenums.OverWorldID(0)

        for connector in exit_connectors:
            if connector.to_exit == LocExit.NORTHERN_RUINS_1000:
                nr_1000_era = connector.from_exit.value[0].value.overworld_id

            if connector.to_exit == LocExit.NORTHERN_RUINS_600:
                nr_600_era = connector.from_exit.value[0].value.overworld_id

        # print(nr_600_era, nr_1000_era)
        if nr_600_era != nr_1000_era:
            break

    assign_dict.update(temp_assign_dict)
    return list(exit_connectors)


def main():
    ...


if __name__ == "__main__":
    main()











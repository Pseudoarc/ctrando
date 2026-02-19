"""Fill with the entrance shuffler logic."""
from ctrando.arguments import entranceoptions, logicoptions
from ctrando.logic import logictypes

from ctrando.bosses import bosstypes as bty
from ctrando.common import ctenums, distribution, memory
from ctrando.common.random import RNGType
from ctrando.treasures import treasuretypes as ttypes
from ctrando.entranceshuffler import regionmap, maptraversal, entrancerandomizer, portalshuffle


def get_forced_key_items():
    return [
        ctenums.ItemID.C_TRIGGER, ctenums.ItemID.CLONE,
        ctenums.ItemID.PENDANT, ctenums.ItemID.PENDANT_CHARGE, ctenums.ItemID.DREAMSTONE,
        ctenums.ItemID.RUBY_KNIFE, # ctenums.ItemID.JETSOFTIME,
        ctenums.ItemID.TOOLS, ctenums.ItemID.RAINBOW_SHELL,
        ctenums.ItemID.PRISMSHARD, ctenums.ItemID.JERKY, ctenums.ItemID.JERKY,
        ctenums.ItemID.BENT_HILT, ctenums.ItemID.BENT_SWORD,
        ctenums.ItemID.HERO_MEDAL, ctenums.ItemID.MASAMUNE_1,
        # ItemID.MASAMUNE_2,  This doesn't unlock anything so not forced
        ctenums.ItemID.TOMAS_POP, ctenums.ItemID.MOON_STONE, ctenums.ItemID.SUN_STONE,
        ctenums.ItemID.BIKE_KEY, ctenums.ItemID.SEED, ctenums.ItemID.GATE_KEY,
        ctenums.ItemID.YAKRA_KEY, ctenums.ItemID.RACE_LOG,
    ]


def update_starting_rewards(
        starting_rewards: list[logictypes.RewardType],
        entrance_options: entranceoptions.EntranceShufflerOptions,
):
    if entrance_options.shuffle_entrances:
        starting_rewards.append(memory.Flags.OW_LAVOS_HAS_FALLEN)


def get_key_item_fill(
        initial_treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID],
        boss_assignment: dict[bty.BossSpotID, bty.BossID],
        recruit_assignment: dict[ctenums.RecruitID, list[ctenums.CharID]],
        logic_options: logicoptions.LogicOptions,
        entrance_options: entranceoptions.EntranceShufflerOptions,
        rng: RNGType
) -> tuple[dict[ctenums.TreasureID, ctenums.ItemID], dict[regionmap.OWExit, regionmap.OWExit], regionmap.RegionMap]:

    forced_key_items = get_forced_key_items()

    if logic_options.jets_of_time:
        forced_key_items.append(ctenums.ItemID.JETSOFTIME)

    key_items = forced_key_items + logic_options.additional_key_items
    for item in initial_treasure_assignment.values():
        if item in key_items:
            key_items.remove(item)

    for item in logic_options.starter_rewards:
        if item in key_items:
            key_items.remove(item)

    # Do it this way to preserve multiples in the loose list
    normal_key_items = list(key_items)
    possible_loose: list[ctenums.ItemID] = []
    for item_id in logic_options.loose_key_items:
        if item_id in key_items:
            possible_loose.append(item_id)
            normal_key_items.remove(item_id)


    # Precompute BossSpots which have Nizbel or Retinite
    # Only needed with element locks
    nizbel_spots = {
        spot for spot, boss in boss_assignment.items()
        if boss in (bty.BossID.NIZBEL,)
    }
    nizbel_rule = logictypes.LogicRule([
        [ctenums.CharID.CRONO],
        [ctenums.CharID.ROBO, ctenums.CharID.MAGUS]
    ])

    retinite_spots = {
        spot for spot, boss in boss_assignment.items()
        if boss == bty.BossID.RETINITE
    }
    retinite_rule = logictypes.LogicRule([[ctenums.CharID.MARLE],
                                          [ctenums.CharID.FROG]])

    while True:
        # Build a candidate map
        exit_connectors = entrancerandomizer.get_random_exit_connectors(entrance_options, rng)
        region_connectors = regionmap.get_default_region_connectors(recruit_assignment, logic_options)
        region_map = entrancerandomizer.get_shuffled_map_from_connectors(
            exit_connectors, region_connectors
        )

        if entrance_options.shuffle_gates:
            portal_assignment = portalshuffle.get_random_portal_assignment(rng)
            portalshuffle.shuffle_map_portals(region_map, portal_assignment)

        # Find Regions with Nizbel/Retinite
        if not logic_options.disable_element_locks:
            nizbel_regions = {
                region_name for region_name, loc_region in region_map.loc_region_dict.items()
                if nizbel_spots.intersection(loc_region.reward_spots)
            }

            retinite_regions = {
                region_name for region_name, loc_region in region_map.loc_region_dict.items()
                if retinite_spots.intersection(loc_region.reward_spots)
            }

            # Update Nizbel/Retinite Rules
            for connector_list in region_map.name_connector_dict.values():
                for connector in connector_list:
                    if connector.to_region_name in nizbel_regions:
                        connector.rule &= nizbel_rule
                    elif connector.to_region_name in retinite_regions:
                        connector.rule &= retinite_rule

        # Starting Rewards
        region_map.loc_region_dict["starting_rewards"].region_rewards.extend(
            logic_options.starter_rewards
        )

        if entrancerandomizer.is_map_viable(region_map):
            excluded_spots = list(set(logic_options.forced_excluded_spots).union(logic_options.excluded_spots))
            for _ in range(5):
                # Shuffle KI list so that the possible loose ones are at the end in random order
                rng.shuffle(normal_key_items)
                rng.shuffle(possible_loose)
                key_items = normal_key_items + possible_loose

                treasure_assignment = fill_key_items(
                    region_map, initial_treasure_assignment, recruit_assignment, key_items,
                    excluded_spots,list(logic_options.forced_spots), list(logic_options.incentive_spots),
                    logic_options.incentive_factor, logic_options.decay_factor, rng
                )
                if verify_fill(region_map, treasure_assignment, recruit_assignment,
                               logic_options):
                    break
            else:
                continue

            break
        else:
            pass
            # print("not viable")
            # input()

    entrance_assignment = entrancerandomizer.get_ow_exit_assign_dict(exit_connectors)
    return treasure_assignment, entrance_assignment, region_map


def fill_key_items(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, list[ctenums.CharID]],
        key_item_list: list[ctenums.ItemID],
        prohibited_spots: list[ctenums.TreasureID],
        forced_spots: list[ctenums.TreasureID],
        incentive_spots: list[ctenums.TreasureID],
        incentive_factor: float,
        decay_factor: float,
        rng: RNGType,
) -> dict[ctenums.TreasureID, ttypes.RewardType]:
    """
    Put key items in key item spots.  Assumes the key items are already shuffled
    so that the low priority ones are at the end of the list.
    """
    working_treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType] = {
        tid: ctenums.ItemID.NONE
        for tid in ctenums.TreasureID
        if tid not in prohibited_spots
    }
    working_treasure_dict.update(treasure_dict)

    # rng.shuffle(key_item_list)
    forced_keys = key_item_list[0: len(forced_spots)]

    for key, spot in zip(forced_keys, forced_spots):
        working_treasure_dict[spot] = key

    if len(forced_spots) < len(key_item_list):
        remaining_keys = key_item_list[len(forced_spots):]
        spot_weights: dict[ctenums.TreasureID, float] = {
            spot: (incentive_factor if spot in incentive_spots else 1)
            for spot in ctenums.TreasureID
        }

        working_treasure_dict = fill_weighted_random_decay(
            region_map, remaining_keys, working_treasure_dict,
            recruit_dict, spot_weights, decay_factor, include_shops=False,
            rng=rng
        )

    return working_treasure_dict


def get_trimmed_region_dict(
        region_map: regionmap.RegionMap,
        include_shops: bool = False,
) -> dict[str, list[ctenums.TreasureID]]:
    allowed_type = ctenums.TreasureID
    if include_shops:
        allowed_type = allowed_type | ctenums.ShopID

    groups = region_map.get_treasure_group_dict()
    trimmed_groups = {
        name: list(spot for spot in spots if isinstance(spot, allowed_type))
        for name, spots in groups.items()
    }
    trimmed_groups = {
        name: spots
        for name, spots in trimmed_groups.items() if spots
    }

    return trimmed_groups


def _get_random_group(
        group_weights: dict[str, float],
        rng: RNGType
) -> str:
    """
        Returns group name chosen randomly according to weights.
        """
    group_weight_pairs = [
        (weight, name) for name, weight in group_weights.items() if weight != 0
    ]

    dist = distribution.Distribution(*group_weight_pairs)
    return dist.get_random_item(rng)


def _get_random_tid_from_group(
        tids: list[ctenums.TreasureID],
        spot_weights: dict[ctenums.TreasureID, float],
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        rng: RNGType
):
    weight_spot_pairs = [
        (spot_weights[spot], spot)
        for spot in tids
        if spot in treasure_dict and treasure_dict[spot] == ctenums.ItemID.NONE
    ]
    dist = distribution.Distribution(*weight_spot_pairs)
    tid = dist.get_random_item(rng)
    return tid


def fill_weighted_random_decay(
        region_map: regionmap.RegionMap,
        items_to_assign: list[ctenums.ItemID],
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, list[ctenums.CharID]],
        spot_weights: dict[ctenums.TreasureID, float],
        decay_factor: float,
        include_shops: bool,
        rng: RNGType
) -> dict[ctenums.TreasureID, ttypes.RewardType]:


    groups = get_trimmed_region_dict(region_map, include_shops)
    num_assignments = {name: 0 for name in groups}

    items_to_assign = sorted(items_to_assign)
    rng.shuffle(items_to_assign)

    ret_dict = dict(treasure_dict)

    while items_to_assign:
        next_item = items_to_assign.pop()
        traverser = maptraversal.MapTraverser(
            region_map, "starting_rewards", items_to_assign
        )

        traverser.maximize(ret_dict, recruit_dict)
        avail_spots = sorted(traverser.reached_regions)
        available_groups = {
            key: item for (key, item) in groups.items()
            if key in traverser.reached_regions
        }

        group_weights: dict[str, float] = dict()
        for name, tids in available_groups.items():
            trimmed_tids = [tid for tid in tids
                            if tid in ret_dict and ret_dict[tid] == ctenums.ItemID.NONE]
            weight = sum(spot_weights.get(tid, 0) for tid in trimmed_tids)
            if weight != 0:
                group_weights[name] = weight

        for name, weight in group_weights.items():
            group_weights[name] = weight*(decay_factor**num_assignments[name])

        group = _get_random_group(group_weights, rng)
        tid = _get_random_tid_from_group(available_groups[group],
                                         spot_weights, ret_dict, rng)
        # print(f"Assign {next_item} to {tid} in group {group}")
        # input()
        ret_dict[tid] = next_item
        num_assignments[group] += 1

    return ret_dict


def verify_fill(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, list[ctenums.CharID]],
        logic_options: logicoptions.LogicOptions,
        starting_region: str = "starting_rewards",
) -> bool:
    traverser = maptraversal.MapTraverser(
        region_map,
        starting_region
    )

    sphere = 0
    flight_sphere: int | None = None
    # dark_ages_sphere: int | None = None

    while True:
        orig_reached = set(traverser.reached_regions)
        traverser.step(treasure_dict, recruit_dict)
        if (
                flight_sphere is None and
                logictypes.ScriptReward.FLIGHT in traverser.game.other_rewards
        ):
            flight_sphere = sphere

        # if (
        #         dark_ages_sphere is None and
        #         memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS in traverser.game.other_rewards
        # ):
        #     dark_ages_sphere = sphere

        if traverser.reached_regions == orig_reached:
            break

        sphere += 1

    # traverser.maximize(treasure_dict, recruit_dict)

    total_regions = set(region_map.name_connector_dict.keys())
    missed_regions = total_regions.difference(traverser.reached_regions)
    if missed_regions:
        # print("Missed:")
        # for region_name in missed_regions:
        #     print(f"\t{region_name}")
        # # input()
        # print("Collected:")
        # print("  Items:")
        # for item in traverser.game.key_items:
        #     print(f"\t{item}")
        # print("  Chars:")
        # for char in traverser.game.characters:
        #     print(f"\t{char}")
        # print("  Flags:")
        # for other in traverser.game.other_rewards:
        #     print(f"\t{other}")
        # print("Remaining Connections")
        # for connection in traverser.available_connectors:
        #     print(f"\t{connection.link_name}")
        return False

    if flight_sphere < logic_options.min_flight_depth:
        return False

    # print(sphere, flight_sphere)
    # input()
    return True


def forward_fill_key_items(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
        key_item_list: list[ctenums.ItemID],
        prohibited_spots: list[ctenums.TreasureID],
        forced_spots: list[ctenums.TreasureID],
        incentive_spots: list[ctenums.TreasureID],
        incentive_factor: float,
        decay_factor: float,
        rng: RNGType
) -> dict[ctenums.TreasureID, ttypes.RewardType] | None:
    """Perform a forward fill.  This is fallback for when generation stalls."""

    groups = get_trimmed_region_dict(region_map, False)
    working_treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType] = {
        tid: ctenums.ItemID.NONE
        for tid in ctenums.TreasureID
        if tid not in prohibited_spots
    }

    forced_assignment = _forward_fill_forced_recursive(
        region_map, groups, key_item_list, forced_spots,
        working_treasure_dict, recruit_dict, rng
    )
    if forced_assignment is None:
        return None

    used_key_items = [
        key_item for spot, key_item in forced_assignment.items()
        if spot in forced_spots
    ]

    remaining_keys = list(key_item_list)
    for key_item in used_key_items:
        remaining_keys.remove(key_item)

    if remaining_keys:
        spot_weights: dict[ctenums.TreasureID, float] = {
            spot: (incentive_factor if spot in incentive_spots else 1)
            for spot in ctenums.TreasureID
        }
        assignment = fill_weighted_random_decay(
            region_map, remaining_keys, forced_assignment, recruit_dict,
            spot_weights, decay_factor, include_shops=False, rng=rng
        )
        return assignment

    return forced_assignment


def _forward_fill_forced_recursive(
        region_map: regionmap.RegionMap,
        group_tid_dict: dict[str, list[ctenums.TreasureID]],
        remaining_key_items: list[ctenums.ItemID],
        remaining_forced_spots: list[ctenums.TreasureID],
        current_assignment: dict[ctenums.TreasureID, ctenums.ItemID],
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID | None],
        rng: RNGType
) -> dict[ctenums.TreasureID, ctenums.ItemID] | None:

    if not remaining_forced_spots:
        return current_assignment

    traverser = maptraversal.MapTraverser(region_map, "starting_rewards")
    traverser.maximize(current_assignment, recruit_dict)

    available_forced_tids = [
        tid for (region_name, tids) in group_tid_dict.items()
        for tid in tids
        if tid in remaining_forced_spots and current_assignment[tid] == ctenums.ItemID.NONE
    ]

    rng.shuffle(remaining_key_items)

    for ind, key in enumerate(remaining_key_items):
        # For the purposes of forward fill, it should not matter which of the
        # available spots is filled.
        spot = rng.choice(available_forced_tids)

        # Try assigning key to spot
        current_assignment[spot] = key
        result = _forward_fill_forced_recursive(
            region_map, group_tid_dict,
            remaining_key_items[:ind] + remaining_key_items[ind+1:],
            [x for x in remaining_forced_spots if x != spot],
            current_assignment, recruit_dict,
            rng
        )
        if result is not None:
            return result

        # Undo assignment.
        current_assignment[spot] = ctenums.ItemID.NONE

    return None

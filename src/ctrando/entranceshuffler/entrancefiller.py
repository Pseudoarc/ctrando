"""Fill with the entrance shuffler logic."""
from ctrando.arguments import entranceoptions, logicoptions
from ctrando.logic import logictypes

from ctrando.common import ctenums, distribution, memory
from ctrando.common.random import RNGType
from ctrando.treasures import treasuretypes as ttypes
from ctrando.entranceshuffler import regionmap, maptraversal, entrancerandomizer


def get_forced_key_items():
    return [
        ctenums.ItemID.C_TRIGGER, ctenums.ItemID.CLONE,
        ctenums.ItemID.PENDANT, ctenums.ItemID.PENDANT_CHARGE, ctenums.ItemID.DREAMSTONE,
        ctenums.ItemID.RUBY_KNIFE, ctenums.ItemID.JETSOFTIME,
        ctenums.ItemID.TOOLS, ctenums.ItemID.RAINBOW_SHELL,
        ctenums.ItemID.PRISMSHARD, ctenums.ItemID.JERKY, ctenums.ItemID.JERKY,
        ctenums.ItemID.BENT_HILT, ctenums.ItemID.BENT_SWORD,
        ctenums.ItemID.HERO_MEDAL, ctenums.ItemID.MASAMUNE_1,
        # ItemID.MASAMUNE_2,  This doesn't unlock anything so not forced
        ctenums.ItemID.TOMAS_POP, ctenums.ItemID.MOON_STONE, ctenums.ItemID.SUN_STONE,
        ctenums.ItemID.BIKE_KEY, ctenums.ItemID.SEED, ctenums.ItemID.GATE_KEY
    ]


def update_starting_rewards(
        starting_rewards: list[logictypes.RewardType],
        entrance_options: entranceoptions.EntranceShufflerOptions,
):
    if entrance_options.shuffle_entrances:
        starting_rewards.append(memory.Flags.OW_LAVOS_HAS_FALLEN)


def get_key_item_fill(
        initial_treasure_assignment: dict[ctenums.TreasureID, ctenums.ItemID],
        recruit_assignment: dict[ctenums.RecruitID, ctenums.CharID],
        logic_options: logicoptions.LogicOptions,
        entrance_options: entranceoptions.EntranceShufflerOptions,
        rng: RNGType
) -> tuple[dict[ctenums.TreasureID, ctenums.ItemID], dict[regionmap.OWExit, regionmap.OWExit]]:

    forced_key_items = get_forced_key_items()

    key_items = forced_key_items + logic_options.additional_key_items
    for item in initial_treasure_assignment.values():
        if item in key_items:
            key_items.remove(item)

    while True:
        exit_connectors = entrancerandomizer.get_random_exit_connectors(entrance_options, rng)
        # for x in exit_connectors:
        #     if x.from_exit in entrance_options.preserve_spots:
        #     print(f"{x.from_exit} --> {x.to_exit}")
        # input()
        region_connectors = regionmap.get_default_region_connectors(recruit_assignment, logic_options)
        region_map = entrancerandomizer.get_shuffled_map_from_connectors(
            exit_connectors, region_connectors
        )

        region_map.loc_region_dict["starting_rewards"].region_rewards.extend(
            logic_options.starter_rewards
        )
        if entrancerandomizer.is_map_viable(region_map):
            for _ in range(5):
                treasure_assignment = fill_key_items(
                    region_map, initial_treasure_assignment, recruit_assignment, key_items,
                    logic_options.excluded_spots, logic_options.forced_spots, logic_options.incentive_spots,
                    logic_options.incentive_factor, logic_options.decay_factor, rng
                )
                if verify_fill(region_map, treasure_assignment, recruit_assignment):
                    break
            else:
                continue

            break
        else:
            print("not viable")
            # input()

    entrance_assignment = entrancerandomizer.get_ow_exit_assign_dict(exit_connectors)

    return treasure_assignment, entrance_assignment


def fill_key_items(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
        key_item_list: list[ctenums.ItemID],
        prohibited_spots: list[ctenums.TreasureID],
        forced_spots: list[ctenums.TreasureID],
        incentive_spots: list[ctenums.TreasureID],
        incentive_factor: float,
        decay_factor: float,
        rng: RNGType,
) -> dict[ctenums.TreasureID, ttypes.RewardType]:
    working_treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType] = {
        tid: ctenums.ItemID.NONE
        for tid in ctenums.TreasureID
        if tid not in prohibited_spots
    }
    working_treasure_dict.update(treasure_dict)

    rng.shuffle(key_item_list)
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
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
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

        group_weights: dict[str: float] = dict()
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
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
        starting_region: str = "starting_rewards"
) -> bool:
    traverser = maptraversal.MapTraverser(
        region_map,
        starting_region
    )
    traverser.maximize(treasure_dict, recruit_dict)

    total_regions = set(region_map.name_connector_dict.keys())
    missed_regions = total_regions.difference(traverser.reached_regions)
    if missed_regions:
        # print("Missed:")
        # for region_name in missed_regions:
        #     print(f"\t{region_name}")
        # input()
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
        working_treasure_dict, recruit_dict
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

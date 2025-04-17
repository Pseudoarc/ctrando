"""
Filler that weighs groups and uses decay to spread the assignment
"""
import typing
from copy import deepcopy
from dataclasses import dataclass

import logic.logictypes
from ctrando.common import ctenums, distribution

from logic.rewardstructure import RewardStructure


@dataclass
class _AssignData:
    current_weight: float
    num_assignments: int


def _gather_initial_data(
        reward_structure: RewardStructure,
        spot_weights: dict[ctenums.TreasureID, float],
        ignore_items: typing.Optional[list[ctenums.ItemID]] = None
) -> dict[str, _AssignData]:
    """
    Gather weight and number of assignments for each group.
    Only count assignments of items in count_items.
    """
    if ignore_items is None:
        ignore_items = []

    working_ignore_items: list[typing.Optional[ctenums.ItemID]] = ignore_items + [None]
    ret_dict: dict[str, _AssignData] = dict()
    for name, group in reward_structure.group_dict.items():

        num_assignments = sum(
            1 for tid in group.treasure_spots
            if reward_structure.treasure_dict[tid].reward not in working_ignore_items
        )

        current_weight = sum(
            spot_weights.get(tid, 1)
            for tid in group.treasure_spots
            if reward_structure.treasure_dict[tid].reward is None
        )
        ret_dict[name] = _AssignData(current_weight, num_assignments)

    return ret_dict


def _get_random_group(group_weights: dict[str, float]) -> str:
    """
    Returns group name chosen randomly according to weights.
    """
    group_weight_pairs = [
        (weight, name) for name, weight in group_weights.items() if weight != 0
    ]

    dist = distribution.Distribution(*group_weight_pairs)
    return dist.get_random_item()


def _get_random_tid_from_group(
    reward_structure: RewardStructure,
    group_name: str,
    spot_weights: dict[ctenums.TreasureID, float],
):
    """Get a random TID from a group according to weights."""
    group = reward_structure.group_dict[group_name]
    weight_spot_pairs = [
        (spot_weights[spot], spot)
        for spot in group.treasure_spots
        if reward_structure.treasure_dict[spot].reward is None
    ]

    dist = distribution.Distribution(*weight_spot_pairs)
    tid = dist.get_random_item()

    return tid


def fill_weighted_random_decay(
    reward_structure: RewardStructure,
    items_to_assign: list[ctenums.ItemID],
    spot_weights: dict[ctenums.TreasureID, float],
    decay_factor: float = 0.7,
) -> RewardStructure:
    """
    Fill randomly but allow each spot to have a weight.  Discourage repeat assignments
    to the same group with decay_factor.
    """

    ret_rs = deepcopy(reward_structure)

    weight_data = _gather_initial_data(ret_rs, spot_weights)
    items_to_assign = sorted(items_to_assign)

    while items_to_assign:

        next_item = items_to_assign.pop()

        # TODO: decide assumed or not.

        # Assumed filler allows for strange placements.
        #  - Pure random will almost never allow a buried item because the random fill is highly
        #    unlikely to place the rest of the items in a configuration to accommodate that.
        #  - Assumed filler will tend to dump more items into early spheres because once there's
        #    an obstruction, the location pool is diminished until the obstruction is removed.
        #  - Possibly, try to always place an unclogger before placing others.

        # No Assumed:
        # Only consider groups for which the given key is not forced
        # possible_group_names = [
        #     name
        #     for name, group in ret_rs.group_dict.items()
        #     if next_item not in group.access_rule.get_forced_keys()
        # ]

        # Assumed
        assumed_game = logic.logictypes.Game(set(), items_to_assign)
        assumed_game = ret_rs.get_maximized_game(assumed_game)
        possible_group_names = ret_rs.get_reachable_group_names(assumed_game)

        current_weights = {
            name: data.current_weight * (decay_factor**data.num_assignments)
            for name, data in weight_data.items()
            if name in possible_group_names
        }

        # import pprint
        # pprint.pprint(current_weights)
        # input()

        # for name, data in current_weights.items():
        #     print(f"{name}: {data}")

        chosen_group_name = _get_random_group(current_weights)
        chosen_tid = _get_random_tid_from_group(ret_rs, chosen_group_name, spot_weights)
        print(f"Placing {next_item} in {chosen_tid}")
        # input()

        ret_rs.assign_treasure(chosen_tid, next_item)
        weight_data[chosen_group_name].num_assignments += 1
        weight_data[chosen_group_name].current_weight -= spot_weights[chosen_tid]

    return ret_rs

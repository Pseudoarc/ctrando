"""Module for simple random assignment of items."""
# import random

from ctrando.common import ctenums
from logic.rewardstructure import RewardStructure
from logic.rewardfiller import FailedFillException


def fill_random(
        reward_structure: RewardStructure,
        items_to_assign: list[ctenums.ItemID],
):
    """
    Uniformly randomly assign items_to_assign to the spots in reward_structure.
    The only exception is that items will not be put in places immediately locked by
    that item.
    """

    working_items = list(items_to_assign)
    while working_items:
        next_item = working_items.pop()

        avail_group_names = [
            name for name, group in reward_structure.group_dict.items()
            if next_item not in group.access_rule.get_forced_keys()
        ]

        avail_spots = [
            treasure_id for treasure_id, rs_entry in reward_structure.treasure_dict.items()
            if rs_entry.group_name in avail_group_names and rs_entry.reward is None
        ]

        if not avail_spots:
            raise FailedFillException

        chosen_spot = random.choice(avail_spots)
        reward_structure.assign_treasure(chosen_spot, next_item)

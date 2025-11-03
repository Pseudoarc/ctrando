"""Walk through a Map and collect rewards."""
import typing
from typing import Any

from ctrando.common import ctenums, memory
from ctrando.entranceshuffler.regionmap import RegionConnector
from ctrando.logic.logictypes import Game
from ctrando.entranceshuffler import regionmap
from ctrando.treasures import treasuretypes as ttypes


class MapTraverser:
    def __init__(
            self,
            region_map: regionmap.RegionMap,
            starting_name: str,
            starting_rewards: list[Any] | None = None
    ):
        self.region_map = region_map
        self.starting_name = starting_name
        self.starting_rewards = [] if starting_rewards is None else list(starting_rewards)
        self.reached_regions: set[str] = set()
        self.available_connectors: set[RegionConnector] = set()

        useful_items: set[typing.Any] = set()
        for name, connectors in self.region_map.name_connector_dict.items():
            for connector in connectors:
                for rule in connector.rule.get_access_rule():
                    rule_items = [x for x in rule if isinstance(x, ctenums.ItemID)]
                    useful_items.update(rule_items)
        self.useful_items = useful_items

        game = Game()
        if starting_rewards is not None:
            for reward in starting_rewards:
                if isinstance(reward, ctenums.ItemID):
                    game.key_items.append(reward)
                elif isinstance(reward, ctenums.CharID):
                    game.characters.add(reward)
                else:
                    game.other_rewards.add(reward)
        self.game = game

    def add_region_connectors(self, region_name: str):
        connectors = self.region_map.name_connector_dict[region_name]
        for connector in connectors:
            if connector.to_region_name not in self.reached_regions:
                self.available_connectors.add(connector)

    def add_region_rewards(
            self,
            region_name: str,
            treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
            recruit_dict: dict[ctenums.RecruitID, ctenums.CharID | None],
            rewards_to_skip: set[Any] = None,
            log_flags: bool = False
    ) -> list[str]:
        rewards_summary: list[str] = []

        if rewards_to_skip is None:
            rewards_to_skip = set()

        if region_name in self.region_map.loc_region_dict:
            region = self.region_map.loc_region_dict[region_name]
            # for reward in region.region_rewards:
            #     if reward not in self.game.other_rewards and reward not in rewards_to_skip:
            #         ... # print(f"Gained {reward} from {region_name}")
            region_rewards = set(region.region_rewards).difference(rewards_to_skip)

            for reward in region_rewards:
                if isinstance(reward, memory.Flags) or reward in self.game.other_rewards:
                    continue
                if reward not in self.game.other_rewards:
                    rewards_summary.append(f"Gained {reward} from {region_name}")

            self.game.other_rewards.update(region_rewards)

            for spot in region.reward_spots:
                reward: Any = None
                if isinstance(spot, ctenums.TreasureID):
                    reward = treasure_dict.get(spot, None)
                    if reward in self.useful_items and reward not in rewards_to_skip:
                        self.game.key_items.append(reward)
                    else:
                        reward = None
                elif isinstance(spot, ctenums.RecruitID):
                    reward = recruit_dict[spot]
                    if reward is not None and reward not in rewards_to_skip:
                        self.game.characters.add(reward)
                else:
                    ...
                    # print(spot)

                if reward is not None and not isinstance(reward, ctenums.ShopID):
                    rewards_summary.append(f"Gained {reward} from {spot}")

        return rewards_summary

    def maximize(
            self,
            treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
            recruit_dict: dict[ctenums.RecruitID, ctenums.CharID | None],
            rewards_to_skip: set[Any] = None,
            regions_to_skip: set[str] = None
    ):
        if regions_to_skip is None:
            regions_to_skip = set()
        if rewards_to_skip is None:
            rewards_to_skip = set()

        sphere = 0
        while True:
            # header = f"Sphere {sphere}"
            # print(header)
            # print("-" * len(header))
            orig_reached = set(self.reached_regions)
            # print(len(orig_reached))
            self.step(treasure_dict, recruit_dict, rewards_to_skip, rewards_to_skip)
            if self.reached_regions == orig_reached:
                break

            sphere += 1

    def step(
            self,
            treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
            recruit_dict: dict[ctenums.RecruitID, ctenums.CharID | None],
            rewards_to_skip: set[Any] = None,
            regions_to_skip: set[str] = None,
            log_connectors: bool = False
    ) -> list[str]:

        if regions_to_skip is None:
            regions_to_skip = set()
        if rewards_to_skip is None:
            rewards_to_skip = set()

        step_summary: list[str] = []
        step_regions: list[str] = []

        if not self.reached_regions:
            self.reached_regions.add(self.starting_name)
            step_regions.append(self.starting_name)
            step_summary.append(f"Begin in {self.starting_name}.")
            self.add_region_connectors(self.starting_name)

        while True:
            new_regions = list()
            connectors = sorted(self.available_connectors,
                                key = lambda x:x.link_name)
            for connector in connectors:  # list(self.available_connectors):
                to_region_name = connector.to_region_name
                has_region = to_region_name in self.reached_regions.union(new_regions)

                if to_region_name in regions_to_skip:
                    self.available_connectors.remove(connector)
                elif connector.rule(self.game):
                    if not has_region:
                        new_regions.append(to_region_name)
                        if log_connectors:
                            step_summary.append(
                                f"Followed {connector.link_name} from {connector.from_region_name} "
                                f"to {connector.to_region_name}")
                    else:
                        self.available_connectors.remove(connector)

            if not new_regions:
                break

            step_regions.extend(new_regions)
            self.reached_regions.update(new_regions)
            for region in new_regions:
                self.add_region_connectors(region)

        # We use a list to keep the regions in traversal order.
        for region_name in step_regions:
            step_summary.extend(
                self.add_region_rewards(region_name, treasure_dict, recruit_dict,
                                        rewards_to_skip)
            )
        return step_summary


def is_map_traversable(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
        starting_rewards: list[typing.Any] = None
) -> bool:
    traverser = MapTraverser(region_map, "starting_rewards", starting_rewards)
    traverser.maximize(treasure_dict, recruit_dict)

    total_regions = set(region_map.name_connector_dict.keys())
    if traverser.reached_regions == total_regions:
        return True

    print("Missed:")
    for x in total_regions.difference(traverser.reached_regions):
        print(f"\t{x}")

    return False


def get_sphere_dict(
        region_map: regionmap.RegionMap,
        treasure_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        recruit_dict: dict[ctenums.RecruitID, ctenums.CharID],
        starting_rewards: list[typing.Any] = None
) -> dict[str, int]:
    """
    Return a dictionary of region name -> sphere number
    """
    sphere = 0
    traverser = MapTraverser(region_map, "starting_rewards", starting_rewards)

    total_regions = set(region_map.name_connector_dict.keys())
    ret_dict = {name: 0 for name in total_regions}

    while True:
        traverser.step(treasure_dict, recruit_dict)
        regions = traverser.reached_regions
        regions.intersection_update(total_regions)

        if not regions:
            raise ValueError

        for region in regions:
            ret_dict[region] = sphere

        total_regions.difference_update(regions)
        if not total_regions:
            break

        sphere += 1

    return ret_dict


def main():
    pass


if __name__ == "__main__":
    main()


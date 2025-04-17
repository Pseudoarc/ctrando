from dataclasses import dataclass

from ctrando.common import ctenums, distribution
from ctrando.logic.logictypes import Game
from logic.rewardstructure import RewardStructure


class FailedFillException(Exception):
    """Raise when a fill fails."""


@dataclass
class _AssignData:
    weight: float = 0.0
    num_assignments: int = 0


def _build_assign_data(
    reward_structure: RewardStructure,
    incentive_spots: list[ctenums.TreasureID],
    incentive_factor: float,
) -> dict[str, _AssignData]:
    """
    Compute weights of groups at the start of generation
    """

    ret_dict: dict[str, _AssignData] = dict()
    for name, group in reward_structure.group_dict.items():
        open_tid_spots = [
            spot
            for spot, reward in group.reward_assignment.items()
            if isinstance(spot, ctenums.TreasureID) and reward is None
        ]
        filled_tid_spots = [
            spot
            for spot, reward in group.reward_assignment.items()
            if isinstance(spot, ctenums.TreasureID) and reward is not None
        ]
        weight = sum(
            1 if spot not in incentive_spots else incentive_factor
            for spot in open_tid_spots
            if spot not in incentive_spots
        )
        num_assignments = len(filled_tid_spots)

        if weight != 0:
            ret_dict[name] = _AssignData(weight, num_assignments)

    return ret_dict


def verify_fill(reward_structure: RewardStructure) -> bool:
    """Returns True if reward_structure is 100%able."""

    current_game = Game()

    while True:
        new_game = reward_structure.get_updated_game(current_game)
        if new_game == current_game:
            if reward_structure.get_unreachable_group_names(current_game):
                return False
            return True

        current_game = new_game


def prove_fill(reward_structure: RewardStructure) -> bool:
    current_game = Game()

    sphere = 0
    while True:
        print(f"Sphere {sphere}:")
        print("===============")
        new_game = reward_structure.get_updated_game(current_game, print_annotations=True)
        if new_game == current_game:
            unreachable_names = reward_structure.get_unreachable_group_names(current_game)
            if unreachable_names:
                print("Failed to reach:")
                for name in unreachable_names:
                    group = reward_structure.group_dict[name]
                    missed_keys = [
                        reward_structure.treasure_dict[key].reward for key in group.treasure_spots
                        if reward_structure.treasure_dict[key].reward is not None
                    ]
                    print(f"{name}: " +
                          ', '.join(str(reward) for reward in missed_keys))
                return False
            return True

        sphere += 1
        current_game = new_game

"""Module to make a RewardStructure for a randomized game."""
from itertools import combinations

from ctrando.common.ctenums import TreasureID as TID, CharID, RecruitID, ItemID
from ctrando.common.memory import Flags
from ctrando.logic.logictypes import LogicRule, ScriptReward, RewardType



class ProgressiveRule:
    def __init__(self, progression: list[RewardType]):
        self.progression = list(progression)

    def __call__(self, progression_level: int = 1) -> LogicRule:
        progression_level = sorted([1, progression_level, len(self.progression)])[1]

        rules = [
            list(x) for x in combinations(self.progression, progression_level)
        ]

        return LogicRule(rules)


_progressive_pendant_rule = ProgressiveRule([ItemID.PENDANT, ItemID.PENDANT_CHARGE])
_progressive_sword_rule = ProgressiveRule([ItemID.MASAMUNE_1, ItemID.MASAMUNE_2])
_progressive_clone_rule = ProgressiveRule([ItemID.C_TRIGGER, ItemID.CLONE])
_progressive_shell_rule = ProgressiveRule([ItemID.RAINBOW_SHELL, ItemID.PRISMSHARD])
_progressive_bike_key_rule = ProgressiveRule([ItemID.BIKE_KEY, ItemID.RACE_LOG])

_fair_recruit_item: dict[CharID, ItemID] = {
    CharID.CRONO: ItemID.BIKE_KEY,
    CharID.MARLE: ItemID.PENDANT,
    CharID.LUCCA: ItemID.GATE_KEY,
    CharID.ROBO: ItemID.SEED,
    CharID.FROG: ItemID.HERO_MEDAL,
    CharID.AYLA: ItemID.DREAMSTONE,
    # CharID.MAGUS: ItemID.PENDANT_CHARGE
    CharID.MAGUS: ItemID.RUBY_KNIFE
}


def get_fair_recruit_item(char_id: CharID) -> ItemID:
    return _fair_recruit_item[char_id]


if __name__ == '__main__':
    pass

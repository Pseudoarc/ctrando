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


def can_access_magus_castle() -> LogicRule:
    """Logic Rule for accessing Magus's Castle."""


def can_access_dark_ages() -> LogicRule:
    """Logic Rule for getting to Dark Ages"""
    return LogicRule(
        # initial_rules=[
        #     [ItemID.PENDANT, ItemID.PENDANT_CHARGE],
        #     [ItemID.DREAMSTONE],
        #     [ItemID.MASAMUNE_1, CharID.FROG]
        # ]
        [Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS]
    )

def can_access_factory() -> LogicRule:
    """Condition for accessing factory."""
    return LogicRule([CharID.ROBO]) & (LogicRule([ItemID.BIKE_KEY]) | can_fly())


def can_access_eot() -> LogicRule:
    """Logic Rule for getting to End of Time"""
    char_combs = combinations(CharID, 4)
    rule = list(list(x) for x in char_combs)

    char_rule = LogicRule(rule) & LogicRule([ItemID.GATE_KEY])
    return can_access_factory() | char_rule


def can_access_tyrano_lair() ->  LogicRule:
    """Logic Rule for getting to Tyrano Lair"""
    return can_fly() | LogicRule([ItemID.DREAMSTONE])

def can_fly() ->  LogicRule:
    # flight_from_da = LogicRule(
    #     initial_rules=[
    #         [ItemID.PENDANT_CHARGE, ItemID.RUBY_KNIFE],
    #         [ItemID.JETSOFTIME]
    #     ]
    # )
    # return can_access_dark_ages() & flight_from_da
    return LogicRule([ScriptReward.FLIGHT])


if __name__ == '__main__':
    pass

import argparse
from collections.abc import Iterable
import functools
import typing
from ctrando.arguments.argumenttypes import str_to_enum, str_to_enum_dict
from ctrando.common import ctenums, memory
from ctrando.logic.logictypes import RewardType, ScriptReward

_treasure_id_str_dict = str_to_enum_dict(ctenums.TreasureID)
_item_id_str_dict = str_to_enum_dict(ctenums.ItemID)


_reward_dict: dict[str, RewardType] = {
    "epoch": ScriptReward.EPOCH,
    "flight": ScriptReward.FLIGHT,
    "dark_ages": memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
    "future": memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS,
    "last_village_portal": memory.Flags.HAS_ALGETTY_PORTAL,
    "end_of_time": memory.Flags.HAS_EOT_TIMEGAUGE_ACCESS,
    "bucket": memory.Flags.BUCKET_AVAILABLE,
    "apocalypse": memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS,
    "omen_present": memory.Flags.OW_OMEN_PRESENT,
    "omen_last_village": memory.Flags.OW_OMEN_DARKAGES,
    "dark_ages_pillar":  memory.Flags.HAS_DARK_AGES_PORTAL,
    "bangor_pillar": memory.Flags.HAS_BANGOR_PORTAL,
    "truce_pillar": memory.Flags.HAS_TRUCE_PORTAL,
    "desert": memory.Flags.PLANT_LADY_SAVES_SEED,
}


def str_to_reward(string: str) -> RewardType:
    """Translate a string into a RewardType."""

    # For now very very limited.
    string = string.lower()
    if string not in _reward_dict:
        raise KeyError

    return _reward_dict[string]


class LogicOptions:
    _default_incentive_factor: typing.ClassVar[float] = 5.0
    _default_decay_factor: typing.ClassVar[float] = 0.7
    _default_hard_lavos_end_boss: typing.ClassVar[bool] = False
    _default_additional_key_items: typing.ClassVar[tuple[ctenums.ItemID, ...]] = tuple()
    _default_incentive_spots: typing.ClassVar[tuple[ctenums.TreasureID, ...]] = tuple()
    _default_forced_spots: typing.ClassVar[tuple[ctenums.TreasureID, ...]] = (
        ctenums.TreasureID.DEATH_PEAK_SOUTH_FACE_SUMMIT,
        ctenums.TreasureID.SUN_PALACE_KEY, ctenums.TreasureID.BEKKLER_KEY,
        ctenums.TreasureID.FAIR_PENDANT, ctenums.TreasureID.ZEAL_MAMMON_MACHINE,
        ctenums.TreasureID.MT_WOE_KEY, ctenums.TreasureID.GIANTS_CLAW_KEY,
        ctenums.TreasureID.KINGS_TRIAL_KEY, ctenums.TreasureID.YAKRAS_ROOM,
        ctenums.TreasureID.SNAIL_STOP_KEY, ctenums.TreasureID.DENADORO_MTS_KEY,
        ctenums.TreasureID.FROGS_BURROW_LEFT, ctenums.TreasureID.MELCHIOR_FORGE_MASA,
        ctenums.TreasureID.CYRUS_GRAVE_KEY, ctenums.TreasureID.TATA_REWARD,
        ctenums.TreasureID.FIONA_KEY, ctenums.TreasureID.SUN_KEEP_2300,
        ctenums.TreasureID.JERKY_GIFT, ctenums.TreasureID.ARRIS_DOME_DOAN_KEY,
        ctenums.TreasureID.ARRIS_DOME_FOOD_LOCKER_KEY, ctenums.TreasureID.REPTITE_LAIR_KEY,
        ctenums.TreasureID.TABAN_GIFT_VEST, ctenums.TreasureID.GENO_DOME_BOSS_1
    )
    _default_excluded_spots: typing.ClassVar[tuple[ctenums.TreasureID]] = (
        # Magus
        ctenums.TreasureID.MAGUS_CASTLE_RIGHT_HALL, ctenums.TreasureID.MAGUS_CASTLE_GUILLOTINE_1,
        ctenums.TreasureID.MAGUS_CASTLE_GUILLOTINE_2, ctenums.TreasureID.MAGUS_CASTLE_SLASH_ROOM_1,
        ctenums.TreasureID.MAGUS_CASTLE_SLASH_ROOM_2, ctenums.TreasureID.MAGUS_CASTLE_SLASH_SWORD_FLOOR,
        ctenums.TreasureID.MAGUS_CASTLE_STATUE_HALL, ctenums.TreasureID.MAGUS_CASTLE_FOUR_KIDS,
        ctenums.TreasureID.MAGUS_CASTLE_OZZIE_1, ctenums.TreasureID.MAGUS_CASTLE_OZZIE_2,
        ctenums.TreasureID.MAGUS_CASTLE_ENEMY_ELEVATOR, ctenums.TreasureID.MAGUS_CASTLE_LEFT_HALL,
        ctenums.TreasureID.MAGUS_CASTLE_UNSKIPPABLES, ctenums.TreasureID.MAGUS_CASTLE_PIT_E,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_NE, ctenums.TreasureID.MAGUS_CASTLE_PIT_NW,
        ctenums.TreasureID.MAGUS_CASTLE_PIT_W, ctenums.TreasureID.MAGUS_CASTLE_FLEA_MAGIC_TAB,
        ctenums.TreasureID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB,
        # Sunken Desert
        ctenums.TreasureID.SUNKEN_DESERT_B1_NE, ctenums.TreasureID.SUNKEN_DESERT_B1_SE,
        ctenums.TreasureID.SUNKEN_DESERT_B1_NW, ctenums.TreasureID.SUNKEN_DESERT_B1_SW,
        ctenums.TreasureID.SUNKEN_DESERT_B2_N, ctenums.TreasureID.SUNKEN_DESERT_B2_NW,
        ctenums.TreasureID.SUNKEN_DESERT_B2_W, ctenums.TreasureID.SUNKEN_DESERT_B2_SW,
        ctenums.TreasureID.SUNKEN_DESERT_B2_SE, ctenums.TreasureID.SUNKEN_DESERT_B2_E,
        ctenums.TreasureID.SUNKEN_DESERT_B2_CENTER, ctenums.TreasureID.SUNKEN_DESERT_POWER_TAB,
        # Tyrano Lair
        ctenums.TreasureID.TYRANO_LAIR_MAZE_1, ctenums.TreasureID.TYRANO_LAIR_MAZE_2,
        ctenums.TreasureID.TYRANO_LAIR_MAZE_3, ctenums.TreasureID.TYRANO_LAIR_MAZE_4,
    )
    _default_starter_rewards: typing.ClassVar[tuple[RewardType,...]] = (ScriptReward.EPOCH,)

    def __init__(
            self,
            additional_key_items: Iterable[ctenums.ItemID] = _default_additional_key_items,
            forced_spots: Iterable[ctenums.TreasureID] = _default_forced_spots,
            incentive_spots: Iterable[ctenums.TreasureID] = _default_incentive_spots,
            incentive_factor: float = _default_incentive_factor,
            excluded_spots: Iterable[ctenums.TreasureID] = _default_excluded_spots,
            decay_factor: float = _default_decay_factor,
            hard_lavos_end_boss: bool = _default_hard_lavos_end_boss,
            starter_rewards: Iterable[RewardType] = _default_starter_rewards
    ):
        self.additional_key_items = sorted(additional_key_items)
        self.forced_spots = forced_spots
        self.incentive_spots = sorted(incentive_spots)
        self.incentive_factor = incentive_factor
        self.excluded_spots = excluded_spots
        self.decay_factor = decay_factor
        self.hard_lavos_final_boss = hard_lavos_end_boss
        self.starter_rewards = starter_rewards

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Add these options to the parser."""

        group = parser.add_argument_group(
            "Logic Options",
            "Options for the distribution of key items"
        )

        group.add_argument(
            "--additional-key-items",
            nargs="+",
            type=functools.partial(str_to_enum, enum_type=ctenums.ItemID),
            help="Extra (non-progression) items to add to the key item pool.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--forced-spots",
            nargs="+",
            type=functools.partial(str_to_enum, enum_type=ctenums.TreasureID),
            help="Spots forced to have key items.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--incentive-spots",
            nargs="+",
            type=functools.partial(str_to_enum, enum_type=ctenums.TreasureID),
            help="Spots with increased probability to have key items.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--incenctive-factor",
            type=float,
            default=argparse.SUPPRESS,
            help="Factor by which to increase the weight of incentive spots."
        )

        group.add_argument(
            "--excluded-spots",
            nargs="+",
            type=functools.partial(str_to_enum, enum_type=ctenums.TreasureID),
            help="Spots which are forbidden to have key items.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--decay-factor",
            type=float,
            help=("Factor by which to decrease the weight of regions which "
                  "have already received items (1.0 = no change)."),
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--starter-rewards",
            nargs="+",
            type=str_to_reward,
            help="Rewards to grant at game start.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--hard-lavos-end-boss",
            action="store_true",
            help="The game will end if Ocean Palace Lavos is defeated.",
            default=argparse.SUPPRESS
        )

    @ classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        attr_names = [
            "additional_key_items", "forced_spots", "incentive_spots",
            "incentive_factor", "excluded_spots", "decay_factor",
            "hard_lavos_end_boss", "starter_rewards"
        ]

        init_dict: dict[str, typing.Any] = dict()

        for attr_name in attr_names:
            if hasattr(namespace, attr_name):
                init_dict[attr_name] = getattr(namespace, attr_name)

        return LogicOptions(**init_dict)

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"additional_key_items={self.additional_key_items}"
            f"forced_spots={self.forced_spots}, "
            f"incentive_spots={self.incentive_spots}, "
            f"incentive_factor={self.incentive_factor}, "
            f"excluded_spots={self.excluded_spots}, "
            f"decay_factor={self.decay_factor})"
        )






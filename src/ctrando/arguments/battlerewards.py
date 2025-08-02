import argparse
import enum
import typing

from ctrando.arguments import argumenttypes
from dataclasses import dataclass, fields


class EnemyPoolType(enum.StrEnum):
    VANILLA = "vanilla"
    ALL = "all"
    # FIXED = "fixed"


class RewardPoolType(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE = "shuffle"
    RANDOM = "random"
    # RANDOM_TIERED = "random_tiered"
    # RANDOM_TIERED_CONSUMABLE = "random_tiered_consumable"


class DropOptions:
    _default_drop_enemy_pool: typing.ClassVar[EnemyPoolType] = EnemyPoolType.VANILLA
    _default_drop_reward_pool: typing.ClassVar[RewardPoolType] = RewardPoolType.VANILLA
    _default_drop_rate: typing.ClassVar[float] = 0.10
    _default_mark_dropping_enemies: typing.ClassVar[bool] = False

    def __init__(
            self,
            drop_enemy_pool=_default_drop_enemy_pool,
            drop_reward_pool=_default_drop_reward_pool,
            drop_rate=_default_drop_rate,
            mark_dropping_enemies=_default_mark_dropping_enemies
    ):
        self.drop_enemy_pool = drop_enemy_pool
        self.drop_reward_pool = drop_reward_pool
        self.drop_rate = drop_rate
        self.mark_dropping_enemies = mark_dropping_enemies

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Enemy Drop Settings",
            description="Settings which modify enemy drops."
        )

        argumenttypes.add_str_enum_to_group(
            group, "--drop-enemy-pool", EnemyPoolType,
            help_str="Pool of enemies which can have a dropped item"
        )

        argumenttypes.add_str_enum_to_group(
            group, "--drop-reward-pool", RewardPoolType,
            help_str="Method of choosing enemy dropped items"
        )

        group.add_argument(
            "--drop-rate",
            action="store", type=float,
            default=argparse.SUPPRESS,
            help="Percentage of enemies in the drop pool which have a dropped item"
        )

        group.add_argument(
            "--mark-dropping-enemies",
            action="store_true",
            default=argparse.SUPPRESS,
            help="Alter enemy names to indicate a dropped item"
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):

        init_dict: dict[str, typing.Any] = {}
        attr_names = (
            "drop_enemy_pool", "drop_reward_pool",
            "drop_rate", "mark_dropping_enemies"
        )

        for attr in attr_names:
            if attr in namespace:
                init_dict[attr] = getattr(namespace, attr)

        return cls(**init_dict)


class CharmOptions:
    _default_charm_enemy_pool: typing.ClassVar[EnemyPoolType] = EnemyPoolType.VANILLA
    _default_charm_reward_pool: typing.ClassVar[RewardPoolType] = RewardPoolType.VANILLA
    _default_charm_rate: typing.ClassVar[float] = 0.05
    _default_mark_charmable_enemies: typing.ClassVar[bool] = False
    def __init__(
            self,
            charm_enemy_pool=_default_charm_enemy_pool,
            charm_reward_pool=_default_charm_reward_pool,
            charm_rate=_default_charm_rate,
            mark_charmable_enemies=_default_mark_charmable_enemies
    ):
        self.charm_enemy_pool = charm_enemy_pool
        self.charm_reward_pool = charm_reward_pool
        self.charm_rate = charm_rate
        self.mark_charmable_enemies = mark_charmable_enemies

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Enemy Charm Settings",
            description="Settings which modify enemy charms."
        )

        argumenttypes.add_str_enum_to_group(
            group, "--charm-enemy-pool", EnemyPoolType,
            help_str="Pool of enemies which can have a charmable item"
        )

        argumenttypes.add_str_enum_to_group(
            group, "--charm-reward-pool", RewardPoolType,
            help_str="Method of choosing enemy charmable items"
        )

        group.add_argument(
            "--charm-rate",
            action="store", type=float,
            default=argparse.SUPPRESS,
            help="Percentage of enemies in the charm pool which have a charmable item"
        )

        group.add_argument(
            "--mark-charmable-enemies",
            action="store_true",
            default=argparse.SUPPRESS,
            help="Alter enemy names to indicate a charmable item"
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        init_dict: dict[str, typing.Any] = {}
        attr_names = (
            "charm_enemy_pool", "charm_reward_pool",
            "charm_rate", "mark_charmable_enemies"
        )

        for attr in attr_names:
            if attr in namespace:
                init_dict[attr] = getattr(namespace, attr)

        return cls(**init_dict)


@dataclass
class XPTPGRewards:
    xp_scale: float = 1.0
    tp_scale: float = 1.0
    g_scale: float = 1.0
    split_xp: bool = False
    split_tp: bool = False
    fix_tp_doubling: bool = False
    xp_penalty_level: int = 99
    xp_penalty_percent: int = 0
    level_cap: int = 60

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Battle Rewards Settings",
            description="Settings which modify post-battle rewards."
        )
        help_dict: dict[str: str] = {
            'xp_scale': "Factor by which to scale XP earned in battle",
            'tp_scale': "Factor by which to scale TP earned in battle",
            'g_scale': "Factor by which to scale G earned in battle",
            'split_xp': "XP is split among living party members rather than shared evenly",
            'split_tp': "TP is split among living party members rather than shared evenly",
            'fix_tp_doubling': "TP rewards are not duplicated for every gained tech level",
            "xp_penalty_level": "Levels past this level become more difficult to obtain",
            "xp_penalty_percent": "For each level beyond the penalty, the requirement grows by this percent",
            "level_cap": "Levels beyond the level cap will have prohibitively large requirements."
        }

        argumenttypes.add_dataclass_to_group(
            cls, group, help_dict=help_dict
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        return argumenttypes.extract_dataclass_from_namespace(cls, namespace)


class BattleRewards:
    def __init__(
            self,
            xp_tp_rewards: XPTPGRewards = XPTPGRewards(),
            drop_options: DropOptions = DropOptions(),
            charm_options: CharmOptions = CharmOptions(),
    ):
        self.xp_tp_rewards = xp_tp_rewards
        self.drop_options = drop_options
        self.charm_options = charm_options

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        XPTPGRewards.add_group_to_parser(parser)
        DropOptions.add_group_to_parser(parser)
        CharmOptions.add_group_to_parser(parser)

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        return cls(
            XPTPGRewards.extract_from_namespace(namespace),
            DropOptions.extract_from_namespace(namespace),
            CharmOptions.extract_from_namespace(namespace)
        )
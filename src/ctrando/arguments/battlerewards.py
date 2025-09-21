import argparse
import enum
import typing

from ctrando.arguments import argumenttypes
from dataclasses import dataclass, fields

from ctrando.arguments.argumenttypes import DiscreteNumericalArg


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

    _attr_names: typing.ClassVar[tuple[str, ...]] = (
        "drop_enemy_pool", "drop_reward_pool",
        "drop_rate", "mark_dropping_enemies"
    )
    _help_dict: typing.ClassVar[dict[str, str]] = {
        "drop_enemy_pool": "Pool of enemies which can have a dropped item",
        "drop_reward_pool": "Method of choosing enemy dropped items",
        "drop_rate": "Percentage (decimal) of enemies in the drop pool which have a dropped item",
        "mark_dropping_enemies": "Alter enemy names to indicate a dropped item"
    }
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
    def get_argument_spec(cls) -> dict[str, argumenttypes.Argument]:
        ret_dict: dict[str, argumenttypes.Argument] = {}

        attr_name = "drop_enemy_pool"
        ret_dict[attr_name] = argumenttypes.DiscreteCategorialArg(
            list(EnemyPoolType), EnemyPoolType.VANILLA,
            cls._help_dict[attr_name]
        )

        attr_name = "drop_reward_pool"
        ret_dict[attr_name] = argumenttypes.DiscreteCategorialArg(
            list(RewardPoolType), RewardPoolType.VANILLA,
            cls._help_dict[attr_name]
        )

        attr_name = "drop_rate"
        ret_dict[attr_name] = argumenttypes.DiscreteNumericalArg(
            0.0, 1.0, 0.01, 1.0,
            cls._help_dict[attr_name]
        )

        attr_name = "mark_dropping_enemies"
        ret_dict[attr_name] = argumenttypes.FlagArg(cls._help_dict[attr_name])

        return ret_dict

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
        for attr in cls._attr_names:
            if attr in namespace:
                init_dict[attr] = getattr(namespace, attr)

        return cls(**init_dict)


class CharmOptions:
    _default_charm_enemy_pool: typing.ClassVar[EnemyPoolType] = EnemyPoolType.VANILLA
    _default_charm_reward_pool: typing.ClassVar[RewardPoolType] = RewardPoolType.VANILLA
    _default_charm_rate: typing.ClassVar[float] = 0.05
    _default_mark_charmable_enemies: typing.ClassVar[bool] = False

    _attr_names: typing.ClassVar[tuple[str, ...]] = (
        "charm_enemy_pool", "charm_reward_pool",
        "charm_rate", "mark_charmable_enemies"
    )
    _help_dict: typing.ClassVar[dict[str, str]] = {
        "charm_enemy_pool": "Pool of enemies which can have a charmable item",
        "charm_reward_pool": "Method of choosing enemy charmable items",
        "charm_rate": "Percentage (decimal) of enemies in the charm pool which have a charmable item",
        "mark_charmable_enemies": "Alter enemy names to indicate a charmable item"
    }
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
    def get_argument_spec(cls) -> dict[str, argumenttypes.Argument]:
        ret_dict: dict[str, argumenttypes.Argument] = {}

        attr_name = "charm_enemy_pool"
        ret_dict[attr_name] = argumenttypes.DiscreteCategorialArg(
            list(EnemyPoolType), EnemyPoolType.VANILLA,
            cls._help_dict[attr_name]
        )

        attr_name = "charm_reward_pool"
        ret_dict[attr_name] = argumenttypes.DiscreteCategorialArg(
            list(RewardPoolType), RewardPoolType.VANILLA,
            cls._help_dict[attr_name]
        )

        attr_name = "charm_rate"
        ret_dict[attr_name] = argumenttypes.DiscreteNumericalArg(
            0.0, 1.0, 0.01, 1.0,
            cls._help_dict[attr_name]
        )

        attr_name = "mark_charmable_enemies"
        ret_dict[attr_name] = argumenttypes.FlagArg(cls._help_dict[attr_name])

        return ret_dict

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Enemy Charm Settings",
            description="Settings which modify enemy charms."
        )

        argumenttypes.add_str_enum_to_group(
            group, "--charm-enemy-pool", EnemyPoolType,
            help_str=cls._help_dict["charm_enemy_pool"]
        )

        argumenttypes.add_str_enum_to_group(
            group, "--charm-reward-pool", RewardPoolType,
            help_str=cls._help_dict["charm_reward_pool"]
        )

        group.add_argument(
            "--charm-rate",
            action="store", type=float,
            default=argparse.SUPPRESS,
            help=cls._help_dict["charm_rate"]
        )

        group.add_argument(
            "--mark-charmable-enemies",
            action="store_true",
            default=argparse.SUPPRESS,
            help=cls._help_dict["mark_charmable_enemies"]
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

    _help_dict: typing.ClassVar[dict[str, str]] = {
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
    _arg_names: typing.ClassVar[tuple[str, ...]] = (
        'xp_scale', 'tp_scale', 'g_scale', 'split_xp', 'split_tp',
        'fix_tp_doubling', "xp_penalty_level", "xp_penalty_percent",
        "level_cap"
    )

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Adds this as a group to the parser."""
        group = parser.add_argument_group(
            title="Battle Rewards Settings",
            description="Settings which modify post-battle rewards."
        )


        argumenttypes.add_dataclass_to_group(
            cls, group, help_dict=cls._help_dict
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        return argumenttypes.extract_dataclass_from_namespace(cls, namespace)

    @classmethod
    def get_arg_specs(cls) -> dict[str, argumenttypes.Argument]:

        ret_dict: dict[str, argumenttypes.Argument[typing.Any]] = {}

        for arg_name in ("xp_scale", "tp_scale", "g_scale"):
            ret_dict[arg_name] = argumenttypes.DiscreteNumericalArg(
                0.50, 10.00, 0.05, 3.0,
                cls._help_dict[arg_name]
            )

        for arg_name in ("split_tp", "fix_tp_doubling"):
            ret_dict[arg_name] = argumenttypes.FlagArg(cls._help_dict[arg_name])

        arg_name = "xp_penalty_level"
        ret_dict[arg_name] = argumenttypes.DiscreteNumericalArg(
            1, 99, 1, 40,
            cls._help_dict[arg_name]
        )

        arg_name = "xp_penalty_percent"
        ret_dict[arg_name] = argumenttypes.DiscreteNumericalArg(
            0, 100, 1, 15,
            cls._help_dict[arg_name]
        )

        arg_name = "level_cap"
        ret_dict[arg_name] = argumenttypes.DiscreteNumericalArg(
            1, 99, 1, 50,
            cls._help_dict[arg_name]
        )

        return ret_dict



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
    def get_arg_specs(cls) -> dict[str, argumenttypes.Argument]:
        ret_dict = XPTPGRewards.get_arg_specs()
        ret_dict.update(DropOptions.get_argument_spec())
        ret_dict.update(CharmOptions.get_argument_spec())

        return ret_dict

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
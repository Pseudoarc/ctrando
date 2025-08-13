"""Module for Gear Randomization Options"""
import argparse
from collections.abc import Iterable
import enum
import functools
import typing

from ctrando.arguments import argumenttypes as aty
from ctrando.common.ctenums import ItemID


class BronzeFistPolicy(enum.StrEnum):
    """Policies to Handle BronzeFist"""
    VANILLA = "vanilla"
    REMOVE = "remove"
    CRIT_4x = "4x_crit"
    RANDOM_OTHER = "random_other"


class DSItem(enum.Enum):
    """Possible DS Items from Gear Rando"""
    # Weapons
    DREAMSEEKER = enum.auto()
    # STARDUST_BOW = enum.auto()
    VENUS_BOW = enum.auto()
    TURBOSHOT = enum.auto()
    SPELLSLINGER = enum.auto()
    DRAGON_ARM = enum.auto()
    APOCALYPSE_ARM = enum.auto()
    DINOBLADE = enum.auto()
    JUDGEMENT_SCYTHE = enum.auto()
    DREAMREAPER = enum.auto()
    # Armors
    REPTITE_DRESS = enum.auto()
    DRAGON_ARMOR = enum.auto()
    REGAL_PLATE = enum.auto()
    REGAL_GOWN =  enum.auto()
    SHADOWPLUME_ROBE = enum.auto()
    ELEMENTAL_AEGIS = enum.auto()
    SAURIAN_LEATHERS = enum.auto()
    # Helmets
    DRAGONHEAD = enum.auto()
    REPTITE_TIARA = enum.auto()
    MASTERS_CROWN = enum.auto()
    ANGELS_TIARA = enum.auto()
    # Accessories
    VALOR_CREST = enum.auto()
    DRAGONS_TEAR = enum.auto()


def weapon_pool_verify(in_string: str) -> ItemID:
    """return stringified weapon name + verificaion"""
    item_id = aty.str_to_enum(in_string, ItemID)
    if not 0 < item_id < ItemID.WEAPON_END_5A:
        raise ValueError(f"{in_string} is not a weapon")

    return item_id


class GearRandoOptions:
    _default_weapon_rando_pool: typing.ClassVar[tuple[ItemID]] = (
        ItemID.RAINBOW, ItemID.SHIVA_EDGE, ItemID.SWALLOW, ItemID.RED_KATANA, ItemID.SLASHER,
        ItemID.VALKERYE, ItemID.SIREN, ItemID.SONICARROW,
        ItemID.WONDERSHOT, ItemID.SHOCK_WAVE, ItemID.PLASMA_GUN,
        ItemID.TERRA_ARM, ItemID.CRISIS_ARM,
        ItemID.MASAMUNE_1, ItemID.MASAMUNE_2, ItemID.BRAVESWORD, ItemID.RUNE_BLADE, ItemID.DEMON_HIT, ItemID.PEARL_EDGE,
        ItemID.IRON_FIST, ItemID.BRONZEFIST,
        ItemID.DOOMSICKLE
    )
    _default_ds_item_pool: typing.ClassVar[tuple[ItemID]] = tuple(DSItem)
    _default_ds_replacement_chance: int = 50
    _default_bronze_fist_policy: typing.ClassVar[BronzeFistPolicy] = BronzeFistPolicy.VANILLA

    _arg_names: typing.ClassVar[tuple[str, ...]] = (
        "ds_item_pool", "ds_replacement_chance", "weapon_rando_pool",
        "bronze_fist_policy"
    )

    def __init__(
            self,
            ds_item_pool: Iterable[DSItem] = _default_ds_item_pool,
            ds_replacement_chance: int = _default_ds_replacement_chance,
            weapon_rando_pool: Iterable[ItemID] = _default_weapon_rando_pool,
            bronze_fist_policy: BronzeFistPolicy = _default_bronze_fist_policy
    ):
        self.ds_item_pool: tuple[DSItem, ...] = tuple(ds_item_pool)
        self.ds_replacement_chance = ds_replacement_chance
        self.weapon_rando_pool = tuple(weapon_rando_pool)
        self.bronze_fist_policy = bronze_fist_policy
        # self.remove_9999 = remove_9999

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):

        group = parser.add_argument_group(
            "Gear Randomization Options",
            "Options for how the stats of weapons may be randomized"
        )

        group.add_argument(
            "--ds-item-pool",
            nargs="*",
            help="DS Items which may appear.",
            type=functools.partial(aty.str_to_enum, enum_type=DSItem),
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--ds-replacement-chance",
            action="store", type=int,
            help="Percent chance (e.g. 10 for 10 percent) to replace an item with a ds counterpart.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--weapon-rando-pool",
            nargs="*",
            help="Weapons whose effects should be shuffled",
            type=weapon_pool_verify,
            default=argparse.SUPPRESS
        )

        aty.add_str_enum_to_group(group, "--bronze-fist-policy",
                                  BronzeFistPolicy,
                                  help_str="How to modify BronzeFist pre-shuffle")

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        return aty.extract_from_namespace(cls, cls._arg_names, namespace)
"""Options which control treasure rewards"""

import argparse
from collections.abc import Iterable
import functools
import enum
import typing

from ctrando.arguments import argumenttypes
from ctrando.arguments.argumenttypes import str_to_enum, str_to_enum_dict
from ctrando.arguments import shopoptions
from ctrando.common.ctenums import ItemID, TreasureID as TID
from ctrando.treasures.treasuretypes import RewardType


class TreasurePool(enum.StrEnum):
    VANILLA = "vanilla"
    RANDOM = "random"
    RANDOM_TIERED = "random_tiered"


class TreasureScheme(enum.StrEnum):
    SHUFFLE = "shuffle"
    LOGIC_DEPTH = "logic_depth"


class TreasureOptions:
    _default_good_loot: typing.ClassVar[tuple[RewardType, ...]] = (
        ItemID.MEGAELIXIR, ItemID.HYPERETHER, ItemID.ELIXIR, ItemID.SPEED_TAB,
        ItemID.RAINBOW, ItemID.SHIVA_EDGE, ItemID.SWALLOW,
        ItemID.VALKERYE, ItemID.SIREN,
        ItemID.WONDERSHOT, ItemID.TABAN_SUIT,
        ItemID.CRISIS_ARM, ItemID.TERRA_ARM,
        ItemID.MASAMUNE_2,
        ItemID.BRONZEFIST,
        ItemID.DOOMSICKLE, ItemID.GLOOM_HELM, ItemID.GLOOM_CAPE,
        ItemID.PRISMSPECS, ItemID.PRISMDRESS, ItemID.PRISM_HELM,
        ItemID.SUN_SHADES, ItemID.VIGIL_HAT, ItemID.SAFE_HELM,
        ItemID.HASTE_HELM, ItemID.FLEA_VEST, ItemID.RBOW_HELM,
        ItemID.MERMAIDCAP, ItemID.DARK_HELM,
        ItemID.NOVA_ARMOR, ItemID.MOON_ARMOR, ItemID.ZODIACCAPE,
        ItemID.GOLD_STUD,
        ItemID.GOLD_ERNG,
        ItemID.BLUE_ROCK, ItemID.GOLD_ROCK, ItemID.BLACK_ROCK,
        ItemID.WHITE_ROCK, ItemID.SILVERROCK,
        ItemID.DRAGON_TEAR, ItemID.VALOR_CREST,
    )
    _default_good_loot_spots: typing.ClassVar[tuple[TID, ...]] = (
        TID.EOT_GASPAR_REWARD, TID.BEKKLER_KEY,
        TID.FAIR_PENDANT, TID.ZEAL_MAMMON_MACHINE, TID.MT_WOE_KEY,
        TID.GIANTS_CLAW_KEY, TID.KINGS_TRIAL_KEY, TID.YAKRAS_ROOM,
        TID.SNAIL_STOP_KEY, TID.DENADORO_MTS_KEY, TID.FROGS_BURROW_LEFT,
        TID.MELCHIOR_FORGE_MASA, TID.CYRUS_GRAVE_KEY, TID.TATA_REWARD,
        TID.FIONA_KEY, TID.SUN_KEEP_2300, TID.JERKY_GIFT, TID.ARRIS_DOME_DOAN_KEY,
        TID.ARRIS_DOME_FOOD_LOCKER_KEY, TID.REPTITE_LAIR_KEY, TID.TABAN_GIFT_VEST,
        TID.GENO_DOME_BOSS_1, TID.SUN_PALACE_KEY, TID.PRISON_TOWER_1000,
        TID.OZZIES_FORT_FINAL_2, TID.ZENAN_BRIDGE_CHEF, TID.ZENAN_BRIDGE_CAPTAIN,
        TID.LAZY_CARPENTER, TID.PYRAMID_LEFT, TID.MELCHIOR_SUNSTONE_SPECS,
        TID.MELCHIOR_SUNSTONE_RAINBOW,
        TID.MELCHIOR_RAINBOW_SHELL, TID.FACTORY_RUINS_GENERATOR,
        TID.DEATH_PEAK_SOUTH_FACE_SUMMIT, TID.KAJAR_ROCK, TID.LARUBA_ROCK,
        TID.LUCCA_WONDERSHOT, TID.HUNTING_RANGE_NU_REWARD, TID.ENHASA_NU_BATTLE_MAGIC_TAB,
        TID.SEWERS_3, TID.LAB_32_RACE_LOG, TID.DORINO_BROMIDE_MAGIC_TAB,
        TID.FACTORY_RIGHT_INFO_ARCHIVE,

        TID.HECKRAN_CAVE_SIDETRACK,
        TID.TABAN_SUNSHADES,
        TID.GENO_DOME_BOSS_2, TID.PYRAMID_RIGHT, TID.OZZIES_FORT_FINAL_1,
        TID.BLACK_OMEN_TERRA_ROCK, TID.GIANTS_CLAW_ROCK,
        TID.DENADORO_ROCK, TID.DENADORO_MTS_WATERFALL_TOP_1,
        TID.KAJAR_ROCK, TID.LARUBA_ROCK,
        TID.BLACK_OMEN_NU_HALL_W, TID.BLACK_OMEN_NU_HALL_E, TID.BLACK_OMEN_NU_HALL_NE,
        TID.BLACK_OMEN_NU_HALL_SE, TID.BLACK_OMEN_NU_HALL_SW, TID.BLACK_OMEN_NU_HALL_NW,
        TID.ARRIS_DOME_SEAL_1, TID.ARRIS_DOME_SEAL_2, TID.ARRIS_DOME_SEAL_3,
        TID.ARRIS_DOME_SEAL_4, TID.BANGOR_DOME_SEAL_1, TID.BANGOR_DOME_SEAL_2,
        TID.BANGOR_DOME_SEAL_3, TID.TRANN_DOME_SEAL_1, TID.TRANN_DOME_SEAL_2,
        TID.OZZIES_FORT_GUILLOTINES_2, TID.OZZIES_FORT_GUILLOTINES_3, TID.OZZIES_FORT_GUILLOTINES_4,
        TID.BLACKBIRD_DUCTS_MAGIC_TAB,
        TID.OCEAN_PALACE_SWITCH_SECRET,
        TID.CRONOS_MOM,
    )
    _default_good_loot_rate = 0.75
    _default_post_assign_shuffle_rate = 0.5
    _default_treasure_pool = TreasurePool.VANILLA
    _default_treasure_scheme = TreasureScheme.SHUFFLE

    def __init__(
            self,
            loot_assignment_scheme: TreasureScheme.SHUFFLE = _default_treasure_scheme,
            good_loot_spots: Iterable[TID] = _default_good_loot_spots,
            good_loot: Iterable[RewardType] = _default_good_loot,
            good_loot_rate: float = _default_good_loot_rate,
            loot_pool = _default_treasure_pool,
            post_assign_shuffle_rate = _default_post_assign_shuffle_rate
    ):
        self.loot_pool = loot_pool
        self.loot_assignment_scheme = loot_assignment_scheme
        self.good_loot_spots = tuple(set(good_loot_spots))
        self.good_loot = tuple(good_loot)
        self.good_loot_rate = good_loot_rate
        self.post_assign_shuffle_rate = post_assign_shuffle_rate

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        return {
            "loot_pool": argumenttypes.arg_from_enum(
                TreasurePool, cls._default_treasure_pool,
                "Method to determine which loot is available for assignment"
            ),
            "loot_assignment_scheme": argumenttypes.arg_from_enum(
                TreasureScheme, cls._default_treasure_scheme,
                "Method used to assign loot."
            ),
            "good_loot": argumenttypes.arg_multiple_from_enum(
                ItemID, cls._default_good_loot,
                "Loot that is considered to be good (ignored by vanilla)",
                available_pool=[
                    x for x in ItemID if x not in shopoptions.ShopOptions.unused_items
                ]
            ),
            "good_loot_spots": argumenttypes.arg_multiple_from_enum(
                TID, cls._default_good_loot_spots,
                "Spots which will be given a random good reward (ignored by vanilla)"
            ),
            "good_loot_rate": argumenttypes.DiscreteNumericalArg(
                0.0, 1.0, 0.05, cls._default_good_loot_rate,
                "Percent chance to fill a good loot spot with good loot",
                type_fn=float
            ),
            "post_assign_shuffle_rate": argumenttypes.DiscreteNumericalArg(
              0.0, 1.0, 0.1, cls._default_post_assign_shuffle_rate,
                "Percent chance to shuffle after basic assignment", type_fn=float
            )
        }

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Add these options to the parser."""
        group = parser.add_argument_group(
            "Treasure Options",
            "Options for how non-logical treasures are distributed"
        )

        group.add_argument(
            "--good-loot",
            nargs="*",
            type=functools.partial(str_to_enum, enum_type=ItemID),
            help="Item types considered as good loot.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--good-loot-spots",
            nargs="*",
            type=functools.partial(str_to_enum, enum_type=TID),
            help="Spots which will be given a random good reward.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--good-loot-rate",
            type=lambda val: float(sorted([0, float(val), 1.0])[1]),
            help="Proportion (between 0 and 1) of good loot spots which receive good loot.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--post-assign-shuffle-rate",
            type=lambda val: float(sorted([0, float(val), 1.0])[1]),
            help="Percent chance to shuffle after basic assignment",
            default=argparse.SUPPRESS
        )

        argumenttypes.add_str_enum_to_group(
            group, "--loot-pool", TreasurePool,
            help_str="Method to determine which loot is available for assignment",
        )

        argumenttypes.add_str_enum_to_group(
            group, "--loot-assignment-scheme", TreasureScheme,
            help_str="Method used to assign loot",
        )


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        attr_names = list(cls.get_argument_spec().keys())

        init_dict = {
            key: getattr(namespace, key)
            for key in attr_names if hasattr(namespace, key)
        }

        return TreasureOptions(**init_dict)

"""Module for storing boss rando options."""
import argparse
from collections.abc import Iterable
import enum
import functools
import typing

from ctrando.arguments import argumenttypes as aty
from ctrando.bosses import bosstypes


class BossRandoType(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE = "shuffle"
    RANDOM = "random"


class MidBossRandoType(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE = "shuffle"
    RANDOM = "random"


class BossRandoOptions:
    _default_rando_scheme: typing.ClassVar[BossRandoType] = BossRandoType.VANILLA
    _default_midboss_rando_scheme: typing.ClassVar[MidBossRandoType] = MidBossRandoType.VANILLA
    _default_vanilla_spots: typing.ClassVar[tuple[bosstypes.BossSpotID, ...]] = tuple()
    _default_boss_pool: typing.ClassVar[tuple[bosstypes.BossID, ...]] = (
        bosstypes.BossID.DALTON_PLUS, bosstypes.BossID.FLEA, bosstypes.BossID.FLEA_PLUS,
        bosstypes.BossID.GOLEM, bosstypes.BossID.GOLEM_BOSS, bosstypes.BossID.HECKRAN,
        bosstypes.BossID.MASA_MUNE, bosstypes.BossID.NIZBEL,
        bosstypes.BossID.NIZBEL_2, bosstypes.BossID.RUST_TYRANO, bosstypes.BossID.SLASH_SWORD,
        bosstypes.BossID.SUPER_SLASH, bosstypes.BossID.YAKRA, bosstypes.BossID.YAKRA_XIII,
        bosstypes.BossID.ZOMBOR, bosstypes.BossID.LAVOS_SPAWN, bosstypes.BossID.ELDER_SPAWN,
        bosstypes.BossID.MEGA_MUTANT, bosstypes.BossID.GIGA_MUTANT, bosstypes.BossID.TERRA_MUTANT,
        bosstypes.BossID.RETINITE, bosstypes.BossID.SON_OF_SUN, bosstypes.BossID.MOTHER_BRAIN,
        bosstypes.BossID.GUARDIAN, bosstypes.BossID.GIGA_GAIA, bosstypes.BossID.MUD_IMP, bosstypes.BossID.R_SERIES,
        bosstypes.BossID.DRAGON_TANK, bosstypes.BossID.ZEAL, bosstypes.BossID.MAGUS_NORTH_CAPE,
    )
    _default_midboss_pool: typing.ClassVar[tuple[bosstypes.BossID, ...]] = (
        bosstypes.BossID.GATO, bosstypes.BossID.DALTON,
        bosstypes.BossID.KRAWLIE, bosstypes.BossID.SUPER_SLASH,
        bosstypes.BossID.FLEA_PLUS, bosstypes.BossID.ATROPOS_XR,
    )


    _arg_names: typing.ClassVar[tuple[str, ...]] = (
        "boss_randomization_type",
        "midboss_randomization_type",
        "vanilla_boss_spots",
        "boss_pool", "midboss_pool"
    )
    _help_dict: typing.ClassVar[dict[str, str]] = {
        "boss_randomization_type": "How bosses should be assigned to spots",
        "midboss_randomization_type": "How midbosses should be assigned to spots",
        "vanilla_boss_spots": "Spots which should always have their vanilla boss (or midboss)",
        "boss_pool": "Bosses to include in assignment (only when boss type is \"random\")",
        "midboss_pool": "Midbosses to include in assignment (only when midboss randomization type is \"random\")",
    }
    _spec_dict: typing.ClassVar[aty.ArgSpec] = {
        "boss_randomization_type": aty.arg_from_enum(
            BossRandoType, _default_rando_scheme,"How bosses should be assigned to spots"
        ),
        "midboss_randomization_type": aty.arg_from_enum(
            BossRandoType, _default_midboss_rando_scheme,"How midbosses should be assigned to spots"
        ),
        "vanilla_boss_spots": aty.arg_multiple_from_enum(
            bosstypes.BossSpotID, _default_vanilla_spots,
            "Spots which should always have their vanilla boss (or midboss)"
        ),
        "boss_pool": aty.arg_multiple_from_enum(
            bosstypes.BossID, _default_boss_pool,
            "Bosses to include in assignment (only when boss type is \"random\")",
            force_enum_names=True,
            available_pool=list(_default_boss_pool)
        ),
        "midboss_pool": aty.arg_multiple_from_enum(
            bosstypes.BossID, _default_midboss_pool,
            "Midbosses to include in assignment (only when boss type is \"random\")",
            force_enum_names=True,
            available_pool=list(_default_midboss_pool)
        ),
    }
    def __init__(
            self,
            boss_randomization_type: BossRandoType = _default_rando_scheme,
            midboss_randomization_type: MidBossRandoType = _default_midboss_rando_scheme,
            vanilla_boss_spots: Iterable[bosstypes.BossSpotID] = _default_vanilla_spots,
            boss_pool: Iterable[bosstypes.BossID] = _default_boss_pool,
            midboss_pool: Iterable[bosstypes.BossID] = _default_midboss_pool
    ):
        self.midboss_randomization_type = midboss_randomization_type
        self.boss_randomization_type = boss_randomization_type
        self.vanilla_boss_spots = tuple(vanilla_boss_spots)
        self.boss_pool = tuple(boss_pool)
        self.midboss_pool = tuple(midboss_pool)

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        return cls._spec_dict

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Boss Rando Options",
            "Options for how bosses are assigned to locations."
        )

        aty.add_str_enum_to_group(
            group, "--boss-randomization-type", BossRandoType,
        )

        aty.add_str_enum_to_group(
            group, "--midboss-randomization-type", MidBossRandoType
        )

        group.add_argument(
            "--vanilla-boss-spots",
            nargs="+",
            type=functools.partial(aty.str_to_enum, enum_type=bosstypes.BossSpotID,
                                   force_enum_names=True),
            help="Spots which must keep their vanilla boss (also midboss).",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--boss-pool",
            nargs="+",
            type=functools.partial(aty.str_to_enum, enum_type=bosstypes.BossID,
                                   force_enum_names=True),
            help="Bosses to include in assignment (only when --boss-rando-scheme=\"random\")",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--midboss-pool",
            nargs="+",
            type=functools.partial(aty.str_to_enum, enum_type=bosstypes.BossID,
                                   force_enum_names=True),
            help="Midbosses to include in assignment (only when --midboss-rando-scheme=\"random\")",
            default=argparse.SUPPRESS
        )

    @classmethod
    def extract_from_namespace(
            cls,
            namespace: argparse.Namespace
    ) -> typing.Self:
        attr_names = [
            "boss_randomization_type", "midboss_randomization_type",
            "vanilla_boss_spots", "boss_pool", "midboss_pool"
        ]

        return aty.extract_from_namespace(cls, arg_names=attr_names, namespace=namespace)
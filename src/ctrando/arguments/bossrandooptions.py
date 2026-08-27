"""Module for storing boss rando options."""
import argparse
from collections.abc import Iterable, Sequence
import enum
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
    _default_lavos_gauntlet_bosses = (
        bosstypes.BossID.DRAGON_TANK, bosstypes.BossID.GUARDIAN,
        bosstypes.BossID.HECKRAN, bosstypes.BossID.ZOMBOR,
        bosstypes.BossID.MASA_MUNE, bosstypes.BossID.NIZBEL,
        bosstypes.BossID.MAGUS, bosstypes.BossID.BLACK_TYRANO,
        bosstypes.BossID.GIGA_GAIA
    )
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
        "lavos_gauntlet_bosses": aty.arg_multiple_from_enum(
            bosstypes.BossID, _default_lavos_gauntlet_bosses,
            "Bosses to fight in the Lavos gauntlet (max 9)",
            available_pool=_default_boss_pool + (bosstypes.BossID.ZEAL_2, bosstypes.BossID.MAMMON_M),
        ),
        "lavos_gauntlet_rewards": aty.FlagArg(
            "Lavos Gauntlet bosses have the same rewards as the base bosses."
        )
    }
    def __init__(
            self,
            boss_randomization_type: BossRandoType = _default_rando_scheme,
            midboss_randomization_type: MidBossRandoType = _default_midboss_rando_scheme,
            vanilla_boss_spots: Iterable[bosstypes.BossSpotID] = _default_vanilla_spots,
            boss_pool: Iterable[bosstypes.BossID] = _default_boss_pool,
            midboss_pool: Iterable[bosstypes.BossID] = _default_midboss_pool,
            lavos_gauntlet_bosses: Sequence[bosstypes.BossID] = _default_lavos_gauntlet_bosses,
            lavos_gauntlet_rewards: bool = False
    ):
        self.midboss_randomization_type = midboss_randomization_type
        self.boss_randomization_type = boss_randomization_type
        self.vanilla_boss_spots = tuple(vanilla_boss_spots)
        self.boss_pool = tuple(boss_pool)
        self.midboss_pool = tuple(midboss_pool)
        self.lavos_gauntlet_bosses = lavos_gauntlet_bosses
        self.lavos_gauntlet_rewards = lavos_gauntlet_rewards

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        return cls._spec_dict

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Boss Rando Options",
            "Options for how bosses are assigned to locations."
        )

        for attr_name, argument in cls.get_argument_spec().items():
            arg_name = aty.attr_name_to_arg_name(attr_name)
            argument.add_to_argparse(arg_name, group)

    @classmethod
    def extract_from_namespace(
            cls,
            namespace: argparse.Namespace
    ) -> typing.Self:
        attr_names = list(cls.get_argument_spec().keys())
        return aty.extract_from_namespace(cls, arg_names=attr_names, namespace=namespace)
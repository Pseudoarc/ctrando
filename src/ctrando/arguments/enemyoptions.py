from __future__ import annotations
import argparse
import typing

from ctrando.arguments import argumenttypes
from ctrando.bosses import bosstypes as bty

class BossScalingOptions:
    """Special Scaling for bosses"""

    _default_levels: typing.ClassVar[dict[bty.BossID, int]] = {
        bty.BossID.DALTON: 26,  # default=32
        bty.BossID.DALTON_PLUS: 17,  # default=20
        bty.BossID.ELDER_SPAWN: 47,  # default=46
        bty.BossID.FLEA: 17,  # default=21
        bty.BossID.GIGA_MUTANT: 48,  # default=47
        bty.BossID.GOLEM: 27,  # default=34
        bty.BossID.GOLEM_BOSS: 34,  # default=34
        bty.BossID.HECKRAN: 12,  # default=13
        bty.BossID.LAVOS_SPAWN: 37,  # default=37
        bty.BossID.MAMMON_M: 44,  # default=48
        bty.BossID.MAGUS_NORTH_CAPE: 37,  # default=37
        bty.BossID.MASA_MUNE: 15,  # default=16
        bty.BossID.MEGA_MUTANT: 46,  # default=45
        bty.BossID.MUD_IMP: 29,  # default=26
        bty.BossID.NIZBEL: 16,  # default=18
        bty.BossID.NIZBEL_2: 21,  # default=27
        bty.BossID.RETINITE: 30,  # default=30
        bty.BossID.R_SERIES: 7,  # default=10
        bty.BossID.RUST_TYRANO: 35,  # default=35
        bty.BossID.SLASH_SWORD: 19,  # default=22
        bty.BossID.SON_OF_SUN: 41,  # default=40
        bty.BossID.TERRA_MUTANT: 50,  # default=49
        bty.BossID.YAKRA: 4,  # default=6
        bty.BossID.YAKRA_XIII: 39,  # default=45
        bty.BossID.ZOMBOR: 9,  # default=13
        # DON'T CHANGE THIS LOLmother_brain_level=1 #default=23
        bty.BossID.DRAGON_TANK: 5,  # default=7
        bty.BossID.GIGA_GAIA: 30,  # default=32
        bty.BossID.GUARDIAN: 6,  # default=8
        bty.BossID.MAGUS: 20,  # default=20
        bty.BossID.BLACK_TYRANO: 20,  # default=20
        bty.BossID.OZZIE_TRIO: 33,  # default=38
        bty.BossID.ATROPOS_XR: 33,  # default=38
        bty.BossID.FLEA_PLUS: 27,  # default=35
        bty.BossID.SUPER_SLASH: 27,  # default=35
        bty.BossID.KRAWLIE: 6,  # default=8
        bty.BossID.GATO: 0,  # default=1
        bty.BossID.ZEAL_2: 42
    }

    def __init__(self, boss_powers: dict[bty.BossID, int | None] = None):
        if boss_powers is None:
            boss_powers = {}
        self.boss_level_dict: dict[bty.BossID, int | None] = {}
        self.boss_level_dict.update(boss_powers)

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict: argumenttypes.ArgSpec = {}

        for boss_id, default in cls._default_levels.items():
            boss_name = f"{boss_id.value.lower()}"
            ret_dict[f"{boss_name}_level"] = argumenttypes.DiscreteNumericalArg(
                0, 99, 1, default,
                f"The internal level of {boss_id} [Experimental]",
                type_fn=int
            )

        return ret_dict

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):

        group = parser.add_argument_group(
            "Boss Level Settings",
            "Adjust internal level of bosses (lower = harder)"
        )
        for boss_id in bty.BossID:
            boss_name = f"{boss_id.lower().replace("_", "-")}"
            group.add_argument(
                f"--{boss_name}-level",
                action="store", type=int,
                help=f"The internal level of {boss_id}",
                default=argparse.SUPPRESS
            )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        boss_level_dict: dict[bty.BossID, int | None] = {}
        for boss_id in bty.BossID:
            arg_name = f"{boss_id.lower()}_level"
            if hasattr(namespace, arg_name):
                boss_level_dict[boss_id] = getattr(namespace, arg_name)

        return BossScalingOptions(boss_level_dict)


class EnemyOptions:
    """Class for storing options for enemies."""
    _default_sightscope_all = False
    _default_forced_sightscope = False
    _default_shuffle_enemies = False

    def __init__(
            self,
            sightscope_all: bool = _default_sightscope_all,
            forced_sightscope: bool = _default_forced_sightscope,
            shuffle_enemies: bool = _default_shuffle_enemies
    ):
        self.sightscope_all = sightscope_all
        self.forced_sightscope = forced_sightscope
        self.shuffle_enemies = shuffle_enemies

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        return {
            "sightscope_all": argumenttypes.FlagArg("Enable sightscope usage on all enemies."),
            "forced_sightscope": argumenttypes.FlagArg("Sightscope effect will be present without the item equipped."),
            "shuffle_enemies": argumenttypes.FlagArg("Normal enemy types are shuffled (respects enemy size)")
        }

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Add Tech Settings to parser."""
        group = parser.add_argument_group(
            "Enemy Options",
            "Options relating to Enemies"
        )

        group.add_argument(
            "--sightscope-all",
            action="store_true",
            help="Enable sightscope usage on all enemies.",
            default=argparse.SUPPRESS
        )
        group.add_argument(
            "--forced-sightscope",
            action="store_true",
            help="Sightscope effect will be present without the item equipped.",
            default=argparse.SUPPRESS
        )
        group.add_argument(
            "--shuffle-enemies",
            action="store_true",
            help="Normal enemy types are shuffled (respects enemy size)",
            default=argparse.SUPPRESS
        )

    @classmethod
    def extract_from_namespace(
            cls, namespace: argparse.Namespace
    ) -> typing.Self:
        attr_names = ["sightscope_all", "forced_sightscope", "shuffle_enemies"]

        return argumenttypes.extract_from_namespace(
            cls,
            arg_names=attr_names,
            namespace=namespace
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"sightscope_all={self.sightscope_all}, "
            f"forced_sightscope={self.forced_sightscope}, "
            f"shuffle_enemies={self.shuffle_enemies}"
        )





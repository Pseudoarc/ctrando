from __future__ import annotations
import argparse
import typing

from ctrando.arguments import argumenttypes
from ctrando.bosses import bosstypes as bty

class BossScalingOptions:
    """Special Scaling for bosses"""

    def __init__(self, boss_powers: dict[bty.BossID, int | None] = None):
        if boss_powers is None:
            boss_powers = {}
        self.boss_level_dict: dict[bty.BossID, int | None] = {}
        self.boss_level_dict.update(boss_powers)

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





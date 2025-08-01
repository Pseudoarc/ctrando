from __future__ import annotations
import argparse
import typing

from ctrando.arguments import argumenttypes


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





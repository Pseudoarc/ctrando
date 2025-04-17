"""Commandline for CTRando"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import enum
import random
import typing

from pathlib import Path

from ctrando.arguments import (
    argumenttypes,
    battlerewards,
    techoptions,
    enemyscaling,
    logicoptions,
    bossrandooptions,
    shopoptions,
    objectiveoptions,
    entranceoptions,
    recruitoptions,
    treasureoptions,
    enemyoptions
)


class KeyListType(enum.StrEnum):
    TREASURE_SPOTS = "spots"
    ITEMS = "items"
    BOSS_SPOTS = "boss_spots"
    BOSSES = "bosses"


@dataclass
class GeneralOptions:
    input_file: typing.Optional[Path] = None
    output_directory: typing.Optional[Path] = None
    seed: typing.Optional[str] = None
    options_file: typing.Optional[Path] = None
    list_keys: typing.Optional[KeyListType] = None

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        general_group = parser.add_argument_group(
            "General Options",
            "Generation options not related to gameplay"
        )
        general_group.add_argument(
            "-i", "--input-file",
            action="store", type=Path,
            help="Path of vanilla Chrono Trigger (USA) rom",
            default=argparse.SUPPRESS
        )

        general_group.add_argument(
            "-o", "--output-directory",
            action="store", type=Path, required=False,
            help="Directory to store output (randomized) rom",
            default=argparse.SUPPRESS
        )

        general_group.add_argument(
            "--seed",
            help="Seed to provide random number generator.",
            default=argparse.SUPPRESS
        )

        general_group.add_argument(
            "--options-file",
            type=Path,
            default=argparse.SUPPRESS,
            help=("File with additional settings.  Will be overiddedn by "
                  "arguments on the commandline.")
        )

        argumenttypes.add_str_enum_to_group(
            general_group, "--list-keys",
            KeyListType,
            help_str=("Do not generate a randomized ROM. "
                      "Only disiplay a list of valid keys of a given type."
                      "Valid types: spots, items, bosses, boss_spots.")
        )


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:

        input_file: typing.Optional[Path] = None
        output_directory: typing.Optional[Path] = None
        if hasattr(namespace, "input_file"):
            input_file = getattr(namespace, "input_file")
            if not input_file.is_file() and input_file.exists():
                raise ValueError("Input file does not exist")

            output_directory: Path = getattr(namespace, "output_directory")
            if output_directory is None:
                output_directory = input_file.parent


        if not hasattr(namespace, "seed"):
            seed = "".join(random.choices("0123456789ABCDEF", k=16))
        else:
            seed = getattr(namespace, "seed")

        if hasattr(namespace, "options_file"):
            options_file = getattr(namespace, "options_file")
        else:
            options_file = None

        if hasattr(namespace, "list_keys"):
            list_keys = getattr(namespace, "list_keys")
        else:
            list_keys = None

        return cls(
            input_file=input_file,
            output_directory=output_directory,
            seed=seed,
            options_file=options_file,
            list_keys=list_keys
        )



class Settings:
    def __init__(
            self,
            general_options: GeneralOptions = GeneralOptions(Path("./ct.sfc"), Path("./")),
            battle_rewards: battlerewards.BattleRewards = battlerewards.BattleRewards(),
            tech_options: techoptions.TechOptions = techoptions.TechOptions(),
            scaling_options: enemyscaling.ScalingOptions = enemyscaling.ScalingOptions(),
            logic_options: logicoptions.LogicOptions = logicoptions.LogicOptions(),
            boss_rando_options: bossrandooptions = bossrandooptions.BossRandoOptions(),
            shop_options: shopoptions.ShopOptions = shopoptions.ShopOptions(),
            objective_options: objectiveoptions.ObjectiveOptions = objectiveoptions.ObjectiveOptions(),
            entrance_options: entranceoptions.EntranceShufflerOptions = entranceoptions.EntranceShufflerOptions(),
            recruit_options: recruitoptions.RecruitOptions =recruitoptions.RecruitOptions(),
            treasure_options: treasureoptions.TreasureOptions = treasureoptions.TreasureOptions(),
            enemy_options: enemyoptions.EnemyOptions = enemyoptions.EnemyOptions()
    ):
        self.general_options = general_options
        self.battle_rewards = battle_rewards
        self.tech_options = tech_options
        self.scaling_options = scaling_options
        self.logic_options = logic_options
        self.boss_rando_options = boss_rando_options
        self.shop_options = shop_options
        self.objective_options = objective_options
        self.entrance_options = entrance_options
        self.recruit_options = recruit_options
        self.treasure_options = treasure_options
        self.enemy_options = enemy_options

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        return cls(
            general_options=GeneralOptions.extract_from_namespace(namespace),
            battle_rewards=battlerewards.BattleRewards.extract_from_namespace(namespace),
            tech_options=techoptions.TechOptions.extract_from_namespace(namespace),
            scaling_options=enemyscaling.ScalingOptions.extract_from_namespace(namespace),
            logic_options=logicoptions.LogicOptions.extract_from_namespace(namespace),
            boss_rando_options=bossrandooptions.BossRandoOptions.extract_from_namespace(namespace),
            shop_options=shopoptions.ShopOptions.extract_from_namespace(namespace),
            objective_options=objectiveoptions.ObjectiveOptions.extract_from_namespace(namespace),
            entrance_options=entranceoptions.EntranceShufflerOptions.extract_from_namespace(namespace),
            recruit_options=recruitoptions.RecruitOptions.extract_from_namespace(namespace),
            treasure_options=treasureoptions.TreasureOptions.extract_from_namespace(namespace),
            enemy_options=enemyoptions.EnemyOptions.extract_from_namespace(namespace)
        )


def get_parser() -> argparse.ArgumentParser:
    """Returns the argument parser."""

    parser = argparse.ArgumentParser()

    GeneralOptions.add_group_to_parser(parser)
    battlerewards.BattleRewards.add_group_to_parser(parser)
    techoptions.TechOptions.add_group_to_parser(parser)
    enemyscaling.ScalingOptions.add_group_to_parser(parser)
    logicoptions.LogicOptions.add_group_to_parser(parser)
    bossrandooptions.BossRandoOptions.add_group_to_parser(parser)
    shopoptions.ShopOptions.add_group_to_parser(parser)
    objectiveoptions.ObjectiveOptions.add_group_to_parser(parser)
    entranceoptions.EntranceShufflerOptions.add_group_to_parser(parser)
    recruitoptions.RecruitOptions.add_group_to_parser(parser)
    treasureoptions.TreasureOptions.add_group_to_parser(parser)
    enemyoptions.EnemyOptions.add_group_to_parser(parser)

    return parser

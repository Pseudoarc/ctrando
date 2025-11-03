# Doing this will make dataclass types store as strings instead of actual types
# from __future__ import annotations

import argparse
import typing
from dataclasses import dataclass
import enum


from ctrando.arguments import argumenttypes


class DynamicScalingScheme(enum.StrEnum):
    NONE = "none"
    PROGRESSION = "progression"
    LOGIC_DEPTH = "logic_depth"


@dataclass
class DynamicScalingOptions:
    max_scaling_level: int = 50
    dynamic_scale_lavos: bool = False
    defense_safety_min_level: int = 10
    defense_safety_max_level: int = 30
    obstacle_safety_level: int = 30


    def __post_init__(self):
        if self.max_scaling_level < 0:
            raise ValueError

        if self.defense_safety_min_level < 0:
            raise ValueError

        if self.obstacle_safety_level < 0:
            raise ValueError

        if self.defense_safety_max_level < self.defense_safety_min_level:
            raise ValueError

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        return {
            "max_scaling_level": argumenttypes.DiscreteNumericalArg(
                1, 99, 1, 50,
                "Maximum level to scale to (if not none)",
                type_fn=int
            ),
            "dynamic_scale_lavos": argumenttypes.FlagArg(
                "Include Lavos in the dynamic scaling (if not none)"),
            "defense_safety_min_level": argumenttypes.DiscreteNumericalArg(
                1, 99, 1, 10,
                "Level before which enemies have standard phys defense",
                type_fn=int
            ),
            "defense_safety_max_level": argumenttypes.DiscreteNumericalArg(
                1, 99, 1, 10,
                "Level after which enemies have their normal phys defense",
                type_fn=int
            ),
            "obstacle_safety_level": argumenttypes.DiscreteNumericalArg(
                1, 99, 1, 10,
                "Level before which Obstacle is single target",
                type_fn=int
            ),
        }

@dataclass()
class LogicDepthScalingData:
    ...


@dataclass
class ProgressionScalingData:
    levels_per_boss: float = 2.0
    levels_per_quest: float = 2.0
    levels_per_key_item: float = 0.0
    levels_per_objective: float = 3.0
    levels_per_character: float = 1.0

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        return {
            "levels_per_boss": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.25, 2.0,
                "Scaling levels gained per boss defeated",
                type_fn=float
            ),
            "levels_per_quest": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.25, 2.0,
                "Scaling levels gained per quest completed",
                type_fn=float
            ),
            "levels_per_key_item": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.25, 0.0,
                "Scaling levels gained per key item obtained",
                type_fn=float
            ),
            "levels_per_objective": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.25, 2.0,
                "Scaling levels gained per objective completed",
                type_fn=float
            ),
            "levels_per_character": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.25, 2.0,
                "Scaling levels gained per character recruited",
                type_fn=float
            ),
        }

    def __post_init__(self):
        if self.levels_per_boss < 0:
            raise ValueError

        if self.levels_per_quest < 0:
            raise ValueError

        if self.levels_per_key_item < 0:
            raise ValueError

        if self.levels_per_objective < 0:
            raise ValueError

        if self.levels_per_character < 0:
            raise ValueError


@dataclass
class StaticScalingOptions:
    normal_enemy_hp_scale: float = 1.0
    static_boss_hp_scale: float = 0.75
    static_hp_scale_lavos: bool = False
    element_safety_level: int = 30

    @classmethod
    def get_argument_spec(cls):
        return {
            "normal_enemy_hp_scale": argumenttypes.DiscreteNumericalArg(
                0.05, 2.0, 0.05, 1.0,
                "Multiply non-boss enemy hp by this factor",
                type_fn=float
            ),
            "static_boss_hp_scale": argumenttypes.DiscreteNumericalArg(
                0.05, 2.0, 0.05, 0.75,
                "Multiply boss hp by this factor",
                type_fn=float
            ),
            "static_hp_scale_lavos": argumenttypes.FlagArg("Apply static hp scaling to lavos"),
            "element_safety_level": argumenttypes.DiscreteNumericalArg(
                1, 99, 1, 30,
                "Before this level any magic hits Nizbel/Retinite weakness",
                type_fn=int
            )
        }

    def __post_init__(self):
        if self.static_boss_hp_scale <= 0:
            raise ValueError


DyanamicScaleSchemeOptions = typing.Union[typing.Type[ProgressionScalingData], None]

class ScalingOptions:
    """Class for all scaling options."""
    _option_type_dict: dict[DynamicScalingScheme, DyanamicScaleSchemeOptions] = {
        DynamicScalingScheme.NONE: None,
        DynamicScalingScheme.PROGRESSION: ProgressionScalingData,
        DynamicScalingScheme.LOGIC_DEPTH: None
    }

    _arg_dict: argumenttypes.ArgSpec = {
        "dynamic_scaling_scheme": argumenttypes.DiscreteCategorialArg(
            list(DynamicScalingScheme), DynamicScalingScheme.PROGRESSION,
            "Method for dynamically scaling enemies"
        ),
    }

    def __init__(
            self,
            dynamic_scaling_scheme: DynamicScalingScheme = DynamicScalingScheme.PROGRESSION,
            dynamic_scaling_scheme_options: DyanamicScaleSchemeOptions = ProgressionScalingData(),
            dynamic_scaling_general_options: DynamicScalingOptions = DynamicScalingOptions(),
            static_scaling_options: StaticScalingOptions = StaticScalingOptions()
    ):
        """All scaling options"""
        self.dynamic_scaling_scheme = dynamic_scaling_scheme
        self.dynamic_scaling_scheme_options = dynamic_scaling_scheme_options
        self.dynamic_scaling_general_options = dynamic_scaling_general_options
        self.static_scaling_options = static_scaling_options

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict = dict(cls._arg_dict)
        ret_dict["dynamic_scaling_scheme_options"] = ProgressionScalingData.get_argument_spec()
        ret_dict["dynamic_scaling_general_options"] = DynamicScalingOptions.get_argument_spec()
        ret_dict["static_scaling_options"] = StaticScalingOptions.get_argument_spec()

        return ret_dict

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):

        dyn_general_group = parser.add_argument_group(
            "Dynamic Scaling General Options",
            "Options which control how enemies scale as the game progresses"
        )

        argumenttypes.add_str_enum_to_group(
            dyn_general_group, "--dynamic-scaling-scheme",
            DynamicScalingScheme,
            default_value=argparse.SUPPRESS,
            help_str="Scheme by which enemies are dynamically scaled"
        )
        help_dict: dict[str, str] = {
            "max_scaling_level": "Maximum level to scale to (if not none)",
            "dynamic_scale_lavos": "Include Lavos in the dynamic scaling (if not none)"
        }
        argumenttypes.add_dataclass_to_group(
            DynamicScalingOptions,
            dyn_general_group,
            help_dict=help_dict
        )

        help_dict: dict[str, str] = {
            "static_boss_hp_scale": "Factor by which to scale all boss HP",
            "element_safety_level": "Level before which bosses will be weak to any element",
            "obstacle_safety_level": "Level before which obstacle will be single target"
        }
        argumenttypes.add_dataclass_to_group(
            StaticScalingOptions,
            dyn_general_group,
            help_dict=help_dict,
        )

        for name, datatype in cls._option_type_dict.items():
            if datatype is not None:
                group = parser.add_argument_group(
                    f"Options for dynamic scaling scheme \"{name}\""
                )
                argumenttypes.add_dataclass_to_group(datatype, group)

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        scale_opts = ScalingOptions()

        scheme = argumenttypes.extract_enum_from_namespace(
            DynamicScalingScheme, "dynamic_scaling_scheme", namespace
        )
        if scheme is not None:
            scale_opts.dynamic_scaling_scheme = scheme
        else:
            scheme = DynamicScalingScheme.NONE

        scheme_settings_type = cls._option_type_dict[scheme]
        if scheme_settings_type is not None:
            scale_opts.dynamic_scaling_scheme_options = \
                argumenttypes.extract_dataclass_from_namespace(scheme_settings_type, namespace)

        scale_opts.dynamic_scaling_general_options = \
            argumenttypes.extract_dataclass_from_namespace(DynamicScalingOptions, namespace)

        scale_opts.static_scaling_options = \
            argumenttypes.extract_dataclass_from_namespace(StaticScalingOptions, namespace)

        return scale_opts


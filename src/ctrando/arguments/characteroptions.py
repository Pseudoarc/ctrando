"""Options for Modifying Character Attributes"""
import argparse
import enum
from dataclasses import dataclass, field
import typing

from ctrando.arguments import argumenttypes as aty


class TechRandoScheme(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE_ELEMENT = "shuffle_element"
    RANDOM_ELEMENT = "random_element"
    CHAOS_ELEMENT = "chaos_element"


@dataclass()
class CharacterOptions:
    use_phys_marle: bool = False
    use_haste_all: bool = False
    use_phys_lucca: bool = False
    use_protect_all: bool = False
    use_reraise: bool = False
    use_magus_dual_techs: bool = False
    use_daltonized_magus: bool = False
    tech_rando_scheme:  TechRandoScheme = TechRandoScheme.VANILLA
    mdef_growth_scale_factor: float = 1.0
    mdef_cap: int = 99
    mdef_levelup_cap: int = 99

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        return {
            "use_phys_marle": aty.FlagArg("+Hit, Physical arrow tech"),
            "use_haste_all": aty.FlagArg("AoE Haste, 15 MP cost"),
            "use_phys_lucca": aty.FlagArg("+Hit. Physical Flame Toss + Bombs"),
            "use_protect_all": aty.FlagArg("AoE Protect, 2x MP cost"),
            "use_reraise": aty.FlagArg("Life2 gives greendream effect"),
            "use_magus_dual_techs": aty.FlagArg("Magus can perform dual techs with fire/ice/lit2"),
            "use_daltonized_magus": aty.FlagArg("Magus shadow techs are replaced with Dalton versions"),
            "tech_rando_scheme": aty.arg_from_enum(
                TechRandoScheme, TechRandoScheme.VANILLA,
                "Scheme to randomize single techs",
                False
            ),
            "mdef_growth_scale_factor": aty.DiscreteNumericalArg(
                0.5, 1.5, 0.01, 1.0,
                "Scale all magic defense gains by this factor", float
            ),
            "mdef_cap": aty.DiscreteNumericalArg(
                1, 99, 1, 99,
                "The maximum possible magic defense (stats + equip)", int
            ),
            "mdef_levelup_cap": aty.DiscreteNumericalArg(
                1, 99, 1, 99,
                "The maximum possible magic defense gained through leveling",
                int
            )
        }

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Character Options",
            "Options which alter character stats and abilities"
        )

        for name, arg in cls.get_argument_spec().items():
            arg.add_to_argparse(aty.attr_name_to_arg_name(name), group)


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ret = aty.extract_from_namespace(cls, list(cls.get_argument_spec().keys()), namespace)
        return ret

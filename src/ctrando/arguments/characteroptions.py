"""Options for Modifying Character Attributes"""
import argparse
import enum
from dataclasses import dataclass, field
import typing

from ctrando.arguments import argumenttypes as aty
from ctrando.common import random, ctenums


class TechRandoScheme(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE_ELEMENT = "shuffle_element"
    RANDOM_ELEMENT = "random_element"
    CHAOS_ELEMENT = "chaos_element"


class CharacterIdentityRandoScheme(enum.StrEnum):
    VANILLA = "vanilla"
    RANDOM = "random"
    SHUFFLE = "shuffle"


@dataclass()
class CharacterOptions:
    use_phys_marle: bool = False
    use_haste_all: bool = False
    use_phys_lucca: bool = False
    use_protect_all: bool = False
    use_reraise: bool = False
    use_magus_dual_techs: bool = False
    use_daltonized_magus: int = 0
    tech_rando_scheme:  TechRandoScheme = TechRandoScheme.VANILLA
    mdef_growth_scale_factor: float = 1.0
    mdef_cap: int = 99
    mdef_levelup_cap: int = 99
    character_identity_randomization: CharacterIdentityRandoScheme = CharacterIdentityRandoScheme.VANILLA
    character_reassign_keep_stats: int = 0
    crono_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    marle_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    lucca_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    robo_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    frog_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    ayla_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)
    magus_identity_choices: tuple[ctenums.CharID, ...] = tuple(ctenums.CharID)

    def __post_init__(self):
        for char_id in ctenums.CharID:
            attr_name = f"{str(char_id).lower()}_identity_choices"
            attr = getattr(self, attr_name)
            if not attr:
                raise ValueError(f"{attr_name} can not be empty")

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        spec = {
            "use_phys_marle": aty.RandomFlagArg("+Hit, Physical arrow tech"),
            "use_haste_all": aty.RandomFlagArg("AoE Haste, 15 MP cost"),
            "use_phys_lucca": aty.RandomFlagArg("+Hit. Physical Flame Toss + Bombs"),
            "use_protect_all": aty.RandomFlagArg("AoE Protect, 2x MP cost"),
            "use_reraise": aty.RandomFlagArg("Life2 gives greendream effect"),
            "use_magus_dual_techs": aty.RandomFlagArg("Magus can perform dual techs with fire/ice/lit2"),
            "use_daltonized_magus": aty.RandomFlagArg("Magus shadow techs are replaced with Dalton versions"),
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
            ),
            "character_identity_randomization": aty.arg_from_enum(
                CharacterIdentityRandoScheme, CharacterIdentityRandoScheme.VANILLA,
                "How character identities should be assigned"
            ),
            "character_reassign_keep_stats": aty.RandomFlagArg(
                "When randomizing characters, don't change stats", 0
            )
        }

        for char_id in ctenums.CharID:
            arg_name = f"{str(char_id).lower()}_identity_choices"
            help_text = f"Possible character assignments for {char_id}"
            spec[arg_name] = aty.arg_multiple_from_enum(
                ctenums.CharID, tuple(x for x in ctenums.CharID),
                help_text, allow_duplicates=True,
            )

        return spec

    def get_choice_dict(self) -> dict[ctenums.CharID, tuple[ctenums.CharID, ...]]:
        return {
            ctenums.CharID.CRONO: self.crono_identity_choices,
            ctenums.CharID.MARLE: self.marle_identity_choices,
            ctenums.CharID.LUCCA: self.lucca_identity_choices,
            ctenums.CharID.ROBO: self.robo_identity_choices,
            ctenums.CharID.FROG: self.frog_identity_choices,
            ctenums.CharID.AYLA: self.ayla_identity_choices,
            ctenums.CharID.MAGUS: self.magus_identity_choices,
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

    def get_definite_version(self, rng: random.RNGType) -> typing.Self:
        kw_dict: dict[str, typing.Any] = dict()
        for name, arg in self.get_argument_spec().items():
            val = getattr(self, name)
            if isinstance(arg, aty.RandomFlagArg):
                bool_val = rng.randrange(0, 100) < val
                kw_dict[name] = 100*int(bool_val)
            else:
                kw_dict[name] = val

        return self.__class__(**kw_dict)


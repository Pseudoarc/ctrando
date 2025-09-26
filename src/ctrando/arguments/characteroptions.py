"""Options for Modifying Character Attributes"""
import argparse
from dataclasses import dataclass, field
import typing

from ctrando.arguments import argumenttypes as aty


@dataclass()
class CharacterOptions:
    attr_names: typing.ClassVar[tuple[str, ...]] = (
        "use_phys_marle", "use_haste_all", "use_phys_lucca", "use_protect_all",
        "use_reraise", "use_magus_dual_techs", "use_daltonized_magus"
    )

    use_phys_marle: bool = False
    use_haste_all: bool = False
    use_phys_lucca: bool = False
    use_protect_all: bool = False
    use_reraise: bool = False
    use_magus_dual_techs: bool = False
    use_daltonized_magus: bool = False

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        return {
            "use_phys_marle": aty.FlagArg("+Hit, Physical arrow tech"),
            "use_haste_all": aty.FlagArg("AoE Haste, 15 MP cost"),
            "use_phys_lucca": aty.FlagArg("+Hit. Physical Flame Toss + Bombs"),
            "use_protect_all": aty.FlagArg("AoE Protect, 2x MP cost"),
            "use_reraise": aty.FlagArg("Life2 gives greendream effect"),
            "use_magus_dual_techs": aty.FlagArg("Magus can perform dual techs with fire/ice/lit2"),
            "use_daltonized_magus": aty.FlagArg("Magus shadow techs are replaced with Dalton versions")
        }

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Character Options",
            "Options which alter character stats and abilities"
        )
        help_dict = {
            name: arg.help_text for name, arg in cls.get_argument_spec().items()
        }
        # help_dict: dict[str, str] = {
        #     "use_phys_marle": "+Hit, Physical arrow tech",
        #     "use_haste_all": "AoE Haste, 15 MP cost",
        #     "use_phys_lucca": "+Hit. Physical Flame Toss + Bombs",
        #     "use_protect_all": "AoE Protect, 2x MP cost",
        #     "use_reraise": "Life2 gives greendream effect",
        #     "use_magus_dual_techs": "Magus can perform dual techs with fire/ice/lit2",
        #     "use_daltonized_magus": "Magus shadow techs are replaced with Dalton versions"
        # }
        aty.add_dataclass_to_group(cls, group, help_dict)


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ret = aty.extract_from_namespace(cls, cls.attr_names, namespace)
        return ret

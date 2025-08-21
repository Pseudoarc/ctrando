"""Options for Modifying Character Attributes"""
import argparse
from dataclasses import dataclass, field
import typing

from ctrando.arguments import argumenttypes as aty


@dataclass()
class CharacterOptions:
    attr_names: typing.ClassVar[tuple[str, ...]] = (
        "use_phys_marle", "use_haste_all", "use_phys_lucca", "use_protect_all"
    )

    use_phys_marle: bool = False
    use_haste_all: bool = False
    use_phys_lucca: bool = False
    use_protect_all: bool = False

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Character Options",
            "Options which alter character stats and abilities"
        )
        help_dict: dict[str, str] = {
            "use_phys_marle": "+Hit, Physical arrow tech",
            "use_haste_all": "AoE Haste, 15 MP cost",
            "use_phys_lucca": "+Hit. Physical Flame Toss + Bombs",
            "use_protect_all": "AoE Protect, 2x MP cost"
        }
        aty.add_dataclass_to_group(cls, group, help_dict)


    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        ret = aty.extract_from_namespace(cls, cls.attr_names, namespace)
        return ret

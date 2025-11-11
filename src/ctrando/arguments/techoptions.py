from __future__ import annotations
import argparse
import enum
import typing

from ctrando.arguments import argumenttypes


class TechOrder(enum.StrEnum):
    VANILLA = "vanilla",
    RANDOM = "random"
    MP_ORDER = "mp"
    MP_TYPE_ORDER = "mp_type"


class TechDamage(enum.StrEnum):
    VANILLA = "vanilla"
    SHUFFLE = "shuffle"
    RANDOM = "random"


class TechOptions:
    """Class for storing options for techs."""
    _default_mp_random_factor_min: typing.ClassVar[float] = 1.0
    _default_mp_random_factor_max: typing.ClassVar[float] = 1.0
    _default_tech_order: typing.ClassVar[TechOrder] = TechOrder.VANILLA
    _default_tech_damage: typing.ClassVar[TechDamage] = TechDamage.VANILLA
    _default_preserve_magic: typing.ClassVar[bool] = False
    _default_black_hole_factor: typing.ClassVar[float] = 8/3
    _default_black_hole_min: typing.ClassVar[float] = 0.0
    _default_show_full_tech_list = False

    def __init__(
            self,
            tech_order: TechOrder = _default_tech_order,
            tech_damage: TechDamage = _default_tech_damage,
            tech_damage_random_factor_min: float = _default_mp_random_factor_min,
            tech_damage_random_factor_max: float = _default_mp_random_factor_max,
            preserve_magic: bool = False,
            black_hole_min: float = _default_black_hole_min,
            black_hole_factor: float = _default_black_hole_factor,
            show_full_tech_list: bool = _default_show_full_tech_list,
            balance_tech_mps: bool = False
    ):

        self.tech_order = tech_order
        self.tech_damage = tech_damage

        tech_damage_random_factor_min = max(0.0, tech_damage_random_factor_min)
        tech_damage_random_factor_max = max(0.0, tech_damage_random_factor_max)
        tech_damage_random_factor_min, tech_damage_random_factor_max = sorted(
            [tech_damage_random_factor_min, tech_damage_random_factor_max]
        )

        self.tech_damage_random_factor_min = tech_damage_random_factor_min
        self.tech_damage_random_factor_max = tech_damage_random_factor_max
        self.preserve_magic = preserve_magic
        self.black_hole_min = black_hole_min
        self.black_hole_factor = black_hole_factor
        self.show_full_tech_list = show_full_tech_list
        self.balance_tech_mps = balance_tech_mps

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        return {
            "tech_order": argumenttypes.arg_from_enum(
                TechOrder, cls._default_tech_order,
                "Order in which techs are learned"
            ),
            "tech_damage": argumenttypes.arg_from_enum(
                TechDamage, cls._default_tech_damage,
                "Damage dealt by techs"
            ),
            "tech_damage_random_factor_min": argumenttypes.DiscreteNumericalArg(
                0.05, 2.00, 0.05,
                cls._default_mp_random_factor_min,
                help_text="Minimum percent (as decimal, default 1.0) which "
                          "MP costs may shift (ignored if vanilla damage)",
                type_fn=float
            ),
            "tech_damage_random_factor_max": argumenttypes.DiscreteNumericalArg(
                0.05, 2.00, 0.05,
                cls._default_mp_random_factor_max,
                help_text="Maximum percent (as decimal, default 1.0) which "
                          "MP costs may shift (ignored if vanilla damage)",
                type_fn=float
            ),
            "preserve_magic": argumenttypes.FlagArg(
                "Keep each PC's first magic tech in its vanilla location "
                "(may break specified order)"
            ),
            "black_hole_factor": argumenttypes.DiscreteNumericalArg(
                0.0, 10.0, 0.5, cls._default_black_hole_factor,
                "Percent kill chance per MP in black hole's cost",
                type_fn=float
            ),
            "black_hole_min": argumenttypes.DiscreteNumericalArg(
                0.0, 100.0, 0.5, cls._default_black_hole_factor,
                "Base percent kill chance for black hole, total is base + mp*factor",
                type_fn=float
            ),
            "show_full_tech_list": argumenttypes.FlagArg(
                "The tech page of the menu will show all single techs"
            ),
            "balance_tech_mps": argumenttypes.FlagArg(
                "Ensure every character has at least one strong tech."
            )
        }

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Add Tech Settings to parser."""
        group = parser.add_argument_group(
            "Tech Options",
            "Options relating to Player Techs"
        )

        argumenttypes.add_str_enum_to_group(
            group, "--tech-order", TechOrder,
            help_str="Order in which techs are learned",
        )
        argumenttypes.add_str_enum_to_group(
            group, "--tech-damage", TechDamage,
            help_str="Damage dealt by techs",
        )
        group.add_argument(
            "--tech-damage-random-factor-min",
            type=float,
            help="Minimum percent (as decimal, default 1.0) which MP costs may shift (ignored if vanilla damage)",
            default=argparse.SUPPRESS
        )
        group.add_argument(
            "--tech-damage-random-factor-max",
            type=float,
            help="Maximum percent (as decimal, default 1.0) which MP costs may shift (ignored if vanilla damage)",
            default=argparse.SUPPRESS
        )
        group.add_argument(
            "--preserve-magic", action="store_true",
            help="Keep each PC's first magic tech in its vanilla location "
            "(may break specified order)",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--black-hole-factor", action="store",
            type=float, default=argparse.SUPPRESS,
            help="Percent kill chance per MP in black hole's cost."

        )

        group.add_argument(
            "--black-hole-min", action="store",
            type=float, default=argparse.SUPPRESS,
            help="Base percent kill chance for black hole.  Total is base + mp*factor."
        )

        group.add_argument(
            "--show-full-tech-list", action="store_true",
            help="The tech page of the menu will show all single techs",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--balance-tech-mps", action="store_true",
            help="Ensure every character has at least one strong tech.",
            default=argparse.SUPPRESS
        )

    @classmethod
    def extract_from_namespace(
            cls, namespace: argparse.Namespace
    ) -> typing.Self:
        attr_names = ["tech_order", "tech_damage", "tech_damage_random_factor_min",
                      "tech_damage_random_factor_max", "preserve_magic",
                      "black_hole_min", "black_hole_factor", "show_full_tech_list",
                      "balance_tech_mps"]

        return argumenttypes.extract_from_namespace(
            cls,
            arg_names=attr_names,
            namespace=namespace
        )

    def __str__(self):
        return (
            f"{self.__class__.__name__}("
            f"tech_order={self.tech_order}, "
            f"tech_damage={self.tech_damage}, "
            f"tech_damage_random_factor_min={self.tech_damage_random_factor_min}, "
            f"tech_damage_random_factor_max={self.tech_damage_random_factor_max}, "
            f"preserve_magic={self.preserve_magic}, "
            f"black_hole_min={self.black_hole_min}, "
            f"black_hole_factor={self.black_hole_factor}, "
            f"show_full_tech_list={self.show_full_tech_list}"
            f"balance_tech_mps={self.balance_tech_mps}"
            ")"
        )





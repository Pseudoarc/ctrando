"""Entrance Shuffler Options"""
import argparse
import functools
import typing

from ctrando.overworlds.owexitdata import OWExitClass as OWExit
from ctrando.arguments import argumenttypes as aty


class EntranceShufflerOptions:
    _default_shuffle_entrances: typing.ClassVar[bool] = False
    # _default_preserve_dungeons: typing.ClassVar[bool] = False
    # _default_preserve_shops: typing.ClassVar[bool] = False
    # Note: Entrance Rando does not have the default Tyrano Lair exit.
    #       Instead, the Lair Ruins by default goes to Tyrano Lair and
    #       LV portal by default goes to Lair Ruins.  So if you want to
    #       make Tyrano Lair a preserved spot, use "lair_ruins".
    _default_preserve_spots: typing.ClassVar[tuple[OWExit, ...]] = (
        # Recruits
        OWExit.MANORIA_CATHEDRAL, OWExit.GUARDIA_CASTLE_1000,
        OWExit.MILLENNIAL_FAIR, OWExit.GUARDIA_CASTLE_600, OWExit.CURSED_WOODS,
        OWExit.DACTYL_NEST, OWExit.PROTO_DOME, OWExit.NORTH_CAPE, OWExit.DEATH_PEAK,
        # Other Dungeons
        OWExit.HECKRAN_CAVE, OWExit.VORTEX_PT, OWExit.ZENAN_BRIDGE_600_NORTH,
        OWExit.DENADORO_MTS, OWExit.MAGUS_LAIR, OWExit.ARRIS_DOME,
        OWExit.FACTORY_RUINS, OWExit.NORTHERN_RUINS_600, OWExit.NORTHERN_RUINS_1000,
        OWExit.GIANTS_CLAW, OWExit.OZZIES_FORT, OWExit.SUNKEN_DESERT,
        OWExit.SUN_PALACE, OWExit.GENO_DOME, OWExit.REPTITE_LAIR,
        OWExit.LAIR_RUINS,  # OWExit.TYRANO_LAIR,
        OWExit.TERRA_CAVE, OWExit.LAST_VILLAGE_COMMONS,
        OWExit.ZEAL_PALACE, OWExit.BLACKBIRD, OWExit.WEST_CAPE,
        # Important exits that are annoying to bury
        OWExit.CHORAS_CARPENTER_600, OWExit.LUCCAS_HOUSE,
        OWExit.SUN_KEEP_PREHISTORY, OWExit.SUN_KEEP_2300,
        OWExit.PORRE_MAYOR_1000, OWExit.PORRE_ELDER_600,
        OWExit.FIONAS_VILLA, OWExit.FIONAS_SHRINE,
        OWExit.SNAIL_STOP, OWExit.KEEPERS_DOME, OWExit.TATAS_HOUSE,
    )
    _default_vanilla_spots: typing.ClassVar[tuple[OWExit, ...]] = ()

    @classmethod
    def get_argument_spec(cls) -> aty.ArgSpec:
        return {
            "shuffle_entrances": aty.FlagArg("Whether to shuffle entrances or not"),
            "preserve_spots": aty.arg_multiple_from_enum(
                OWExit, cls._default_preserve_spots,
                "Spots which are to be shuffled among themselves"
            ),
            "rest_vanilla": aty.FlagArg("Only shuffle locations in preserve_spots"),
            "vanilla_spots": aty.arg_multiple_from_enum(
                OWExit, cls._default_vanilla_spots,
                "Spots guaranteed to not be shuffled. Takes precedence over preserve_spots"
            ),
            "shuffle_gates": aty.FlagArg("Shuffle where (non-algetty) portals lead to")
        }

    def __init__(
            self,
            shuffle_entrances: bool = _default_shuffle_entrances,
            preserve_spots: tuple[OWExit, ...] = _default_preserve_spots,
            vanilla_spots: tuple[OWExit, ...] = _default_vanilla_spots,
            rest_vanilla: bool = False,
            shuffle_gates: bool = False
    ):
        self.shuffle_entrances = shuffle_entrances

        if OWExit.TYRANO_LAIR in preserve_spots or OWExit.TYRANO_LAIR in vanilla_spots:
            raise ValueError("Use \"lair_ruins\" in place of \"tyrano_lair\"")

        vanilla_spot_temp = {spot: None for spot in vanilla_spots}
        self.vanilla_spots = tuple(vanilla_spot_temp.keys())

        preserve_spot_temp = {spot: None for spot in preserve_spots}
        self.preserve_spots = tuple(
            x for x in preserve_spot_temp.keys() if x not in vanilla_spots
        )

        if rest_vanilla:
            total_spots = list(OWExit)
            total_spots.remove(OWExit.TYRANO_LAIR)
            self.vanilla_spots = tuple(
                x for x in total_spots if x not in preserve_spots
            )

        self.shuffle_gates = shuffle_gates

    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        group = parser.add_argument_group(
            "Entrance Shuffler Options",
            "Options for how overworld entrances are shuffled."
        )

        group.add_argument(
            "--shuffle-entrances",
            action="store_true",
            help="Shuffle the target of overworld entrances",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--preserve-spots",
            nargs="*",
            type=functools.partial(aty.str_to_enum, enum_type=OWExit),
            help="Spots which are to be shuffled among themselves.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--rest-vanilla",
            action="store_true",
            help="Only shuffle locations specified by --preserve-spots (default: False)",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--vanilla-spots",
            nargs="*",
            type=functools.partial(aty.str_to_enum, enum_type=OWExit),
            help="Spots which are not shuffled.  Will take precedence over --preserve-spots",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--shuffle-gates",
            action="store_true",
            help="Shuffle where (non-algetty) portals lead",
            default=argparse.SUPPRESS
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:
        attr_names = [
            "shuffle_entrances", "preserve_spots", "vanilla_spots", "rest_vanilla",
            "shuffle_gates"  # "preserve_dungeons", "preserve_shops"
        ]
        return aty.extract_from_namespace(cls, arg_names=attr_names, namespace=namespace)

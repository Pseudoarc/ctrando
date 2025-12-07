"""Options which are applied after randomization."""
import argparse
from dataclasses import dataclass, field
import enum

import typing
from functools import partial

from ctrando.arguments import argumenttypes
from ctrando.postrando.palettes import SNESPalette


def clip(val: float, min_val: float, max_val: float) -> float:
    return sorted([min_val, val, max_val])[1]


class EndingID(enum.StrEnum):
    BEYOND_TIME = "beyond time"
    THE_DREAM_PROJECT = "the dream project"
    THE_SUCCESSOR_OF_GUARDIA = "the successor of guardia"
    GOODNIGHT = "goodnight"
    THE_LEGENDARY_HERO = "the legendary hero"
    THE_UNKNOWN_PAST = "the unknown past"
    PEOPLE_OF_THE_TIMES = "people of the times"
    THE_OATH = "the oath"
    DINO_AGE = "dino age"
    WHAT_THE_PROPHET_SEEKS = "what the prophet seeks"
    SLIDE_SHOW = "a slide show?"
    RANDOM = "random"


@dataclass()
class PostRandoOptions:
    attr_names: typing.ClassVar[tuple[str, ...]] = (
        "default_fast_loc_movement", "default_fast_ow_movement",
        "default_fast_epoch_movement", "battle_speed", "message_speed",
        "battle_memory_cursor", "menu_memory_cursor",
        "window_background",
        "crono_palette", "marle_palette", "lucca_palette", "robo_palette",
        "frog_palette", "ayla_palette", "magus_palette",
        "ending", "remove_flashes"
    )
    _default_fast_loc_movement: typing.ClassVar[bool] = False
    _default_fast_ow_movement: typing.ClassVar[bool] = False
    _default_fast_epoch_movement: typing.ClassVar[bool] = False

    _default_battle_speed: typing.ClassVar[int] = 5
    _default_message_speed: typing.ClassVar[int] = 5

    _default_battle_memory_cursor: typing.ClassVar[bool] = False
    _default_menu_memory_cursor: typing.ClassVar[bool] = False
    _default_window_background: typing.ClassVar[int] = 1

    _default_crono_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6510FF7F3F4F1F363F02171CB53A4A77C639E11C0B00881C")
    _default_marle_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6514FF7F7F6BBF52FF27BF1EBF097000F05F293E4421671C")
    _default_lucca_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6510FF7F9F577F361F17922A8B151F0A532DA918FE7DA61C")
    _default_robo_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6510FF7F3E3F571AF4678D3E9021724EEB102925C718C920")
    _default_frog_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "8514FF7FCF0BCA02FF1A0B721A3D93010F124915C510881C")
    _default_ayla_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6510FF7FDF4A1B26FF3B3E039329AC1C50564A39A7288618")
    _default_magus_palette_b: typing.ClassVar[bytes] = bytes.fromhex(
        "6510BD7F3B5B562EAD7E4D653A1EC74035199028641C8614")

    _default_crono_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6510FF7F3F4F1F363F02171CB53A4A77C639E11C0B00881C"))
    _default_marle_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6514FF7F7F6BBF52FF27BF1EBF097000F05F293E4421671C"))
    _default_lucca_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6510FF7F9F577F361F17922A8B151F0A532DA918FE7DA61C"))
    _default_robo_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6510FF7F3E3F571AF4678D3E9021724EEB102925C718C920"))
    _default_frog_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("8514FF7FCF0BCA02FF1A0B721A3D93010F124915C510881C"))
    _default_ayla_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6510FF7FDF4A1B26FF3B3E039329AC1C50564A39A7288618"))
    _default_magus_palette: typing.ClassVar[SNESPalette] = SNESPalette.from_bytes(
        bytes.fromhex("6510BD7F3B5B562EAD7E4D653A1EC74035199028641C8614"))

    default_fast_loc_movement: bool = _default_fast_loc_movement
    default_fast_ow_movement: bool = _default_fast_ow_movement
    default_fast_epoch_movement: bool = _default_fast_epoch_movement

    battle_speed: int = _default_battle_speed
    message_speed: int = _default_message_speed
    battle_memory_cursor: bool = _default_battle_memory_cursor
    menu_memory_cursor: bool = _default_menu_memory_cursor
    window_background: int = _default_window_background

    crono_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_crono_palette_b))
    marle_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_marle_palette_b))
    lucca_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_lucca_palette_b))
    robo_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_robo_palette_b))
    frog_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_frog_palette_b))
    ayla_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_ayla_palette_b))
    magus_palette: SNESPalette = field(default_factory = partial(SNESPalette.from_bytes,
                                                                 _default_magus_palette_b))

    ending: EndingID = EndingID("the dream project")
    remove_flashes: bool = False

    def __post_init__(self):
        self.battle_speed = sorted([1, int(self.battle_speed), 8])[1]
        self.message_speed = sorted([1, int(self.message_speed), 8])[1]

    @classmethod
    def get_argument_spec(cls) -> argumenttypes.ArgSpec:
        ret_dict: argumenttypes.ArgSpec = {
            "default_fast_loc_movement": argumenttypes.FlagArg(
                "Default location (dungeon, etc) movement is fast and run button slows"),
            "default_fast_ow_movement": argumenttypes.FlagArg(
                "Default overworld movement is fast and run button slows"),
            "default_fast_epoch_movement": argumenttypes.FlagArg(
                "Default epoch movement is fast and run button slows"),
            "battle_speed": argumenttypes.DiscreteNumericalArg(
                1, 8, 1, cls._default_battle_speed,
                "Default battle speed", type_fn=int),
            "message_speed": argumenttypes.DiscreteNumericalArg(
                1, 8, 1, cls._default_message_speed,
                "Default message speed", type_fn=int),
            "battle_memory_cursor": argumenttypes.FlagArg(
                "By default turn battle memory cursor on"),
            "menu_memory_cursor": argumenttypes.FlagArg(
                "By default turn menu memory cursor on"),
            "window_background": argumenttypes.DiscreteNumericalArg(
                1, 8, 1, cls._default_window_background,
                "Default window background", type_fn=int
            )
        }

        # defaults = (cls._default_crono_palette, cls._default_marle_palette,
        #             cls._default_lucca_palette, cls._default_robo_palette,
        #             cls._default_frog_palette, cls._default_ayla_palette,
        #             cls._default_ayla_palette)
        for arg_name in ("crono_palette", "marle_palette", "lucca_palette", "robo_palette",
                         "frog_palette", "ayla_palette", "magus_palette",):
            char_name = arg_name.split("_")[0].capitalize()
            ret_dict[arg_name] = argumenttypes.StringArgument[SNESPalette](
                help_text=f"Hex format palette for {char_name}",
                parser=SNESPalette.from_hex_sequence,
                default_value=""
            )

        ret_dict["ending"] = argumenttypes.arg_from_enum(
            EndingID, EndingID.THE_DREAM_PROJECT,
            "name of ending (or \"random\")"
        )
        ret_dict["remove_flashes"] = argumenttypes.FlagArg(
            "Remove flashes from many animations"
        )

        return ret_dict



    @classmethod
    def add_group_to_parser(cls, parser: argparse.ArgumentParser):
        """Add these options to the parser."""

        group = parser.add_argument_group(
            "Post-Randomization Options",
            "Options which are applied to an already-randomized rom."
        )

        group.add_argument(
            "--default-fast-loc-movement",
            action="store_true",
            help="Default location (dungeon, etc) movement is fast and run button slows.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--default-fast-ow-movement",
            action="store_true",
            help="Default overworld movement is fast and run button slows.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--default-fast-epoch-movement",
            action="store_true",
            help="Default epoch movement is fast and run button slows.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--battle-speed",
            action="store",
            type=lambda x: clip(int(x), 1, 8),
            help="Default battle speed.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--message-speed",
            action="store",
            type=lambda x: clip(int(x), 1, 8),
            help="Default message speed.",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--battle-memory-cursor",
            action="store_true",
            help="By default turn battle memory cursor on",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--menu-memory-cursor",
            action="store_true",
            help="By default turn menu memory cursor on",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--window-background",
            action="store",
            type=lambda x: clip(int(x), 1, 8),
            help="Default window background",
            default=argparse.SUPPRESS
        )

        for name in ("crono_palette", "marle_palette", "lucca_palette", "robo_palette",
        "frog_palette", "ayla_palette", "magus_palette"):
            char_name = name.split("_")[0]
            name = "--" + name.replace("_", "-")
            group.add_argument(name, action="store", type=SNESPalette.from_hex_sequence,
                               help=f"Hex format palette for {char_name}",
                               default=argparse.SUPPRESS)

        group.add_argument(
            "--ending", action="store",
            type=EndingID,
            help="name of ending (or \"random\")",
            default=argparse.SUPPRESS
        )

        group.add_argument(
            "--remove-flashes", action="store_true",
            help="Remove flashes from many animations."
        )

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace) -> typing.Self:

        ret = argumenttypes.extract_from_namespace(
            cls, cls.attr_names, namespace
        )

        return ret

    def to_toml_dict(self) -> dict[str, typing.Any]:
        ret_dict = {}

        for name in self.attr_names:
            if name in ("crono_palette", "marle_palette", "lucca_palette", "robo_palette",
                        "frog_palette", "ayla_palette", "magus_palette"):
                attr: SNESPalette = getattr(self, name)
                ret_dict[name] =  attr.to_hex_sequence()
            else:
                ret_dict[name] = getattr(self, name)

        return ret_dict

    def to_namespace(self) -> argparse.Namespace:
        name_dict = self.to_toml_dict()
        return argparse.Namespace(**name_dict)

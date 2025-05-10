"""Options which are applied after randomization."""
import argparse
from dataclasses import dataclass
import typing

from ctrando.arguments import argumenttypes


def clip(val: float, min_val: float, max_val: float) -> float:
    return sorted([min_val, val, max_val])[1]


@dataclass()
class PostRandoOptions:
    attr_names: typing.ClassVar[tuple[str, ...]] = (
        "default_fast_loc_movement", "default_fast_ow_movement",
        "default_fast_epoch_movement", "battle_speed", "message_speed",
        "battle_memory_cursor", "menu_memory_cursor"
    )
    _default_fast_loc_movement: typing.ClassVar[bool] = False
    _default_fast_ow_movement: typing.ClassVar[bool] = False
    _default_fast_epoch_movement: typing.ClassVar[bool] = False

    _default_battle_speed: typing.ClassVar[int] = 5
    _default_message_speed: typing.ClassVar[int] = 5

    _default_battle_memory_cursor: typing.ClassVar[bool] = False
    _default_menu_memory_cursor: typing.ClassVar[bool] = False

    default_fast_loc_movement: bool = _default_fast_loc_movement
    default_fast_ow_movement: bool = _default_fast_ow_movement
    default_fast_epoch_movement: bool = _default_fast_epoch_movement

    battle_speed: int = _default_battle_speed
    message_speed: int = _default_message_speed
    battle_memory_cursor: bool = _default_battle_memory_cursor
    menu_memory_cursor: bool = _default_menu_memory_cursor

    def __post_init__(self):
        self.battle_speed = sorted([1, int(self.battle_speed), 8])[1]
        self.message_speed = sorted([1, int(self.message_speed), 8])[1]

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

    @classmethod
    def extract_from_namespace(cls, namespace: argparse.Namespace):
        ret = argumenttypes.extract_from_namespace(
            cls, cls.attr_names, namespace
        )

        return ret

    def to_toml_dict(self) -> dict[str, typing.Any]:
        return {
            name: getattr(self, name) for name in self.attr_names
        }

    def to_namespace(self) -> argparse.Namespace:
        name_dict = self.to_toml_dict()
        return argparse.Namespace(**name_dict)

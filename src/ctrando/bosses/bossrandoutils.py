"""Useful routines and datatypes for boss rando."""
from dataclasses import dataclass, field
import typing
from typing import Union

from ctrando.common import ctenums
from ctrando.bosses import bosstypes
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF


HookLocator = typing.Callable[[LocationEvent], int]


def find_first_coord(script: LocationEvent, obj_id, func_id) -> int:
    ...


class CommandHookLocator:
    """This is too close to something in objectives, but merging the ideas comes later."""
    def __init__(
            self,
            obj_id: int,
            func_id: int,
            command_sequence: typing.Optional[list[Union[int, EC]]],
            after_last: bool = False
    ):
        self.obj_id = obj_id
        self.func_id = func_id
        if command_sequence is None:
            command_sequence = []
        self.command_sequence = list(command_sequence)

        self.after_last = after_last

    def __call__(self, script: LocationEvent) -> int:
        pos = script.get_function_start(self.obj_id, self.func_id)
        cur_cmd = get_command(script.data, pos)

        for cmd in self.command_sequence:
            if isinstance(cmd, int):
                pos, cur_cmd = script.find_command([cmd], pos)
            elif isinstance(cmd, EC):
                pos = script.find_exact_command(cmd, pos)
                cur_cmd = cmd

            pos += len(cur_cmd)

        if not self.after_last and self.command_sequence:
            pos -= len(cur_cmd)

        return pos


def are_tiles_coords(pixel_x, pixel_y) -> bool:
    return ((pixel_x - 8) % 0x10 == 0) and ((pixel_y-0xF) % 0x10 == 0)


def tile_to_pixel_coords(tile_x: int, tile_y: int) -> tuple[int, int]:
    return tile_x*0x10 + 8, tile_y*0x10+0x0F


def extract_pixel_coordinates(command: EC) -> tuple[int, int]:
    if command.command in (0x8B, 0x96):  # Tile coordinates
        x_coord, y_coord = tile_to_pixel_coords(command.args[0], command.args[1])
    elif command.command == 0x8D:  # Pixel Coordinates
        x_coord, y_coord = command.args[0] >> 4, command.args[1] >> 4
    else:  # Can add more cases for move commands
        raise TypeError(f"{command} does not support coordinates")

    return x_coord, y_coord


def can_use_tile_coords(
        first_x_px: int, first_y_px: int,
        boss_scheme: bosstypes.BossScheme
) -> bool:
    for part in boss_scheme.parts:
        x_coord, y_coord = first_x_px + part.displacement[0], first_y_px + part.displacement[1]
        if not are_tiles_coords(x_coord, y_coord):
            return False

        return True


def update_boss_object_load(
        script: LocationEvent,
        part: bosstypes.BossPart,
        obj_id: int,
        load_index: int = 0
):
    pos = script.get_object_start(obj_id)
    for ind in range(load_index+1):
        pos, cmd = script.find_command([0x83], pos)
        if ind != load_index:
            pos += len(cmd)

    cmd = get_command(script.data, pos)
    is_static = bool(cmd.args[1] & 0x80)
    script.replace_command_at_pos(pos, EC.load_enemy(part.enemy_id, part.slot, is_static))


def update_boss_object_coordinates(
        script: LocationEvent,
        part: bosstypes.BossPart,
        base_x_px: int,
        base_y_px: int,
        obj_id: int,
        func_id: FID = FID.STARTUP,
        command_index: int = 0,
        force_pixel_coords: bool = False
):
    pos = script.get_function_start(obj_id, func_id)

    obj_x_px = max(base_x_px + part.displacement[0], 0)
    obj_y_px = max(base_y_px + part.displacement[1], 0)

    for ind in range(command_index+1):
        pos, cmd = script.find_command([0x8B, 0x8D], pos)
        if ind != command_index:
            pos += len(cmd)

    new_coord_cmd = EC.set_object_coordinates_auto(obj_x_px, obj_y_px, force_pixel_coords)
    script.replace_command_at_pos(pos, new_coord_cmd)


def append_boss_object(
        script: LocationEvent,
        part: bosstypes.BossPart,
        first_x_px: int,
        first_y_px: int,
        force_pixel_coords: bool = False,
        is_shown: bool = False
) -> int:
    """Build a new object for a boss part and return its index."""

    new_obj_id = script.append_empty_object()

    coord_command = EC.set_object_coordinates_auto(
        first_x_px + part.displacement[0],
        first_y_px + part.displacement[1],
        force_pixel_coords
    )

    startup = (
        EF()
        .add(EC.load_enemy(part.enemy_id, part.slot, False))
        .add(coord_command)
    )
    if not is_shown:
        startup.add(EC.set_own_drawing_status(False))
    startup.append(
        EF()
        .add(EC.return_cmd())
        .add(EC.end_cmd())
    )

    do_nothing = EF().add(EC.return_cmd())

    script.set_function(new_obj_id, FID.STARTUP, startup)
    script.set_function(new_obj_id, FID.ACTIVATE, do_nothing)
    script.set_function(new_obj_id, FID.TOUCH, do_nothing)

    return new_obj_id


def assign_boss_to_one_spot_location_script(
        script: LocationEvent,
        boss_scheme: bosstypes.BossScheme,
        boss_load_finder: HookLocator,
        show_pos_finder: typing.Optional[HookLocator] = None,
        last_coord_finder: typing.Optional[HookLocator] = None,
        battle_x_px: typing.Optional[int] = None,
        battle_y_px: typing.Optional[int] = None,
):
    """
    Assign any boss to a location which originally has a one spot boss.
    - script: LocationEvent -- The script in which the assignment is made
    - boss_scheme: bosstypes.BossScheme -- The parts of the boss to assign
    - boss_load_finder: HookLocator -- Finds the location of the LoadEnemy command
            which loads the one-part boss.
    - coord_finder: HookLocator | None -- Finds the coordinate-setting function for the boss
    - show_pos_finder: HookLocator | None -- Finds where to show the additional parts of the
            assigned boss.  May be None if the boss's parts should all start visible.
    - last_coord_finder: HookLocator | None  Finds the command which last sets the boss's coordinate.
            Used to set the positions of additional parts.
    - battle_x_px, battle_y_px: (int, int) -- If last_coord_finder is None, gives hardcoded
            values for the position of the boss
    """

    # replace the main part with
    main_part = boss_scheme.parts[0]

    pos: typing.Optional[int] = None
    cmd: typing.Optional[EC] = None

    if battle_x_px is None or battle_y_px is None:
        pos = last_coord_finder(script)
        cmd = get_command(script.data, pos)
        battle_x_px, battle_y_px = extract_pixel_coordinates(cmd)

    force_px = not can_use_tile_coords(battle_x_px, battle_y_px, boss_scheme)

    if pos is not None and cmd is not None:
        new_coord_command = EC.set_object_coordinates_auto(
            battle_x_px, battle_y_px, force_px
        )

        if new_coord_command.command != cmd.command:
            if cmd.command in (0x8B, 0x8D):  # Is coord setting
                script.replace_command_at_pos(pos, new_coord_command)
            else:  # Some sort of move command, insert after the move
                script.insert_commands(
                    new_coord_command.to_bytearray(),
                    pos + len(cmd)
                )

    pos = boss_load_finder(script)
    boss_load_cmd = get_command(script.data, pos)
    is_static = bool(boss_load_cmd.args[1] & 0x80)
    new_boss_load_cmd = EC.load_enemy(main_part.enemy_id, main_part.slot, is_static)
    script.data[pos:pos+len(boss_load_cmd)] = new_boss_load_cmd.to_bytearray()

    is_shown = True if show_pos_finder is None else False

    show_cmds = EF()
    for part in boss_scheme.parts[1:]:
        obj_id = append_boss_object(
            script, part, battle_x_px, battle_y_px, force_px, is_shown
        )

        if not is_shown:
            show_cmds.add(EC.set_object_drawing_status(obj_id, True))

    if not is_shown:
        pos = show_pos_finder(script)
        script.insert_commands(show_cmds.get_bytearray(), pos)


@dataclass
class BadAnimData:
    bad_static_anims: list[int] = field(default_factory=list)
    bad_normal_anims: list[int] = field(default_factory=list)
    good_static_anims: typing.Optional[list[int]] = None
    good_normal_anims: typing.Optional[list[int]] = None


def fix_animations(
        script: LocationEvent,
        obj_id: int,
        func_id: typing.Optional[int],
        bad_anim_data: BadAnimData
):
    """Remove bad animation commands"""
    if func_id is None:
        start = script.get_object_start(obj_id)
        end = script.get_object_end(obj_id)
    else:
        start = script.get_function_start(obj_id, func_id)
        end = script.get_function_end(obj_id, func_id)

    use_norm_whitelist = False if bad_anim_data.good_normal_anims is None else True
    use_static_whitelist = False if bad_anim_data.good_static_anims is None else True

    pos = start
    while pos < end:
        pos, cmd = script.find_command_opt(
            [
                EC.static_animation(0).command, EC.play_animation(0, True).command,
                EC.play_animation(0, False).command
            ], pos, end
        )

        if pos is None or pos >= end:
            break

        delete = False
        if cmd.command in (EC.play_animation(0,True).command,
                           EC.play_animation(0,False).command):
            if (
                    cmd.args[0] in bad_anim_data.bad_normal_anims or
                    use_norm_whitelist and cmd.args[0] not in bad_anim_data.good_normal_anims
            ):
                script.delete_commands(pos, 1)
            else:
                pos += len(cmd)

        elif cmd.command == EC.static_animation(0).command:
            if (
                    cmd.args[0] in bad_anim_data.bad_static_anims or
                    use_static_whitelist and cmd.args[0] not in bad_anim_data.good_static_anims
            ):
                script.delete_commands(pos, 1)
            else:
                pos += len(cmd)


_bad_anim_dict: dict[ctenums.EnemyID, BadAnimData] = {
    ctenums.EnemyID.NU: BadAnimData([], [])
}
"""Functions to assign bosses to spots."""
import dataclasses
import typing

from ctrando.base import openworldutils as owu
from ctrando.bosses import bossrandoutils as bru, bosstypes
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, get_command, Operation as OP
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.objectives import objectivetypes as oty
from ctrando.common import ctenums, memory
from ctrando.locations import scriptmanager


def _default_boss_load_finder(obj_id: int) -> bru.CommandHookLocator:
    return bru.CommandHookLocator(obj_id, FID.STARTUP, [0x83])


def _default_coordinate_finder(obj_id: int) -> bru.HookLocator:

    def find_coord(script: LocationEvent) -> int:
        pos, _ = script.find_command(
            [0x8B, 0x8D],
            script.get_function_start(obj_id, FID.STARTUP)
        )
        return pos

    return find_coord


def _strip_static_animations(
        script: scriptmanager.LocationEvent,
        start_pos: int,
        end_pos: int
):

    while True:
        start_pos, cmd = script.find_command_opt([0xAC], start_pos, end_pos)
        if start_pos is None:
            break

        script.data[start_pos + 1] = 0
        start_pos += len(cmd)

def assign_cathedral_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.MANORIA_COMMAND
    script = script_manager[loc_id]
    boss_obj = 0xA

    # Vanilla script does a vector move while the object is hidden.
    # We remove the vector move and alter the coordinates to the approximate destination.
    last_coord_finder = bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x8B])
    pos = last_coord_finder(script)
    script.replace_command_at_pos(pos, EC.set_object_coordinates_tile(0x8, 0xB))

    pos, _ = script.find_command([0x92], pos)
    script.delete_commands(pos, 1)

    bru.assign_boss_to_one_spot_location_script(
        script, boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83]),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_0,
                                               [EC.return_cmd()]),
        last_coord_finder=last_coord_finder
    )


def assign_heckran_cave_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.HECKRAN_CAVE_BOSS
    boss_obj = 0xA  # 0xC in vanilla

    battle_x_px, battle_y_px = 0x340, 0x1A1

    script = script_manager[loc_id]
    pos, end = script.get_function_bounds(boss_obj, FID.TOUCH)
    _strip_static_animations(script, pos, end)

    bru.assign_boss_to_one_spot_location_script(
        script, boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83]),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ACTIVATE, [EC.return_cmd()]),
        last_coord_finder=None,
        battle_x_px=battle_x_px, battle_y_px=battle_y_px
    )



def assign_denadoro_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE
    boss_obj = 0x14

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83]),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_1, [EC.return_cmd()]),
        battle_x_px=0x80,
        battle_y_px=0xFC,
        # last_coord_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x8D])
    )


def assign_reptite_lair_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.REPTITE_LAIR_AZALA_ROOM
    boss_obj = 9

    # Last
    # last_tile_x, last_tile_y = 0x37, 0xC
    # last_px_x, last_px_y = bru.tile_to_pixel_coords(last_tile_x, last_tile_y)
    last_px_x, last_px_y = 0x373, 0xC5

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83]),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_1, [EC.return_cmd()]),
        battle_x_px=last_px_x,
        battle_y_px=last_px_y
    )


def assign_magus_castle_flea_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.MAGUS_CASTLE_FLEA
    boss_obj = 0xC

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83, 0x83]),
        show_pos_finder=bru.CommandHookLocator(
            boss_obj, FID.STARTUP,[EC.set_byte(0x7F020C)]
        ),
        last_coord_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x8B, 0x8B])
    )


def assign_magus_castle_slash_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.MAGUS_CASTLE_SLASH
    boss_obj = 0xB

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x83]),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ACTIVATE, [EC.play_sound(0x8D)]),
        last_coord_finder=bru.CommandHookLocator(boss_obj, FID.STARTUP, [0x8B])
    )


# Skip Ozzie's fort for now because those are being counted as midbosses (?)

def assign_kings_trial_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.KINGS_TRIAL
    boss_obj = 0xD

    # The boss is so far to the left that we will need to manipulate coords

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_1,
                                               [EC.return_cmd()]),
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_giants_claw_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.GIANTS_CLAW_TYRANO
    boss_obj = 9

    enemy_ids = [part.enemy_id for part in boss.parts]
    if ctenums.EnemyID.RUST_TYRANO in enemy_ids:
        return

    # Always do the copy as though the body is dead
    script = script_manager[loc_id]
    pos = script.find_exact_command(EC.if_flag(memory.Flags.GIANTS_CLAW_BOSS_DEFEATED),
                                    script.get_function_start(0, FID.ACTIVATE))
    script.delete_commands(pos, 1)

    bru.assign_boss_to_one_spot_location_script(
        script, boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=None,
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_tyrano_lair_midboss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.TYRANO_LAIR_NIZBEL
    boss_obj = 8

    battle_x_px, battle_y_px = bru.tile_to_pixel_coords(7, 0xD)
    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            boss_obj, FID.ARBITRARY_0, [EC.return_cmd()]
        ),
        last_coord_finder=None,
        battle_x_px=battle_x_px, battle_y_px=battle_y_px
    )


def assign_zeal_palace_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.ZEAL_PALACE_THRONE_NIGHT
    boss_obj = 0xA

    battle_x_px, battle_y_px = 0x180, 0xAA  # Experimentally determined b/c of vectormove
    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_1,
                                               [EC.play_sound(0x8D)]),
        last_coord_finder=None,
        battle_x_px=battle_x_px,  # Check these.
        battle_y_px=battle_y_px
    )


def assign_epoch_reborn_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.REBORN_EPOCH
    boss_obj = 0xA

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=None,
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_blackbird_left_wing_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACKBIRD_LEFT_WING
    boss_obj = 0x17

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_0,
                                               [EC.play_song(0x29)]),
        last_coord_finder=bru.CommandHookLocator(boss_obj, FID.ARBITRARY_0,
                                                 [0x8B])
    )


def get_base_alt_slots(
        boss_part: bosstypes.BossPart
) -> tuple[int, int]:
    base_slot = boss_part.slot
    base_id = boss_part.enemy_id

    alt_slot = get_twin_slot(boss_part)

    return tuple(sorted([base_slot, alt_slot]))


def get_twin_slot(
        boss_part: bosstypes.BossPart
):
    base_slot = boss_part.slot
    base_id = boss_part.enemy_id

    # Usually base slot determines the alt slot that works.
    if base_slot == 3:
        alt_slot = 7
    elif base_slot == 6:
        alt_slot = 3
    elif base_slot == 7:
        alt_slot = 9
    else:
        alt_slot = 7

    # But it doesn't always work.
    if base_id == ctenums.EnemyID.GOLEM_BOSS:
        alt_slot = 8
    elif base_id == ctenums.EnemyID.GOLEM:
        alt_slot = 6
    elif base_id in (ctenums.EnemyID.NIZBEL, ctenums.EnemyID.NIZBEL_II,
                     ctenums.EnemyID.RUST_TYRANO):
        alt_slot = 6
    elif base_id == ctenums.EnemyID.ZEAL:
        alt_slot = 3

    return alt_slot


def assign_twin_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.OCEAN_PALACE_REGAL_ANTECHAMBER

    if len(boss.parts) !=2 :
        raise ValueError

    main_part = boss.parts[0]
    alt_part = boss.parts[1]
    part1_locator = _default_boss_load_finder(0xF)
    part2_locator = _default_boss_load_finder(0x10)

    part1_load = EC.load_enemy(main_part.enemy_id, main_part.slot)
    part2_load = EC.load_enemy(alt_part.enemy_id, alt_part.slot)

    script = script_manager[loc_id]
    pos = part1_locator(script)
    script.replace_command_at_pos(pos, part1_load)

    pos = part2_locator(script)
    script.replace_command_at_pos(pos, part2_load)



@dataclasses.dataclass
class BossObjectData:
    obj_id: int
    load_index: int = 0
    coord_index: int = 0



def update_multi_part_objects(
        script: LocationEvent,
        boss: bosstypes.BossScheme,
        script_obj_data: list[BossObjectData],
        first_x_px: int,
        first_y_px: int,
        copy_obj_ind: int = -1
) -> list[int]:
    """
    Adds ore removes objects as needed to assign a boss to the script.
    If new objects are needed, they are a copy of the object of script_obj_data
    with index copy_obj_ind.
    """

    num_repl_parts = min(len(script_obj_data), len(boss.parts))
    force_pixel_coords = not bru.can_use_tile_coords(first_x_px, first_y_px, boss)

    for ind, part in enumerate(boss.parts[0:num_repl_parts]):
        obj_data = script_obj_data[ind]
        bru.update_boss_object_load(script, part, obj_data.obj_id, obj_data.load_index)
        bru.update_boss_object_coordinates(
            script, part, first_x_px, first_y_px, obj_data.obj_id, FID.STARTUP,
            command_index=obj_data.coord_index, force_pixel_coords=force_pixel_coords
        )

    remaining_boss_objs = sorted(script_obj_data[num_repl_parts:],
                                 key=lambda x: x.obj_id,
                                 reverse=True)
    for boss_obj in remaining_boss_objs:
        script.remove_object(boss_obj.obj_id)

    remaining_scheme_parts = boss.parts[num_repl_parts:]
    copy_data = script_obj_data[copy_obj_ind]
    ret_ids: list[int] = []
    for part in remaining_scheme_parts:
        new_obj_id = script.append_copy_object(copy_data.obj_id)
        ret_ids.append(new_obj_id)
        bru.update_boss_object_load(script, part, new_obj_id, copy_data.load_index)
        bru.update_boss_object_coordinates(
            script, part, first_x_px, first_y_px, new_obj_id,
            command_index=copy_data.coord_index, force_pixel_coords=force_pixel_coords
        )

    return ret_ids


def assign_zenan_bridge_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.ZENAN_BRIDGE_BOSS
    script = script_manager[loc_id]

    first_x_px, first_y_px = 0xE8, 0x78
    main_id = boss.parts[0].enemy_id
    if main_id not in (ctenums.EnemyID.ZOMBOR_TOP, ctenums.EnemyID.RETINITE_EYE):
        first_y_px += 0x20

    boss_copy = bosstypes.BossScheme(*boss.parts)
    boss_copy.reorder_horiz(left=False)
    boss = boss_copy

    boss_obj_data = [BossObjectData(0xB, 1, 1), BossObjectData(0xC, 1, 1)]
    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, first_x_px, first_y_px
    )

    if new_objs:
        new_show_cmds = EF()
        for obj_id in new_objs:
            new_show_cmds.add(EC.call_obj_function(obj_id, FID.TOUCH, 6, FS.CONT))
        new_show_cmds.add(EC.generic_command(0xE7, 2, 1))

        pos = script.find_exact_command(
            EC.call_obj_function(0xB, FID.TOUCH, 6, FS.CONT),
            script.get_function_start(1, FID.STARTUP)
        )

        # This is tricky.
        #  - The skeletons and Ozzie need to be gone before the parts show up.
        #  - Ozzie can be force removed.
        #  - The skeletons are doing some weird palette stuff that will continue
        #    if they are interrupted.
        # The only solution is to give a little extra pause to make sure the skeletons
        # are all gone.
        new_block = (
            EF().add(EC.remove_object(0xA))  # Force removed ozzie.
            .add(EC.pause(1))  # Wait for skeletons to finish.  Not precise.
        )
        script.insert_commands(new_block.get_bytearray(), pos)

        find_cmd = EC.call_obj_function(0xC, FID.TOUCH, 6, FS.CONT)
        pos = script.find_exact_command(find_cmd) + len(find_cmd)
        script.insert_commands(new_show_cmds.get_bytearray(), pos)


def assign_beast_cave_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BEAST_NEST

    if boss.parts[0].enemy_id == ctenums.EnemyID.MUD_IMP:
        return

    script = script_manager[loc_id]

    # Remove Beasts
    script.remove_object(0xC)
    script.remove_object(0xB)

    # Treat this like a one-spot with just the Mud Imp in 0xA
    boss_obj = 0xA
    pixel_x, pixel_y = bru.tile_to_pixel_coords(0x7, 0x6)
    bru.assign_boss_to_one_spot_location_script(
        script, boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(boss_obj, FID.ACTIVATE, [EC.return_cmd()]),
        battle_x_px=pixel_x, battle_y_px=pixel_y
    )


def assign_death_peak_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.DEATH_PEAK_GUARDIAN_SPAWN
    script = script_manager[loc_id]

    first_x_px, first_y_px = 0x78, 0xD0
    boss_obj_data = [
        BossObjectData(0x9),  # Shell
        BossObjectData(0xA),  # Head
    ]

    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, first_x_px, first_y_px
    )

    if new_objs:
        new_cmds = EF()
        for obj_id in new_objs:
            new_cmds.add(
                EC.call_obj_function(obj_id, FID.ARBITRARY_0, 3, FS.CONT)
            )

        pos, _ = script.find_command(
            [0xD9], script.get_function_start(8, FID.ACTIVATE)
        )
        script.insert_commands(new_cmds.get_bytearray(), pos)

    for loc_id in (ctenums.LocID.DEATH_PEAK_CAVE, ctenums.LocID.DEATH_PEAK_NORTHEAST_FACE):
        boss_obj_data = [BossObjectData(0x8), BossObjectData(0x9)]
        if loc_id == ctenums.LocID.DEATH_PEAK_CAVE:
            first_x_px, first_y_px = bru.tile_to_pixel_coords(0x8, 0x12)
        else:
            first_x_px, first_y_px = bru.tile_to_pixel_coords(5, 0x38)

        update_multi_part_objects(
            script_manager[loc_id], boss, boss_obj_data, first_x_px, first_y_px
        )


def _enemy_floats(enemy_id: ctenums.EnemyID) -> bool:
    return enemy_id in (
        ctenums.EnemyID.TERRA_MUTANT_BOTTOM, ctenums.EnemyID.TERRA_MUTANT_HEAD,
        ctenums.EnemyID.GIGA_MUTANT_BOTTOM, ctenums.EnemyID.GIGA_MUTANT_HEAD,
        ctenums.EnemyID.MEGA_MUTANT_BOTTOM, ctenums.EnemyID.MEGA_MUTANT_HEAD,
        ctenums.EnemyID.GOLEM, ctenums.EnemyID.GOLEM_BOSS
    )


def assign_black_omen_mega_mutant_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACK_OMEN_1F_ENTRANCE
    first_x_px, first_y_px = 0x80, 0x80

    floats = _enemy_floats(boss.parts[0].enemy_id)

    boss_obj_data = [BossObjectData(0xB), BossObjectData(0xC)]

    script = script_manager[loc_id]
    pos = script.find_exact_command(
        EC.call_obj_function(0xC, FID.TOUCH, 6, FS.CONT),
        script.get_function_start(8, FID.ACTIVATE)
    )
    script.delete_commands(pos, 2)

    # By default object 0xC links back to object 0xB.  This is ok for mutants
    # because they have the same coords.  Remove the link for others.
    func = script.get_function(0xB, FID.ACTIVATE)
    script.set_function(0xC, FID.ACTIVATE, func)
    script.set_function(0xC, FID.TOUCH, EF())

    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data,
        first_x_px, first_y_px, copy_obj_ind=0
    )

    total_objs = [0xB, 0xC] + new_objs

    new_cmds = EF()

    for ind, (obj_id, part) in enumerate(zip(total_objs, boss.parts)):
        first_x_px, first_y_px = bru.tile_to_pixel_coords(0x3, 0x1A)
        bru.update_boss_object_coordinates(
            script, part, first_x_px, first_y_px,
            obj_id, FID.ACTIVATE, 0, False
        )

        first_x_px, first_y_px = 0x81, 0x1F0
        bru.update_boss_object_coordinates(
            script, part, first_x_px, first_y_px,
            obj_id, FID.ACTIVATE, 1, True
        )

        func_sync = FS.HALT if ind == len(boss.parts) - 1 else FS.CONT
        new_cmds.add(EC.call_obj_function(obj_id, FID.TOUCH, 6, func_sync))

    pos = script.find_exact_command(EC.play_sound(0x78),
                                    script.get_function_start(0x8, FID.ACTIVATE)) + 2
    pos = script.find_exact_command(EC.play_sound(0x78), pos)
    script.insert_commands(new_cmds.get_bytearray(), pos)


def assign_black_omen_giga_mutant_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACK_OMEN_GIGA_MUTANT
    boss_obj_data = [BossObjectData(0xE), BossObjectData(0xF)]
    script = script_manager[loc_id]
    first_x_px, first_y_px = 0x280, 0x1B0

    pos = script.find_exact_command(
        EC.call_obj_function(0xF, FID.TOUCH, 3, FS.CONT)
    )
    script.delete_commands(pos, 2)

    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, first_x_px, first_y_px
    )

    total_objs = [0xE, 0xF] + new_objs
    total_objs = total_objs[0:len(boss.parts)]

    new_cmds = EF()
    for ind, obj_id in enumerate(total_objs):
        func_sync = FS.HALT if ind == len(boss.parts) - 1 else FS.CONT
        new_cmds.add(EC.call_obj_function(obj_id, FID.TOUCH, 3, func_sync))

    pos = script.find_exact_command(
        EC.call_obj_function(0xD, FID.ARBITRARY_0, 3, FS.CONT),
        script.get_function_start(0xA, FID.ACTIVATE)
    )
    pos += len(get_command(script.data, pos))
    script.insert_commands(new_cmds.get_bytearray(), pos)


def assign_black_omen_terra_mutant_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACK_OMEN_TERRA_MUTANT
    script = script_manager[loc_id]

    # 0x10 has logic for starting the fight, so make sure it stays around
    boss_obj_data = [BossObjectData(0x10), BossObjectData(0xF)]

    new_objs = update_multi_part_objects(script, boss, boss_obj_data, 0x7F, 0x7F)

    new_cmds_a0 = EF()
    new_cmds_a1 = EF()
    new_remove = EF()
    for obj_id in new_objs:
        new_cmds_a0.add(EC.call_obj_function(obj_id, FID.ARBITRARY_0, 1, FS.CONT))
        new_cmds_a1.add(EC.call_obj_function(obj_id, FID.ARBITRARY_1, 1, FS.CONT))
        (
            new_remove
            .add(EC.disable_script_processing(obj_id))
            .add(EC.remove_object(obj_id))
        )

    if new_objs:
        find_cmd = EC.if_flag(memory.Flags.TERRA_MUTANT_DEFEATED)
        pos = script.find_exact_command(find_cmd) + len(find_cmd)

        script.insert_commands(new_remove.get_bytearray(), pos)

        find_cmd = EC.call_obj_function(0xF, FID.ARBITRARY_0, 1, FS.CONT)
        pos = script.find_exact_command(find_cmd, script.get_function_start(8, FID.TOUCH))
        pos += len(find_cmd)
        script.insert_commands(new_cmds_a0.get_bytearray(), pos)

        find_cmd = EC.call_obj_function(0xF, FID.ARBITRARY_1, 2, FS.CONT)
        pos = script.find_exact_command(find_cmd, pos)
        pos += len(find_cmd)
        script.insert_commands(new_cmds_a1.get_bytearray(), pos)

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.LESS_THAN, 2),
        script.get_function_start(8, FID.TOUCH)
    )
    script.replace_jump_cmd(
        pos, EC.if_mem_op_value(0x7F0210, OP.LESS_THAN, len(boss.parts)),
    )

    pos = script.find_exact_command(
        EC.if_mem_op_value(0x7F0210, OP.LESS_THAN, 4),
        script.get_function_start(8, FID.TOUCH)
    )
    script.replace_jump_cmd(
        pos, EC.if_mem_op_value(0x7F0210, OP.LESS_THAN, 2*len(boss.parts)),
    )


def assign_black_omen_elder_spawn_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACK_OMEN_ELDER_SPAWN
    script = script_manager[loc_id]
    boss_obj_data = [BossObjectData(0x8), BossObjectData(0x9)]

    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, 0xFF, 0xFF
    )

    boss_objs = ([8, 9] + new_objs)[0:len(boss.parts)]
    for ind, obj_id in enumerate(boss_objs):
        x_px, y_px = bru.tile_to_pixel_coords(0x1F, 2)
        bru.update_boss_object_coordinates(
            script, boss.parts[ind], x_px, y_px,
            obj_id, FID.ACTIVATE, command_index=0
        )
        x_px, y_px = 0x188, 0xC0
        bru.update_boss_object_coordinates(
            script, boss.parts[ind], x_px, y_px,
            obj_id, FID.ACTIVATE, command_index=1
        )

    new_cmds = EF()
    for obj_id in new_objs:
        new_cmds.add(EC.call_obj_function(obj_id, FID.TOUCH, 6, FS.CONT))

    pos = script.find_exact_command(EC.play_sound(0xFF))
    script.insert_commands(new_cmds.get_bytearray(), pos)


def assign_sunken_desert_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    # Treat this one like a one-part.
    loc_id = ctenums.LocID.SUNKEN_DESERT_DEVOURER
    script = script_manager[loc_id]

    if boss.parts[0].enemy_id in (ctenums.EnemyID.RETINITE_EYE,
                                  ctenums.EnemyID.RETINITE_TOP,
                                  ctenums.EnemyID.RETINITE_BOTTOM):
        return

    # Remove the 0xF (Bottom) Object which rises up  instead make copies of 0xE which fades in.
    script.remove_object(0xF)

    # After this is deleted, 0x10 (Bottom) drops down to 0xF.
    # The eye is still in 0xE, and this is the part we copy for new parts.
    boss_obj_data = [BossObjectData(0xF), BossObjectData(0xE)]  # Shifted up

    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, 0xCC0, 0xCC0,
    )

    if len(boss.parts) == 1:
        total_objs = [0xE]
    else:
        total_objs = [0xF, 0xE] + new_objs

    base_coords: dict[FID, tuple[int, int]] = {
        FID.ARBITRARY_0: (0x9, 0xD),
        FID.ARBITRARY_1: (0xB, 0x19),
        FID.ARBITRARY_2: (0x12, 0xB),
        FID.ARBITRARY_3: (0x16, 0x18)
    }

    # Real coord setting happens in the Arb0-Arb3, which get called after triggering
    # the battle.
    for func_id, (x_tile, y_tile) in base_coords.items():
        for obj_id, part in zip(total_objs[1:], boss.parts[1:]):
            x_px, y_px = bru.tile_to_pixel_coords(x_tile, y_tile)
            bru.update_boss_object_coordinates(
                script, part, x_px, y_px, obj_id,
                func_id,
            )

    main_obj = total_objs[0]
    for func_id in range(FID.ARBITRARY_0, FID.ARBITRARY_4):
        new_cmds = EF()
        for ind, obj_id in enumerate(total_objs[1:]):
            func_sync = FS.HALT if ind == len(total_objs) - 1 else FS.CONT
            new_cmds.add(EC.call_obj_function(obj_id, func_id, 6, func_sync))
        # The function of the removed object had the stop shake command.  Add it in.
        new_cmds.add(EC.generic_command(0xF4, 0x00))

        pos = script.get_function_start(main_obj, func_id+5)
        pos = script.find_exact_command(EC.generic_command(0x88, 0x00), pos)
        script.insert_commands(new_cmds.get_bytearray(), pos)



def assign_sun_palace_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.SUN_PALACE
    script = script_manager[loc_id]

    pos = script.find_exact_command(EC.play_animation(1),
                                    script.get_function_start(0xB, FID.ARBITRARY_1)) + 2
    del_end = script.find_exact_command(EC.play_animation(1), pos)
    script.delete_commands_range(pos, del_end)

    first_x, first_y = 0x100, 0x1FF
    boss_obj_data = [
        BossObjectData(0xB, 0, 1), BossObjectData(0xC, 0, 1), BossObjectData(0xD, 0, 1),
        BossObjectData(0xE, 0, 1), BossObjectData(0xF, 0, 1), BossObjectData(0x10, 0, 2),
    ]

    # Moonstone object comes after the boss parts.
    # Deleting will cause problems with finding the item, so dummy them out instead.
    for data in boss_obj_data[len(boss.parts):]:
        script.dummy_object_out(data.obj_id)
    boss_obj_data = boss_obj_data[0:len(boss.parts)]

    new_objs = update_multi_part_objects(script, boss, boss_obj_data, first_x, first_y)

    total_objs = [data.obj_id for data in boss_obj_data] + new_objs
    total_objs = total_objs[0: len(boss.parts)]

    new_cmds = EF()
    for ind, obj_id in enumerate(total_objs):
        if ind == 0:
            continue
        func_sync = FS.HALT if ind == len(total_objs) - 1 else FS.SYNC
        new_cmds.add(EC.call_obj_function(obj_id, FID.ACTIVATE, 1, func_sync))
        new_cmds.add(EC.pause(0.063))

    pos = script.find_exact_command(EC.play_animation(1),
                                    script.get_function_start(0xB, FID.ARBITRARY_1)) + 2
    script.insert_commands(new_cmds.get_bytearray(), pos)

    if new_objs:
        new_cmds = EF()
        for obj_id in new_objs:
            new_cmds.add(EC.remove_object(obj_id))

        pos = script.find_exact_command(EC.remove_object(0x8)) + 2
        script.insert_commands(new_cmds.get_bytearray(), pos)



def assign_arris_dome_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    main_id = boss.parts[0].enemy_id
    if main_id in (ctenums.EnemyID.GUARDIAN, ctenums.EnemyID.GUARDIAN_BIT):
        return

    loc_id = ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER
    script = script_manager[loc_id]

    # Copy L1 and L3 (needed?) tiles over guardian's body
    copy_cmd = EC.copy_tiles(
        3, 0x11, 0xC, 0x1C, 3, 2,
        copy_l1=True, copy_l3=True, copy_props=True,
        unk_0x10=True, unk_0x20=True, wait_vblank=True
    )
    pos = script.get_function_start(0, FID.ACTIVATE)
    script.insert_commands(copy_cmd.to_bytearray(), pos)

    for obj_id in (0xB, 0xC, 0xD):
        # Make all objects shown at the start
        pos = script.get_function_start(obj_id, FID.STARTUP)
        pos = script.find_exact_command(EC.set_own_drawing_status(False), pos)
        script.delete_commands(pos, 1)

        # Remove the move command from the bits
        # Update: No need because we don't need to call this function.  We remove the calls below.
        # if obj_id != 0xB:
        #     pos = script.get_function_start(obj_id, FID.ARBITRARY_0)
        #     pos, _ = script.find_command([0x96], pos)
        #     script.delete_commands(pos, 1)

    pos = script.find_exact_command(
        EC.call_obj_function(0xB, FID.ARBITRARY_0, 3, FS.HALT),
        script.get_function_start(0x9, FID.ACTIVATE)
    )
    script.delete_commands(pos, 3)

    boss_obj_data = [BossObjectData(0xB), BossObjectData(0xC), BossObjectData(0xD)]
    update_multi_part_objects(script, boss, boss_obj_data, 0x80, 0xA8)


def assign_geno_dome_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.GENO_DOME_MAINFRAME
    script = script_manager[loc_id]

    main_id = boss.parts[0].enemy_id
    if main_id in (ctenums.EnemyID.MOTHERBRAIN, ctenums.EnemyID.DISPLAY):
        return

    pos = script.find_exact_command(
        EC.call_obj_function(0x23, FID.ACTIVATE, 1, FS.SYNC)
    )
    script.delete_commands(pos, 2)

    dummy_objs = [0x23, 0x21, 0x20, 0x1F]  # Display and mother brain shoulders
    for obj_id in dummy_objs:
        script.dummy_object_out(obj_id)

    boss_obj_data = [BossObjectData(0x22)]
    new_objs = update_multi_part_objects(
        script, boss, boss_obj_data, 0xA0, 0x6F
    )

    new_cmds = EF()
    hide_cmds = EF()
    total_objs = [0x22] + new_objs
    for ind, obj_id in enumerate(total_objs):
        func_sync = FS.HALT if ind == len(total_objs) - 1 else FS.SYNC
        new_cmds.add(EC.call_obj_function(obj_id, FID.ACTIVATE, 1, func_sync))

        if obj_id != 0x22:
            hide_cmds.add(EC.set_object_drawing_status(obj_id, False))


        pos = script.find_exact_command(EC.remove_object(0x22), script.get_object_start(obj_id))
        script.replace_command_at_pos(pos, EC.remove_object(obj_id))

    pos = script.find_exact_command(EC.play_sound(0x89), script.get_object_start(0x1E)) + 2
    script.insert_commands(new_cmds.get_bytearray(), pos)

    pos = script.find_exact_command(EC.set_object_drawing_status(0x22, False), pos)
    script.insert_commands(hide_cmds.get_bytearray(), pos)


def assign_mt_woe_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.MT_WOE_SUMMIT
    script = script_manager[loc_id]

    copytiles = EC.copy_tiles(2, 1, 0xD, 9, 0x2, 0x11,
                              copy_l1=True, copy_l2=True, copy_l3=True,
                              copy_props=True, wait_vblank=True)
    pos = script.get_function_start(0, FID.ACTIVATE)
    script.insert_commands(copytiles.to_bytearray(), pos)

    boss_obj_data = [BossObjectData(0xA), BossObjectData(0xB), BossObjectData(0xC)]
    update_multi_part_objects(script, boss, boss_obj_data, 0x80, 0x158)

def assign_prison_catwalks_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.PRISON_CATWALKS
    script = script_manager[loc_id]

    if ctenums.EnemyID.DRAGON_TANK in (part.enemy_id for part in boss.parts):
        return

    # Clean up the tank objects:  Replace move to coord commands with vector moves
    boss_obj_data = [BossObjectData(0xD, 1, 1), BossObjectData(0xE, 1, 1), BossObjectData(0xF,1, 1)]
    for obj_data in boss_obj_data:
        script.set_function(
             obj_data.obj_id, FID.ARBITRARY_0,
             EF()
             .add(EC.set_own_drawing_status(True))
             .add(EC.vector_move(0, 0x4A, False))
             .add(EC.return_cmd())
        )

        drop_fid = FID.ARBITRARY_1 if obj_data.obj_id == 0xD else FID.ARBITRARY_2
        pos, _ = script.find_command([0x96], script.get_function_start(obj_data.obj_id, drop_fid))
        script.replace_command_at_pos(pos, EC.vector_move(90, 0x50, True))

    script.set_function(0xD, FID.ARBITRARY_2,
                        EF()
                        .add(EC.set_move_speed(0x20))
                        .add(EC.move_sprite(0x8, 0x9))
                        .add(EC.return_cmd()))
    pos, _ = script.find_command([0xD8], script.get_function_start(5, FID.ARBITRARY_1))
    pos += 3
    script.insert_commands(EC.call_obj_function(0xD, FID.ARBITRARY_2, 6, FS.HALT).to_bytearray(), pos)


    # Remove call blocks for old objects
    pos = script.find_exact_command(EC.call_obj_function(0xE, FID.ARBITRARY_2, 6, FS.CONT),
                                    script.get_function_start(0x15, FID.ARBITRARY_0))
    script.delete_commands(pos, 2)

    pos = script.find_exact_command(EC.call_obj_function(0xE, FID.ARBITRARY_0, 6, FS.CONT),
                                    script.get_function_start(5, FID.ARBITRARY_1))
    script.delete_commands(pos, 3)

    first_x_px, first_y_px = 0x48, 0xA0
    first_x_px += 0x20
    first_y_px -= 0x20

    new_objs = update_multi_part_objects(script, boss, boss_obj_data, first_x_px, first_y_px)
    total_objs = [data.obj_id for data in boss_obj_data] + new_objs
    total_objs = total_objs[0: len(boss.parts)]

    enter_cmds = EF()
    drop_cmds = EF()

    # The last object (explosion) which has some important calls may have shifted.
    # Track how far up it's moved.
    if len(total_objs) < 3:
        shift = 3-len(total_objs)
    else:
        shift = 0

    for ind, obj in enumerate(total_objs):
        enter_fs = FS.HALT if ind == len(total_objs) - 1 else FS.CONT
        drop_fs = FS.CONT

        enter_cmds.add(EC.call_obj_function(obj, FID.ARBITRARY_0, 6, enter_fs))

        if obj != 0xD:
            drop_cmds.add(EC.call_obj_function(obj, FID.ARBITRARY_1, 6, drop_fs))

    pos = script.find_exact_command(
        EC.call_obj_function(0xD, FID.ARBITRARY_1, 6, FS.CONT),
        script.get_function_start(0x15-shift, FID.ARBITRARY_0)
    ) + 3
    script.insert_commands(drop_cmds.get_bytearray(), pos)

    pos = script.find_exact_command(
        EC.generic_command(0xF4, 0x00),
        script.get_function_start(5, FID.ARBITRARY_1)
    )
    script.insert_commands(enter_cmds.get_bytearray(), pos)


def assign_factory_ruins_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER
    script = script_manager[loc_id]

    if ctenums.EnemyID.R_SERIES in (part.enemy_id for part in boss.parts):
        return

    boss_obj_data = [BossObjectData(ind, 0, 0) for ind in range(0xA, 0x10)]
    for ind, data in enumerate(boss_obj_data):
        pos = script.get_function_start(data.obj_id, FID.ARBITRARY_0)
        if script.data[pos] == 0xAD:
            script.delete_commands(pos, 1)
        pos, _ = script.find_command([EC.move_sprite(0,0).command], pos)
        script.replace_command_at_pos(pos, EC.vector_move(90, 0x18, False))
        script.set_function(data.obj_id, FID.ARBITRARY_1, EF().add(EC.return_cmd()))
        script.set_function(data.obj_id, FID.ARBITRARY_2, EF())
        script.set_function(data.obj_id, FID.ARBITRARY_3, EF())
        script.set_function(data.obj_id, FID.ARBITRARY_4, EF())
        script.set_function(data.obj_id, FID.ARBITRARY_5, EF())

    update_multi_part_objects(script, boss, boss_obj_data, 0xA0, 0x1D8)


def assign_ozzies_fort_super_slash_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.OZZIES_FORT_SUPER_SLASH
    boss_obj = 0x9

    if boss.parts[0].slot == 3:
        boss.parts[0].slot = 6

    boss.parts[0].slot = 5

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            boss_obj, FID.ACTIVATE, [0xD8]
        ),
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_ozzies_fort_flea_plus_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.OZZIES_FORT_FLEA_PLUS
    boss_obj = 0x9

    if boss.parts[0].slot == 3:
        boss.parts[0].slot = 6

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            boss_obj, FID.ACTIVATE, [0xD8]
        ),
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_sewers_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.SEWERS_B1
    boss_obj = 0x24

    if boss.parts[0].slot == 6:
        boss.parts[0].slot = 3

    script = script_manager[loc_id]
    pos = script.find_exact_command(
        EC.static_animation(0),
        script.get_object_start(boss_obj)
    )
    script.delete_commands(pos, 1)

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            0x23, FID.ACTIVATE, [0xD8]
        ),
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )

    func = script_manager[loc_id].get_function(boss_obj, FID.STARTUP)


def assign_gato_spot_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.GATO_EXHIBIT
    boss_obj = 0x8

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=None,
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )

    func = script_manager[loc_id].get_function(boss_obj, FID.STARTUP)


def assign_geno_mid_boss(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.GENO_DOME_MAINFRAME
    boss_obj = 0x1D

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            0, FID.ARBITRARY_2, [0xD8]
        ),
        last_coord_finder=_default_coordinate_finder(boss_obj)
    )


def assign_ozzies_fort_final(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    script = script_manager[ctenums.LocID.OZZIES_FORT_LAST_STAND]

    if len(boss.parts) != 3:
        raise IndexError

    ozzie_obj, slash_obj, flea_obj = 8, 9, 0xA
    bru.update_boss_object_load(script, boss.parts[0], ozzie_obj)
    bru.update_boss_object_load(script, boss.parts[1], slash_obj)
    bru.update_boss_object_load(script, boss.parts[2], flea_obj)


def assign_black_omen_zeal(
        script_manager: scriptmanager.ScriptManager,
        boss: bosstypes.BossScheme,
):
    loc_id = ctenums.LocID.BLACK_OMEN_ZEAL
    boss_obj = 0x08

    bru.assign_boss_to_one_spot_location_script(
        script_manager[loc_id], boss,
        boss_load_finder=_default_boss_load_finder(boss_obj),
        show_pos_finder=bru.CommandHookLocator(
            boss_obj, FID.STARTUP, [0xD8]
        ),
        battle_x_px=0x7F,
        battle_y_px=0xAF
    )


def get_atropos_ribbon_func(
        stat_boost_str_id: int,
        temp_addr: int = 0x7F0240,
) -> EF:
    """Get an EF to give Robo's stat boost."""
    func = (
        EF()
        .add(EC.assign_mem_to_mem(0x7E26FD, temp_addr, 1))
        .add(EC.add_value_to_mem(3, temp_addr))
        .add_if(
            EC.if_mem_op_value(temp_addr, OP.GREATER_THAN, 0x10, 1, 0),
            (
                EF()
                .add(EC.assign_val_to_mem(0x10, temp_addr, 1))
            )
        )
        .add(EC.assign_mem_to_mem(temp_addr, 0x7E26FD, 1))
        .add(EC.assign_mem_to_mem(0x7E2701, temp_addr, 1))
        .add(EC.add_value_to_mem(0xA, temp_addr))
        .add_if(
            EC.if_mem_op_value(temp_addr, OP.GREATER_THAN, 0x50, 1, 0),
            (
                EF()
                .add(EC.assign_val_to_mem(0x50, temp_addr, 1))
            )
        )
        .add(EC.assign_mem_to_mem(temp_addr, 0x7E2701, 1))
        .add(EC.assign_mem_to_mem(0x7E2725, temp_addr, 1))
        .add(EC.add_value_to_mem(0xA, temp_addr))
        .add(EC.assign_mem_to_mem(temp_addr, 0x7E2725, 1))
        .add(EC.set_flag(memory.Flags.HAS_ATROPOS_RIBBON_BUFF))
        .add(EC.text_box(stat_boost_str_id))

    )

    func = (
        EF().add_if(
            EC.if_not_flag(memory.Flags.HAS_ATROPOS_RIBBON_BUFF),
            func
        )
    )

    return func


# _ribbon_locators: dict[bosstypes.BossSpotID, bru.HookLocator] = {
#     bosstypes.BossSpotID.SEWERS_KRAWLIE: bru.CommandHookLocator(0x23, FID.ACTIVATE, [0xD8], True),
#     bosstypes.BossSpotID.OZZIES_FORT_FLEA_PLUS: bru.CommandHookLocator(0x9, FID.ACTIVATE, [0xD8], True),
#     bosstypes.BossSpotID.OZZIES_FORT_SUPER_SLASH: bru.CommandHookLocator(0x9, FID.ACTIVATE, [0xD8], True),
#     bosstypes.BossSpotID.MILLENNIAL_FAIR_GATO: bru.CommandHookLocator(
#         0, FID.STARTUP, [EC.call_obj_function(8, FID.ARBITRARY_2, 6, FS.HALT)]
#     ),
#     bosstypes.BossSpotID.EPOCH_REBORN: bru.CommandHookLocator(0x9, FID.STARTUP, [0xD8], True)
# }
# _ribbon_loc_id: dict[bosstypes.BossSpotID, ctenums.LocID] = {
#     bosstypes.BossSpotID.SEWERS_KRAWLIE: ctenums.LocID.SEWERS_B1,
#     bosstypes.BossSpotID.OZZIES_FORT_FLEA_PLUS: ctenums.LocID.OZZIES_FORT_FLEA_PLUS,
#     bosstypes.BossSpotID.OZZIES_FORT_SUPER_SLASH: ctenums.LocID.OZZIES_FORT_SUPER_SLASH,
#     bosstypes.BossSpotID.MILLENNIAL_FAIR_GATO: ctenums.LocID.GATO_EXHIBIT,
#     bosstypes.BossSpotID.EPOCH_REBORN: ctenums.LocID.REBORN_EPOCH
# }


def remove_ribbon_from_geno_dome(
        script_manager: scriptmanager.ScriptManager
):
    """Remove existing geno dome ribbon buff"""
    geno_script = script_manager[ctenums.LocID.GENO_DOME_MAINFRAME]
    pos, _ = geno_script.find_command([0xBB],
                                      geno_script.get_function_start(0x1D, FID.ARBITRARY_1))
    end = geno_script.find_exact_command(EC.set_flag(memory.Flags.GENO_DOME_ATROPOS_DEFEATED), pos)
    geno_script.delete_commands_range(pos, end)


def add_ribbon_buff_to_spot(
        script_manager: scriptmanager.ScriptManager, spot: bosstypes.BossSpotID
):
    if spot == bosstypes.BossSpotID.GENO_DOME_MID:
        return

    locator_dict = oty.get_boss_locator_dict()
    if spot not in locator_dict:
        raise KeyError

    hook_data = locator_dict[spot](script_manager)
    script, pos = hook_data.script, hook_data.pos
    str_id = script.add_py_string(
        "Atropos' Ribbon ups Robo's Speed{linebreak+0}"
        "by 3 and Magic Defense by 10.{null}"
    )
    func = get_atropos_ribbon_func(str_id)
    script.insert_commands(func.get_bytearray(), pos)


def add_r_series_boss_defeat_check(
        boss_assign_dict: dict[bosstypes.BossSpotID, bosstypes.BossID],
        script_manager: scriptmanager.ScriptManager,
        temp_addr: int = 0x7F0312
):
    """
    Increment the boss counter for R-Series.  Other bosses increment in assembly.
    """
    # Should all bosses get incremented this way?

    spot_locator_dict = oty.get_boss_locator_dict()

    for spot_id, boss_id in boss_assign_dict.items():
        if boss_id == bosstypes.BossID.R_SERIES:
            hook_data = spot_locator_dict[spot_id](script_manager)
            hook_data.script.insert_commands(
                EF()
                .add(EC.assign_mem_to_mem(memory.Memory.BOSSES_DEFEATED, temp_addr, 1))
                .add(EC.increment_mem(temp_addr))
                .add(EC.assign_mem_to_mem(temp_addr, memory.Memory.BOSSES_DEFEATED,1))
                .get_bytearray(), hook_data.pos
            )


def write_blackbird_peek(
        script_manager: scriptmanager.ScriptManager,
        epoch_boss: bosstypes.BossID,
        blackbird_wing_boss: bosstypes.BossID
):
    script = script_manager[ctenums.LocID.BLACKBIRD_HANGAR]

    epoch_boss_part = bosstypes.get_default_scheme(epoch_boss).parts[0]
    wing_boss_part = bosstypes.get_default_scheme(blackbird_wing_boss).parts[0]


    epoch_boss_slot = 3
    wing_main_slot, wing_alt_slot = get_base_alt_slots(wing_boss_part)
    wing_boss_slot = wing_alt_slot

    for obj_id in (6, 8, 9):
        pos = script.get_object_start(obj_id)
        script.delete_commands(pos)

    pos = script.get_object_start(7)
    new_cmd = EC.load_enemy(wing_boss_part.enemy_id, wing_boss_slot, False)
    script.replace_command_at_pos(pos, new_cmd)

    pos = script.get_object_start(0xA)
    script.replace_command_at_pos(
        pos, EC.load_enemy(epoch_boss_part.enemy_id, epoch_boss_slot, False)
    )




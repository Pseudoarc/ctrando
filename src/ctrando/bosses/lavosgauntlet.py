"""Module for Customizing the Lavos Gauntlet"""
from collections.abc import Iterable
import copy
import dataclasses
import typing

from ctrando.attacks import animationscript, animationcommands as ac, enemytech
from ctrando.bosses import bosstypes as bty, bossrandoutils as bru, lavosgauntlettypes as lgt
from ctrando.common import ctenums, ctrom, memory

from ctrando.enemydata import enemystats
from ctrando.enemyai import enemyaimanager, enemyaitypes

from ctrando.locations import locationmap, locationtypes, scriptmanager
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import LocationEvent, FunctionID as FID



# Obj 08 - Control Object
# - Goes away when gauntlet counter > 0
# - On Lavos Status == 2 can initiate a battle
# - Arb0, Arb1 are for ending the battle
# - Arb2 advances the gauntlet.  Gauntlet begins in Obj 00, Arb0
#   changed the script.
# Obj 0A - Control Object
# - Visible on first entry, hides for the rest of the gauntlet
# Obj 0B to the end - Lavos Objects
# - Obj1C is the final lavos
# - In general Lavos objects need to:
#   - set their coordinates (base head 7f, 8f),
#   - hide themselves if it's not their turn, and set 0x7F0214 to 1 on touch.
#   - Head is static, rest are not

# Strategy
# - Keep Gauntlet Counter as 0 to start and 10 to end to avoid editing other scripts
# - Modify Obj00, Arb0 to set the first attack mode
# - Modify Obj00,


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


def make_gauntlet_map_header() -> locationmap.LocationMapHeader:
    header = locationmap.LocationMapHeader().set_properties(
        layer_1_height=0x10, layer_1_width=0x10,
        layer_2_height=0x10, layer_2_width=0x10,
        layer_3_height=0x10, layer_3_width=0x10,
        layer_1_scrolling=0, layer_2_scrolling=0, layer_3_scrolling=0,
        draw_layer_3=True,
        use_layer_1_mainscreen=True,
        use_layer_2_mainscreen=True,
        use_layer_3_mainscreen=True,
        use_sprites_mainscreen=True,
        use_layer_1_subscreen=False, use_layer_2_subscreen=False, use_layer_3_subscreen=False,
        use_sprites_subscreen=False,
    )

    return header


@dataclasses.dataclass()
class GauntletMapData:
    loc_id: ctenums.LocID
    top: int
    left: int


def make_gauntlet_map_alt(
        ct_rom: ctrom.CTRom,
        base_location: ctenums.LocID,
        l3_tiles: bytearray,
        l3_shift_x: int = 0,
        l3_shift_y: int = 0,
):
    if l3_shift_x != 0 or l3_shift_y != 0:
        l3_rows: list[bytearray] = [
            l3_tiles[ind*0x10: ind*0x10+0x10] for ind in range(0x10)
        ]
        if l3_shift_x != 0:
            for ind, row in enumerate(l3_rows):
                l3_rows[ind] = row[-l3_shift_x:] + row[:-l3_shift_x]
        if l3_shift_y != 0:
            l3_rows = l3_rows[-l3_shift_y:] + l3_rows[:-l3_shift_y]

        l3_tiles = b''.join(l3_rows)
    ct_map = locationmap.LocationMap.get_location_map(ct_rom, base_location)
    ct_map.l3_tiles = bytearray(l3_tiles)
    ct_map.header.layer_3_height = 0x10
    ct_map.header.layer_3_width = 0x10
    ct_map.header.draw_layer_3 = True
    ct_map.header.use_layer_3_mainscreen = True
    ct_map.header.use_layer_1_subscreen = True
    ct_map.header.use_layer_2_subscreen = True
    ct_map.header.use_layer_3_subscreen = False
    ct_map.header.use_sprites_subscreen = True
    ct_map.header.enable_layer_1_subscreen_addsub = False
    ct_map.header.enable_layer_2_subscreen_addsub = False
    ct_map.header.enable_layer_3_subscreen_addsub = True
    ct_map.header.enable_sprite_subscreen_addsub = False
    ct_map.header.half_color = False
    ct_map.header.layer_3_scrolling = 0

    return ct_map


def make_gauntlet_map(
        ct_rom: ctrom.CTRom,
        gauntlet_map_data: GauntletMapData
) -> locationmap.LocationMap:
    ct_map = locationmap.LocationMap.get_location_map(ct_rom, gauntlet_map_data.loc_id)
    size = 0x10
    l1_tiles = ct_map.get_tiles(
        gauntlet_map_data.top, gauntlet_map_data.left,
        gauntlet_map_data.top + size, gauntlet_map_data.left + size,
        layer=1
    )
    l2_tiles = ct_map.get_tiles(
        gauntlet_map_data.top, gauntlet_map_data.left,
        gauntlet_map_data.top + size, gauntlet_map_data.left + size,
        layer=2
    )
    props = ct_map.get_tile_properties(
        gauntlet_map_data.top, gauntlet_map_data.left,
        gauntlet_map_data.top + size, gauntlet_map_data.left + size
    )

    # Try to move this elsewhere for re-use
    gaunlet_map = locationmap.LocationMap.get_location_map(ct_rom, ctenums.LocID.GAUNTLET_PRISON_CATWALKS)
    l3_tiles = gaunlet_map.l3_tiles
    header = make_gauntlet_map_header()

    return locationmap.LocationMap(header, l1_tiles, l2_tiles, l3_tiles, props)


def make_gauntlet_script(
        base_script: LocationEvent,
        boss_scheme: bty.BossScheme,
        boss_x_px: int,
        boss_y_px: int,
        part_fns: list[EF]
) -> LocationEvent:
    """
    Make a gaunlet script from a base script
    """
    script = copy.deepcopy(base_script)

    new_ids = bru.assign_boss_to_one_spot_location_script(
        script, boss_scheme,
        _default_boss_load_finder(1),
        None,
        # _default_coordinate_finder(1),
        None,
        boss_x_px, boss_y_px
    )
    pos, cmd = script.find_command([0x8D], script.get_object_start(1))
    script.replace_command_at_pos(
        pos, EC.set_object_coordinates_pixels(boss_x_px, boss_y_px)
    )

    obj_ids = [1] + new_ids
    assigned_ids: list[int] = []
    for obj_id, part, part_fn in zip(
            obj_ids, boss_scheme.parts, part_fns):
        pos, cmd = script.find_command(
            [EC.load_enemy(0, 0).command],
            script.get_object_start(obj_id)
        )
        pos += len(cmd)
        script.insert_commands(
            EC.generic_command(0x8E, 0x33).to_bytearray(), pos)

        script.set_function(
            obj_id, FID.ARBITRARY_0,
            part_fn
        )
        assigned_ids.append(obj_id)

    call_block = EF()
    for obj_id in assigned_ids:
        call_block.add(EC.call_obj_function(obj_id, FID.ARBITRARY_0, 4, FS.HALT))

    pos = script.find_exact_command(EC.call_obj_function(1, FID.ARBITRARY_0, 4, FS.HALT))
    script.delete_commands(pos, 1)
    script.insert_commands(call_block.get_bytearray(), pos)

    return script


def update_gaunlet_script_counter(
        script: LocationEvent,
        new_index: int
):
    find_cmd = EC.assign_val_to_mem(
        new_index, memory.Memory.LAVOS_ATTACK_MODE_COUNTER, 1)
    pos, cmd = script.find_command([find_cmd.command])
    script.replace_command_at_pos(
        pos, find_cmd
    )


def test_mod_gauntlet(
        ct_rom: ctrom.CTRom,
        script_manager: scriptmanager.ScriptManager,
        loc_data_dict: dict[ctenums.LocID, locationtypes.LocationData]
):
    base_loc_data = loc_data_dict[ctenums.LocID.GAUNTLET_PRISON_CATWALKS]
    base_map = locationmap.LocationMap.read_from_ctrom(ct_rom, base_loc_data.map_id)

    gaunlet_data = GauntletMapData(
        ctenums.LocID.SUNKEN_DESERT_DEVOURER, 0x8, 0x10
    )

    new_loc_data = locationtypes.LocationData.read_from_ctrom(ct_rom, ctenums.LocID.SUNKEN_DESERT_DEVOURER)
    new_map = make_gauntlet_map(ct_rom, gaunlet_data)
    new_loc_data.layer_3_tilechunks = base_loc_data.layer_3_tilechunks
    new_loc_data.event_id = base_loc_data.event_id
    new_loc_data.map_id = base_loc_data.map_id
    new_loc_data.left_tile_bound = 0
    new_loc_data.right_tile_bound = 0xF
    new_loc_data.top_tile_bound = 0
    new_loc_data.bottom_tile_bound = 0xE

    loc_data_dict[ctenums.LocID.GAUNTLET_PRISON_CATWALKS] = new_loc_data

    test = locationmap.LocationMapHeader(new_map.header)
    new_map.write_to_ctrom(ct_rom, base_loc_data.map_id)
    test_map = locationmap.LocationMap.read_from_ctrom(ct_rom, base_loc_data.map_id)

    script = script_manager[ctenums.LocID.GAUNTLET_PRISON_CATWALKS]
    script.remove_object(2)
    script.remove_object(2)
    dumb_part = bty.BossPart()
    bru.update_boss_object_coordinates(
        script, dumb_part, 0x80, 0x50, 1
    )
    bru.assign_boss_to_one_spot_location_script(
        script, bty.get_default_scheme(bty.BossID.ZEAL_2),
        _default_boss_load_finder(1),
        None,
        _default_coordinate_finder(1),
    )

    pass



def add_lavos_scheme(
        script: LocationEvent,
        lavos_scheme: bty.BossScheme,
        gauntlet_id: int
):
    lavos_x_px, lavos_y_px = 0x07F, 0x08F

    if not lavos_scheme.parts:
        raise ValueError

    for ind, part in enumerate(lavos_scheme.parts):
        obj_id = script.append_empty_object()
        script.set_function(
            obj_id, FID.STARTUP,
            EF()
            .add(EC.load_enemy(part.enemy_id, part.slot, is_static=(ind==0)))
            .add(EC.set_object_coordinates_pixels(lavos_x_px + part.displacement[0],
                                                  lavos_y_px + part.displacement[1]))
            .add_if(
                EC.if_mem_op_value(memory.Memory.LAVOS_ATTACK_MODE_COUNTER, OP.NOT_EQUALS, gauntlet_id+1),
                EF().add(EC.set_own_drawing_status(False))
            )
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )

        script.set_function(
            obj_id, FID.ACTIVATE,
            EF().add(EC.set_byte(0x7F0214)).add(EC.return_cmd()))

        # Hide the final boss's lavos head
        if ind == 0 and gauntlet_id == 8:
            pos, _ = script.find_command(
                [0xEE],
                script.get_function_start(8, FID.ARBITRARY_2)
            )
            script.insert_commands(
                EC.set_object_drawing_status(obj_id, False).to_bytearray(), pos
            )


def get_lavos_changeloc_cmd(
        boss_id: bty.BossID,
        loc_id: ctenums.LocID | None
) -> EC:
    if boss_id in _vanilla_gauntlet_coords:
        loc_id = _vanilla_gauntlet_correspondence[boss_id]
        x, y = _vanilla_gauntlet_coords[boss_id]
    else:
        if loc_id is None:
            raise ValueError
        data = _boss_gauntlet_data_dict[boss_id]
        x, y = data.changeloc_x, data.changeloc_y

    return EC.change_location(loc_id, x, y, unk=1, force_command_id=0xDF)


def modify_lavos_script(
        script: LocationEvent,
        gauntlet: list[bty.BossID],
        gauntlet_loc_dict: dict[bty.BossID, ctenums.LocID],
        lavos_schemes: dict[bty.BossID, bty.BossScheme]
):

    if len(gauntlet) > 10:
        gauntlet = gauntlet[:10]
    if len(gauntlet) == 0:
        return

    # Gauntlet Init Block
    # Rewrite initial gauntlet counter and the first change location
    init_gauntlet_counter = 9 - len(gauntlet)

    find_cmd = EC.assign_val_to_mem(0, memory.Memory.LAVOS_ATTACK_MODE_COUNTER, 1 )
    pos = script.find_exact_command(
        find_cmd,
        script.get_function_start(0, FID.ARBITRARY_0)
    ) + len(find_cmd)
    pos = script.find_exact_command(find_cmd, pos) + len(find_cmd)
    pos = script.find_exact_command(find_cmd, pos)
    script.replace_command_at_pos(
        pos,
        EC.assign_val_to_mem(init_gauntlet_counter, memory.Memory.LAVOS_ATTACK_MODE_COUNTER, 1)
    )

    pos, cmd = script.find_command([0xDF], pos)
    new_cmd = get_lavos_changeloc_cmd(gauntlet[0],
                                      gauntlet_loc_dict[gauntlet[0]])
    script.replace_command_at_pos(pos, new_cmd)

    # Gauntlet Next Step Block
    next_step_block = EF()
    for ind in range(0, len(gauntlet)-1):
        counter_val = init_gauntlet_counter + ind + 1
        changeloc_cmd = get_lavos_changeloc_cmd(
            gauntlet[ind+1], gauntlet_loc_dict[gauntlet[ind+1]])
        next_step_block.add_if(
            EC.if_mem_op_value(memory.Memory.LAVOS_ATTACK_MODE_COUNTER, OP.EQUALS, counter_val  ),
            EF().add(changeloc_cmd)
        )

    del_st = script.find_exact_command(
        EC.if_mem_op_value(memory.Memory.LAVOS_ATTACK_MODE_COUNTER, OP.EQUALS, 0),
        script.get_function_start(8, FID.ARBITRARY_2)
    )

    del_end = script.find_exact_command(EC.return_cmd(), del_st)
    script.delete_commands_range(del_st, del_end)
    script.insert_commands(next_step_block.get_bytearray(), del_st)

    for obj_id in reversed(range(0xB, 0x1C)):
        script.remove_object(obj_id)

    for ind, boss_id in enumerate(gauntlet):
        add_lavos_scheme(script, lavos_schemes[boss_id], init_gauntlet_counter + ind)


_vanilla_gauntlet_correspondence: dict[bty.BossID, ctenums.LocID] = {
    bty.BossID.DRAGON_TANK: ctenums.LocID.GAUNTLET_PRISON_CATWALKS,
    bty.BossID.GUARDIAN: ctenums.LocID.GAUNTLET_ARRIS_DOME_GUARDIAN,
    bty.BossID.HECKRAN: ctenums.LocID.GAUNTLET_HECKRAN_CAVE,
    bty.BossID.ZOMBOR: ctenums.LocID.GAUNTLET_ZENAN_BRIDGE,
    bty.BossID.MASA_MUNE: ctenums.LocID.GAUNTLET_CAVE_OF_MASAMUNE,
    bty.BossID.NIZBEL: ctenums.LocID.GAUNTLET_REPTITE_LAIR,
    bty.BossID.MAGUS: ctenums.LocID.GAUNTLET_MAGUS_INNER_SANCTUM,
    bty.BossID.BLACK_TYRANO: ctenums.LocID.GAUNTLET_TYRANO_LAIR,
    bty.BossID.GIGA_GAIA: ctenums.LocID.GAUNTLET_MT_WOE_SUMMIT
}

_vanilla_gauntlet_coords: dict[bty.BossID, tuple[int, int]] = {
    bty.BossID.DRAGON_TANK: (7, 7),
    bty.BossID.GUARDIAN: (7, 7),
    bty.BossID.HECKRAN: (0x17, 0x17),
    bty.BossID.ZOMBOR: (0xB, 7),
    bty.BossID.MASA_MUNE: (0x17, 7),
    bty.BossID.NIZBEL: (7, 7),
    bty.BossID.MAGUS: (7, 0xC),
    bty.BossID.BLACK_TYRANO: (7, 9),
    bty.BossID.GIGA_GAIA: (7, 7),
}
@dataclasses.dataclass()
class GauntletData:
    loc_id: ctenums.LocID
    changeloc_x: int
    changeloc_y: int
    boss_x_px: int
    boss_y_px: int
    part_functions: list[EF] = dataclasses.field(
        default_factory=list
    )


_boss_gauntlet_data_dict: dict[bty.BossID, GauntletData] = {
    bty.BossID.DALTON_PLUS: GauntletData(
        ctenums.LocID.REBORN_EPOCH, 0x07, 0x19,
        0x078, 0x198
    ),
    bty.BossID.ELDER_SPAWN: GauntletData(
        ctenums.LocID.BLACK_OMEN_ELDER_SPAWN, 0x18, 0x0C,
        0x188, 0x0C0
    ),
    bty.BossID.FLEA: GauntletData(
        ctenums.LocID.MAGUS_CASTLE_FLEA, 0x7, 0x16,
        0x78, 0x168
    ),
    bty.BossID.GIGA_MUTANT: GauntletData(
        ctenums.LocID.BLACK_OMEN_GIGA_MUTANT, 0x28, 0x1B,
        0x280, 0x1B0
    ),
    bty.BossID.GOLEM: GauntletData(
        ctenums.LocID.ZEAL_PALACE_THRONE, 0x17, 0x13,
        0x170, 0x130
    ),
    bty.BossID.GOLEM_BOSS: GauntletData(
        ctenums.LocID.BLACKBIRD_LEFT_WING, 0x14, 0x14,
        0x140, 0x140
    ),
    # bty.BossID.HECKRAN: ...
    bty.BossID.LAVOS_SPAWN: GauntletData(
        ctenums.LocID.DEATH_PEAK_GUARDIAN_SPAWN, 0xC, 0x11,
        0x0C8, 0x118
    ),
    bty.BossID.MAMMON_M: GauntletData(
        ctenums.LocID.TIME_DISTORTION_PROFANE_MACHINE, 0x08, 0x3,
        0x080, 0x03F
    ),
    bty.BossID.MAGUS_NORTH_CAPE: GauntletData(
        ctenums.LocID.NORTH_CAPE, 0x7, 0x5,
        0x80, 0x50
    ),
    # bty.BossID.MASA_MUNE: ...
    bty.BossID.MEGA_MUTANT: GauntletData(
        ctenums.LocID.BLACK_OMEN_1F_ENTRANCE, 0x8, 0x1F,
        0x81, 0x1F0
    ),
    bty.BossID.MUD_IMP: GauntletData(
        ctenums.LocID.BEAST_NEST, 0x7, 0x6,
        0x78, 0x68
    ),
    # bty.BossID.NIZBEL: ...
    bty.BossID.NIZBEL_2: GauntletData(
        ctenums.LocID.TYRANO_LAIR_NIZBEL, 0x7, 0xD,
        0x78, 0xD8
    ),
    bty.BossID.RETINITE: GauntletData(
        ctenums.LocID.SUNKEN_DESERT_DEVOURER, 0x12, 0xA,
        0x118, 0xA8
    ),
    bty.BossID.R_SERIES: GauntletData(
        ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER, 0x9, 0x23,
        0x99, 0x22F
    ),
    bty.BossID.RUST_TYRANO: GauntletData(
        ctenums.LocID.GIANTS_CLAW_TYRANO, 0x8, 0x27,
        0x80, 0x27F
    ),
    bty.BossID.SLASH_SWORD: GauntletData(
        ctenums.LocID.MAGUS_CASTLE_SLASH, 0x8, 0x24,
        0x88, 0x24F,
    ),
    bty.BossID.SON_OF_SUN: GauntletData(
        ctenums.LocID.SUN_PALACE, 0x10, 0x1F,
        0x108, 0x1FF
    ),
    bty.BossID.TERRA_MUTANT: GauntletData(
        ctenums.LocID.BLACK_OMEN_TERRA_MUTANT, 0x08, 0x08,
        0x07F, 0x07F
    ),
    bty.BossID.YAKRA: GauntletData(
        ctenums.LocID.MANORIA_COMMAND, 0x7, 0x8,
        0x078, 0x08F
    ),
    bty.BossID.YAKRA_XIII: GauntletData(
        ctenums.LocID.KINGS_TRIAL, 0x5, 0x11,
        0x58, 0x11F
    ),
    # bty.BossID.ZOMBOR: ...
    bty.BossID.MOTHER_BRAIN: GauntletData(
        ctenums.LocID.GENO_DOME_MAINFRAME, 0xA, 0x7,
        0xA0, 0x6F
    ),
    # bty.BossID.DRAGON_TANK: ...
    # bty.BossID.GIGA_GAIA: ...
    # bty.BossID.GUARDIAN: ...,
    # bty.BossID.MAGUS: ...
    # bty.Boss.BLACK_TYRANO: ...
    bty.BossID.OZZIE_TRIO: GauntletData(
        ctenums.LocID.OZZIES_FORT_LAST_STAND, 0x29, 0xB,
        0x298, 0xBF
    ),
    bty.BossID.ZEAL: GauntletData(
        ctenums.LocID.BLACK_OMEN_ZEAL, 0x8,0x8,
        0x7F, 0x80
    ),
    bty.BossID.ZEAL_2: GauntletData(
        ctenums.LocID.BLACK_OMEN_CELESTIAL_GATE, 0x8, 0x5,
        0x78, 0x5F
    )
}


def get_lavos_l3_tiles(ct_rom: ctrom.CTRom):
    """Only call on a rom without modified gauntlet maps"""
    loc_map = locationmap.LocationMap.get_location_map(
        ct_rom, ctenums.LocID.GAUNTLET_HECKRAN_CAVE)
    return loc_map.l3_tiles


def get_base_gauntlet_event(ct_rom: ctrom.CTRom):
    """Only call on a rom without modified gauntlet scripts"""
    event = LocationEvent.from_rom_location(
        ct_rom.getbuffer(), ctenums.LocID.GAUNTLET_REPTITE_LAIR)
    return event


def _get_shift(
        val: int, scroll_min: int, scroll_max: int,
        direction: typing.Literal["x", "y"]
):
    """
    Helper function to determine how much to shift Lavos L3 tiles depending
    on the change location tile and scroll box of the map
    """
    if direction == "x":
        neg_offset, pos_offset = 8, 7
    else:
        neg_offset, pos_offset = 8, 6

    edge = val - neg_offset
    if scroll_min < scroll_max:  # Some maps have nonsense scroll values
        if val - neg_offset < scroll_min:
            edge = scroll_min
        elif val + pos_offset > scroll_max:
            edge = scroll_max - (1+neg_offset+pos_offset)

    return edge % 0x10


def make_gauntlet_locations(
        gauntlet_bosses: list[bty.BossID],
        loc_data_dict: dict[ctenums.LocID, locationtypes.LocationData],
        ct_rom: ctrom.CTRom
) -> dict[bty.BossID, ctenums.LocID]:
    """
    Update Location data dict and write maps to ctrom.
    Returns dict of boss id to loc id
    """

    gauntlet_loc_pool = set(_vanilla_gauntlet_correspondence.values())
    remaining_gauntlet_bosses: list[bty.BossID] = []
    ret_dict: dict[bty.BossID, ctenums.LocID] = dict()
    for boss_id in gauntlet_bosses:
        if boss_id in _vanilla_gauntlet_correspondence:
            ret_dict[boss_id] = _vanilla_gauntlet_correspondence[boss_id]
        else:
            remaining_gauntlet_bosses.append(boss_id)

    lavos_l3_tiles = get_lavos_l3_tiles(ct_rom)

    for boss_id in remaining_gauntlet_bosses:
        gauntlet_loc = gauntlet_loc_pool.pop()
        orig_gauntlet_data = _boss_gauntlet_data_dict[boss_id]
        orig_loc_data = copy.copy(loc_data_dict[orig_gauntlet_data.loc_id])
        gauntlet_loc_data = loc_data_dict[gauntlet_loc]

        # The gauntlet location gets all of the original map's data except
        # 1) The map id of the gauntlet location is kept (the map is overwritten)
        # 2) The script id of the gauntlet location is kept (the script is overwritten)
        orig_loc_data.map_id = gauntlet_loc_data.map_id
        orig_loc_data.event_id = gauntlet_loc_data.event_id
        orig_loc_data.layer_3_tilechunks = 0x12

        loc_data_dict[gauntlet_loc] = orig_loc_data
        ret_dict[boss_id] = gauntlet_loc

        y_shift = _get_shift(
            orig_gauntlet_data.changeloc_y,
            orig_loc_data.top_tile_bound, orig_loc_data.bottom_tile_bound, "y"
        )
        x_shift = _get_shift(
            orig_gauntlet_data.changeloc_x,
            orig_loc_data.left_tile_bound, orig_loc_data.right_tile_bound, "x"
        )

        gauntlet_map = make_gauntlet_map_alt(
            ct_rom, orig_gauntlet_data.loc_id, lavos_l3_tiles,
            x_shift, y_shift
        )
        gauntlet_map.write_to_ctrom(
            ct_rom, gauntlet_loc_data.map_id
        )

    return ret_dict


def get_lavos_base_sprite_data() -> enemystats.EnemySpriteData:
    ret_data = enemystats.EnemySpriteData(bytes([0] * 10))
    ret_data.packet_id = 0xA3
    ret_data.sprite_assembly_id = 0x9B
    ret_data.palette = 0xCF
    ret_data.animation_id = 0x97
    ret_data.sprite_size = 1
    ret_data.hand_x_coord = 0
    ret_data.hand_y_coord = 0xE0
    ret_data.unk_07 = 0xC
    ret_data.unk_08 = 0xC
    ret_data.unk_09 = 0x0

    return ret_data


def get_lavos_support_sprite_data(size: int) -> enemystats.EnemySpriteData:
    if size == 0:
        ret_data = enemystats.EnemySpriteData(bytes([0]*10))
        ret_data.packet_id = 0xE0
        ret_data.sprite_assembly_id =0x80
        ret_data.palette = 0xF2
        ret_data.animation_id = 0xB4
        ret_data.sprite_size = 0
        ret_data.hand_x_coord = 0
        ret_data.hand_y_coord = 0xE0
        ret_data.unk_07 = 0xC
        ret_data.unk_08 = 0xC
        ret_data.unk_09 = 0x11
    else:
        ret_data = enemystats.EnemySpriteData(bytes([0] * 10))
        ret_data.packet_id = 0xE1
        ret_data.sprite_assembly_id = 0xAA
        ret_data.palette = 0xF3
        ret_data.animation_id = 0xB5
        ret_data.sprite_size = 1
        ret_data.hand_x_coord = 0
        ret_data.hand_y_coord = 0xE0
        ret_data.unk_07 = 0x8
        ret_data.unk_08 = 0x8
        ret_data.unk_09 = 0x11

    return ret_data


def replace_ai_script_ids(
        ai_script: enemyaitypes.EnemyAIScript,
        repl_dict: dict[ctenums.EnemyID, ctenums.EnemyID],
):
    for part in (ai_script.action_script, ai_script.reaction_script):
        for block in part:
            for condition in block.condition_list:
                if (index := getattr(condition, "index", None)) is not None:
                    setattr(
                        condition, "index",
                        repl_dict.get(index, index)
                    )

def remove_move_commands(
        ai_script: enemyaitypes.EnemyAIScript,
):
    for part in (ai_script.action_script, ai_script.reaction_script):
        for block in part:
            for ind, action in enumerate(block.action_list):
                if isinstance(action, enemyaitypes.Wander):
                    action[:]  = enemyaitypes.Wander(b'\x00\x00\x06\x00')[:]


def make_lavos_safe_techs(
        ct_rom: ctrom.CTRom,
        enemy_attack_manager: enemytech.EnemyAttackManager
):

    repl_dict: dict[ctenums.EnemyTechID, ctenums.EnemyTechID] = {
        ctenums.EnemyTechID.BAD_IMPULSE: ctenums.EnemyTechID.LAVOS_BAD_IMPULSE,
        ctenums.EnemyTechID.HARTFIRE_SWORD: ctenums.EnemyTechID.LAVOS_HARTFIRE_SWORD
    }

    for base_tech_id, lavos_tech_id in repl_dict.items():
        base_script = animationscript.EnemyTechAnimationScript.read_from_ctrom(
            ct_rom, base_tech_id
        )
        for caster_obj in base_script.main_script.caster_objects:
            if caster_obj is None:
                continue
            for command in caster_obj:
                if isinstance(command, ac._PlayAnimationBase):
                    if command.animation_id > 9 :
                        command.animation_id = 3

        base_script.write_to_ctrom(ct_rom, lavos_tech_id)
        base_tech = enemy_attack_manager.get_tech(base_tech_id)
        base_tech.graphics.script_id = lavos_tech_id
        enemy_attack_manager.set_tech(base_tech, lavos_tech_id)


def copy_gaunlet_boss_data(
        gauntlet_manager: lgt.GauntletManager,
        enemy_data_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        enemy_sprite_dict: dict[ctenums.EnemyID, enemystats.EnemySpriteData],
        enemy_ai_manager: enemyaimanager.EnemyAIManager,
        enemy_attack_manager: enemytech.EnemyAttackManager,
        copy_rewards: bool
):

    for boss_id in gauntlet_manager.gauntlet_bosses:
        if lgt.is_vanilla_gauntlet_boss(boss_id):
            continue  # Vanilla gauntlet bosses are already ok

        scheme = gauntlet_manager.get_lavos_scheme(boss_id)
        repl_dict = {
            gauntlet_manager.gauntlet_enemy_to_base_dict[part.enemy_id]: part.enemy_id
            for part in scheme.parts
        }
        for ind, part in enumerate(scheme.parts):
            lavos_enemy_id = part.enemy_id
            base_enemy_id = gauntlet_manager.gauntlet_enemy_to_base_dict[lavos_enemy_id]

            # Sprite Data
            base_sprite_data = enemy_sprite_dict[base_enemy_id]
            if ind == 0:
                base_lavos_sprite_data = get_lavos_base_sprite_data()
            else:
                base_lavos_sprite_data = get_lavos_support_sprite_data(
                    base_sprite_data.sprite_size
                )
            base_lavos_sprite_data.is_primary_enemy = base_sprite_data.is_primary_enemy
            base_lavos_sprite_data.unk_04_10 = base_lavos_sprite_data.unk_04_10
            base_lavos_sprite_data.unk_04_20 = base_lavos_sprite_data.unk_04_20
            base_lavos_sprite_data.unk_04_40 = base_lavos_sprite_data.unk_04_40
            base_lavos_sprite_data.unk_04_80 = base_lavos_sprite_data.unk_04_80
            enemy_sprite_dict[lavos_enemy_id] = base_lavos_sprite_data

            # AI script
            base_enemy_ai_script = copy.deepcopy(
                enemy_ai_manager.script_dict[base_enemy_id])
            replace_ai_script_ids(base_enemy_ai_script, repl_dict)
            remove_move_commands(base_enemy_ai_script)
            base_enemy_ai_script.update_usage({
                ctenums.EnemyTechID.BAD_IMPULSE: ctenums.EnemyTechID.LAVOS_BAD_IMPULSE,
                ctenums.EnemyTechID.HARTFIRE_SWORD: ctenums.EnemyTechID.LAVOS_HARTFIRE_SWORD
            })
            enemy_ai_manager.script_dict[lavos_enemy_id] = base_enemy_ai_script

            # Attack Data
            enemy_attack_manager.main_attack_graphics[lavos_enemy_id] = (
                enemy_attack_manager.main_attack_graphics[base_enemy_id].get_copy()
            )
            enemy_attack_manager.alt_attack_graphics[lavos_enemy_id] = (
                enemy_attack_manager.alt_attack_graphics[base_enemy_id].get_copy()
            )

            # Stats
            base_enemy_data = enemy_data_dict[base_enemy_id].get_copy()
            if not copy_rewards:
                base_enemy_data.xp = 0
                base_enemy_data.tp = 0
                base_enemy_data.gp = 0
                base_enemy_data.charm_item = ctenums.ItemID.NONE
                base_enemy_data.drop_item = ctenums.ItemID.NONE

            enemy_data_dict[lavos_enemy_id] = base_enemy_data


def write_gauntlet_location_scripts(
        gauntlet_bosses: list[bty.BossID],
        script_manager: scriptmanager.ScriptManager,
        gauntlet_loc_dict: dict[bty.BossID, ctenums.LocID]
):
    base_script = copy.deepcopy(script_manager[ctenums.LocID.GAUNTLET_REPTITE_LAIR])

    change_loc_block: EF = EF()
    init_gauntlet_counter = 9 - len(gauntlet_bosses)
    for ind, boss_id in enumerate(gauntlet_bosses):
        if boss_id in _vanilla_gauntlet_correspondence:
            loc_id = _vanilla_gauntlet_correspondence[boss_id]
            script = script_manager[loc_id]
            x, y = _vanilla_gauntlet_coords[boss_id]
            change_loc_block.add_if(
                EC.if_mem_op_value(memory.Memory.LAVOS_ATTACK_MODE_COUNTER,
                                   OP.EQUALS, ind),
                EF().add(EC.change_location(loc_id, x, y, unk=1, force_command_id=0xDF))
            )
        else:
            loc_id = gauntlet_loc_dict[boss_id]
            gauntlet_data = _boss_gauntlet_data_dict[boss_id]
            script = make_gauntlet_script(
                base_script, bty.get_default_scheme(boss_id),
                gauntlet_data.boss_x_px, gauntlet_data.boss_y_px,
                []
            )
            script_manager[loc_id] = script
            change_loc_block.add_if(
                EC.if_mem_op_value(memory.Memory.LAVOS_ATTACK_MODE_COUNTER,
                                   OP.EQUALS, ind),
                EF().add(EC.change_location(
                    loc_id, gauntlet_data.changeloc_x, gauntlet_data.changeloc_y,
                    unk=1, force_command_id=0xDF
                ))
            )

        update_gaunlet_script_counter(script, init_gauntlet_counter + ind + 1)


def apply_lavos_gaunltet_full(
        gauntlet_manager: lgt.GauntletManager,
        ct_rom: ctrom.CTRom,
        script_manager: scriptmanager.ScriptManager,
        loc_data_dict: dict[ctenums.LocID, locationtypes.LocationData],
        enemy_data_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        enemy_sprite_dict: dict[ctenums.EnemyID, enemystats.EnemySpriteData],
        enemy_ai_manager: enemyaimanager.EnemyAIManager,
        enemy_attack_manager: enemytech.EnemyAttackManager,
        copy_rewards: bool
):
    gauntlet_loc_dict = make_gauntlet_locations(
        gauntlet_manager.gauntlet_bosses, loc_data_dict, ct_rom
    )
    write_gauntlet_location_scripts(
        gauntlet_manager.gauntlet_bosses, script_manager, gauntlet_loc_dict
    )

    make_lavos_safe_techs(ct_rom, enemy_attack_manager)
    copy_gaunlet_boss_data(
        gauntlet_manager, enemy_data_dict, enemy_sprite_dict, enemy_ai_manager, enemy_attack_manager, copy_rewards
    )

    modify_lavos_script(
        script_manager[ctenums.LocID.LAVOS],
        gauntlet_manager.gauntlet_bosses,
        gauntlet_loc_dict,
        gauntlet_manager._lavos_scheme_dict
    )






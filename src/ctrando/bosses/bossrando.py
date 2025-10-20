# import random
import typing

from ctrando.arguments import bossrandooptions as bro
from ctrando.bosses import bosstypes as bty
from ctrando.bosses import bossrandoassign as bass
from ctrando.bosses.bossrandoassign import write_blackbird_peek
from ctrando.common import ctenums, random
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.arguments import bossrandooptions as bro
from ctrando.enemydata import enemystats


_default_assignment_dict: dict[bty.BossSpotID, bty.BossID] = {
    bty.BossSpotID.ARRIS_DOME: bty.BossID.GUARDIAN,
    bty.BossSpotID.BEAST_CAVE: bty.BossID.MUD_IMP,
    bty.BossSpotID.BLACKBIRD_LEFT_WING: bty.BossID.GOLEM_BOSS,
    bty.BossSpotID.BLACK_OMEN_MEGA_MUTANT: bty.BossID.MEGA_MUTANT,
    bty.BossSpotID.BLACK_OMEN_GIGA_MUTANT: bty.BossID.GIGA_MUTANT,
    bty.BossSpotID.BLACK_OMEN_TERRA_MUTANT: bty.BossID.TERRA_MUTANT,
    bty.BossSpotID.BLACK_OMEN_ELDER_SPAWN: bty.BossID.ELDER_SPAWN,
    bty.BossSpotID.DEATH_PEAK: bty.BossID.LAVOS_SPAWN,
    bty.BossSpotID.DENADORO_MTS: bty.BossID.MASA_MUNE,
    bty.BossSpotID.EPOCH_REBORN: bty.BossID.DALTON_PLUS,
    bty.BossSpotID.FACTORY_RUINS: bty.BossID.R_SERIES,
    bty.BossSpotID.GENO_DOME_MID: bty.BossID.ATROPOS_XR,
    bty.BossSpotID.GENO_DOME_FINAL: bty.BossID.MOTHER_BRAIN,
    bty.BossSpotID.GIANTS_CLAW: bty.BossID.RUST_TYRANO,
    bty.BossSpotID.HECKRAN_CAVE: bty.BossID.HECKRAN,
    bty.BossSpotID.KINGS_TRIAL: bty.BossID.YAKRA_XIII,
    bty.BossSpotID.MAGUS_CASTLE_FLEA: bty.BossID.FLEA,
    bty.BossSpotID.MAGUS_CASTLE_SLASH: bty.BossID.SLASH_SWORD,
    # bty.BossSpotID.MAGUS_CASTLE_MAGUS: 0,
    bty.BossSpotID.MANORIA_CATHERDAL: bty.BossID.YAKRA,
    bty.BossSpotID.MILLENNIAL_FAIR_GATO: bty.BossID.GATO,
    bty.BossSpotID.MT_WOE: bty.BossID.GIGA_GAIA,
    bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM: bty.BossID.GOLEM,
    bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT: bty.BossID.GOLEM,
    bty.BossSpotID.OZZIES_FORT_FLEA_PLUS: bty.BossID.FLEA_PLUS,
    bty.BossSpotID.OZZIES_FORT_SUPER_SLASH: bty.BossID.SUPER_SLASH,
    bty.BossSpotID.OZZIES_FORT_TRIO: bty.BossID.OZZIE_TRIO,
    bty.BossSpotID.PRISON_CATWALKS: bty.BossID.DRAGON_TANK,
    bty.BossSpotID.REPTITE_LAIR: bty.BossID.NIZBEL,
    bty.BossSpotID.SEWERS_KRAWLIE: bty.BossID.KRAWLIE,
    bty.BossSpotID.SUN_PALACE: bty.BossID.SON_OF_SUN,
    bty.BossSpotID.SUNKEN_DESERT: bty.BossID.RETINITE,
    bty.BossSpotID.TYRANO_LAIR_NIZBEL: bty.BossID.NIZBEL_2,
    bty.BossSpotID.ZEAL_PALACE: bty.BossID.DALTON,
    bty.BossSpotID.ZENAN_BRIDGE: bty.BossID.ZOMBOR,
    bty.BossSpotID.BLACK_OMEN_ZEAL: bty.BossID.ZEAL
}

def get_vanilla_assignment() -> dict[bty.BossSpotID, bty.BossID]:
    return dict(_default_assignment_dict)


AssignFunction = typing.Callable[[ScriptManager, bty.BossScheme], None]


_assign_function_dict: dict[bty.BossSpotID, AssignFunction] = {
    bty.BossSpotID.ARRIS_DOME: bass.assign_arris_dome_boss,
    bty.BossSpotID.BEAST_CAVE: bass.assign_beast_cave_boss,
    bty.BossSpotID.BLACKBIRD_LEFT_WING: bass.assign_blackbird_left_wing_boss,
    bty.BossSpotID.BLACK_OMEN_MEGA_MUTANT: bass.assign_black_omen_mega_mutant_boss,
    bty.BossSpotID.BLACK_OMEN_GIGA_MUTANT: bass.assign_black_omen_giga_mutant_boss,
    bty.BossSpotID.BLACK_OMEN_TERRA_MUTANT: bass.assign_black_omen_terra_mutant_boss,
    bty.BossSpotID.BLACK_OMEN_ELDER_SPAWN: bass.assign_black_omen_elder_spawn_boss,
    bty.BossSpotID.DEATH_PEAK: bass.assign_death_peak_boss,
    bty.BossSpotID.DENADORO_MTS: bass.assign_denadoro_boss,
    bty.BossSpotID.EPOCH_REBORN: bass.assign_epoch_reborn_boss,
    bty.BossSpotID.FACTORY_RUINS: bass.assign_factory_ruins_boss,
    bty.BossSpotID.GENO_DOME_MID: bass.assign_geno_mid_boss,
    bty.BossSpotID.GENO_DOME_FINAL: bass.assign_geno_dome_boss,
    bty.BossSpotID.GIANTS_CLAW: bass.assign_giants_claw_boss,
    bty.BossSpotID.HECKRAN_CAVE: bass.assign_heckran_cave_boss,
    bty.BossSpotID.KINGS_TRIAL: bass.assign_kings_trial_boss,
    bty.BossSpotID.MAGUS_CASTLE_FLEA: bass.assign_magus_castle_flea_boss,
    bty.BossSpotID.MAGUS_CASTLE_SLASH: bass.assign_magus_castle_slash_boss,
    # bty.BossSpotID.MAGUS_CASTLE_MAGUS: 0,
    bty.BossSpotID.MANORIA_CATHERDAL: bass.assign_cathedral_boss,
    bty.BossSpotID.MILLENNIAL_FAIR_GATO: bass.assign_gato_spot_boss,
    bty.BossSpotID.MT_WOE: bass.assign_mt_woe_boss,
    bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM: bass.assign_twin_boss,
    bty.BossSpotID.OZZIES_FORT_FLEA_PLUS: bass.assign_ozzies_fort_flea_plus_boss,
    bty.BossSpotID.OZZIES_FORT_SUPER_SLASH: bass.assign_ozzies_fort_super_slash_boss,
    bty.BossSpotID.OZZIES_FORT_TRIO: bass.assign_ozzies_fort_final,
    bty.BossSpotID.PRISON_CATWALKS: bass.assign_prison_catwalks_boss,
    bty.BossSpotID.REPTITE_LAIR: bass.assign_reptite_lair_boss,
    bty.BossSpotID.SEWERS_KRAWLIE: bass.assign_sewers_boss,
    bty.BossSpotID.SUN_PALACE: bass.assign_sun_palace_boss,
    bty.BossSpotID.SUNKEN_DESERT: bass.assign_sunken_desert_boss,
    bty.BossSpotID.TYRANO_LAIR_NIZBEL: bass.assign_tyrano_lair_midboss,
    bty.BossSpotID.ZEAL_PALACE: bass.assign_zeal_palace_boss,
    bty.BossSpotID.ZENAN_BRIDGE: bass.assign_zenan_bridge_boss,
    bty.BossSpotID.BLACK_OMEN_ZEAL: bass.assign_black_omen_zeal,
}

_midboss_spots: list[bty.BossSpotID] = [
    # bty.BossSpotID.EPOCH_REBORN,
    bty.BossSpotID.ZEAL_PALACE,
    bty.BossSpotID.SEWERS_KRAWLIE,
    bty.BossSpotID.MILLENNIAL_FAIR_GATO, bty.BossSpotID.OZZIES_FORT_FLEA_PLUS,
    bty.BossSpotID.OZZIES_FORT_SUPER_SLASH, bty.BossSpotID.GENO_DOME_MID,
]


def get_random_midboss_assignment(
        boss_rando_options: bro.BossRandoOptions,
        rng: random.RNGType
) -> dict[bty.BossSpotID, bty.BossID]:
    base_dict = {spot: _default_assignment_dict[spot] for spot in _midboss_spots}

    if boss_rando_options.midboss_randomization_type == bro.MidBossRandoType.VANILLA:
        return base_dict

    spot_pool, boss_pool = zip(
        *{spot: boss for spot, boss in base_dict.items()
          if spot not in boss_rando_options.vanilla_boss_spots}.items()
    )

    spot_pool = list(spot_pool)

    boss_pool = list(boss_pool)
    if boss_rando_options.midboss_randomization_type == bro.MidBossRandoType.RANDOM:
        test_pool = set(boss_rando_options.midboss_pool).intersection(boss_pool)
        if test_pool:
            boss_pool = list(test_pool)

        boss_pool = [rng.choice(boss_pool) for _ in spot_pool]
    else:
        rng.shuffle(boss_pool)

    base_dict.update(zip(spot_pool, boss_pool))

    # Guarantee Atropos in geno if she's not in the pool.
    if bty.BossID.ATROPOS_XR not in boss_pool:
        base_dict[bty.BossSpotID.GENO_DOME_MID] = bty.BossID.ATROPOS_XR

    return base_dict


def get_twin_spot_assignment(
        boss_pool: list[bty.BossID],
        rng: random.RNGType
):
    one_spot_ids = [
        boss_id for boss_id in boss_pool
        if len(bty.get_default_scheme(boss_id).parts) == 1
    ]

    if not one_spot_ids:
        raise ValueError

    return rng.choice(one_spot_ids)


def get_ozzies_fort_assignment(
        boss_pool: list[bty.BossID],
        available_spots: list[bty.BossSpotID],
        rng: random.RNGType
) -> bty.BossID:

    bad_ids = [bty.BossID.SLASH_SWORD]
    one_spot_ids = [
        boss_id for boss_id in boss_pool
        if len(bty.get_default_scheme(boss_id).parts) == 1 and boss_id not in bad_ids
    ]

    if not one_spot_ids:
        ozzie_boss = bty.BossID.OZZIE_TRIO
    else:
        ozzie_boss = rng.choice(one_spot_ids)

    return ozzie_boss


def get_random_boss_assignment(
        boss_rando_options: bro.BossRandoOptions,
        rng: random.RNGType
) -> dict[bty.BossSpotID, bty.BossID]:
    base_dict = dict(_default_assignment_dict)

    if boss_rando_options.boss_randomization_type == bro.BossRandoType.VANILLA:
        return base_dict

    available_spots = [
        spot for spot in base_dict
        if spot not in boss_rando_options.vanilla_boss_spots
        and spot not in (_midboss_spots + [bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT])
    ]

    boss_pool: list[bty.BossID] = []
    twin_spots = (bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM,
                  bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT)
    if boss_rando_options.boss_randomization_type == bro.BossRandoType.SHUFFLE:
        boss_pool = [base_dict[spot] for spot in available_spots]

        temp_boss_pool = list(boss_pool)
        temp_available_spots = list(available_spots)

        for twin_spot in twin_spots:
            if twin_spot in available_spots:
                twin_assign = get_twin_spot_assignment(boss_pool, rng)
                temp_available_spots.remove(twin_spot)

                base_dict[twin_spot] = twin_assign

                if twin_spot == bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM:
                    temp_boss_pool.remove(twin_assign)


        # if twin_spot in available_spots:
        #     twin_assign = get_twin_spot_assignment(boss_pool, rng)
        #     base_dict[twin_spot] = twin_assign
        #
        #     temp_available_spots.remove(twin_spot)

        if bty.BossSpotID.OZZIES_FORT_TRIO in available_spots:
            ozzie_boss = get_ozzies_fort_assignment(temp_boss_pool, available_spots, rng)
            base_dict[bty.BossSpotID.OZZIES_FORT_TRIO] = ozzie_boss

            temp_boss_pool.remove(ozzie_boss)
            temp_available_spots.remove(bty.BossSpotID.OZZIES_FORT_TRIO)

        rng.shuffle(temp_boss_pool)
        for spot, boss in zip(temp_available_spots, temp_boss_pool):
            base_dict[spot] = boss
    elif boss_rando_options.boss_randomization_type == bro.BossRandoType.RANDOM:
        boss_pool = list(boss_rando_options.boss_pool)

        for twin_spot in twin_spots:
            if twin_spot in available_spots:
                twin_assign = get_twin_spot_assignment(boss_pool, rng)

                if twin_spot == bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM:
                    available_spots.remove(twin_spot)

        # twin_spot = bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM
        # if twin_spot in available_spots:
        #     twin_assign = get_twin_spot_assignment(boss_pool, rng)
        #     base_dict[twin_spot] = twin_assign
        #     available_spots.remove(twin_spot)

        if bty.BossSpotID.OZZIES_FORT_TRIO in available_spots:
            ozzie_boss = get_ozzies_fort_assignment(boss_pool, available_spots, rng)
            base_dict[bty.BossSpotID.OZZIES_FORT_TRIO] = ozzie_boss
            available_spots.remove(bty.BossSpotID.OZZIES_FORT_TRIO)

        for spot in available_spots:
            base_dict[spot] = rng.choice(boss_pool)

    # if bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM in available_spots:
    #     twin_boss = bty.BossID.GOLEM
    #     one_spot_ids = [
    #         boss_id for boss_id in boss_pool
    #         if len(bty.get_default_scheme(boss_id).parts) == 1
    #     ]
    #     if one_spot_ids:
    #         twin_boss = rng.choice(one_spot_ids)
    #     base_dict[bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM] = twin_boss

    return base_dict


def resolve_character_conflicts(
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        recruit_assign_dict: dict[ctenums.RecruitID, ctenums.CharID | None],
        boss_rando_options: bro.BossRandoOptions,
        rng: random.RNGType
):
    """
    Prevent the Cathedral boss from blocking access to magic required to defeat it.
    Prevent the Death Peak boss from blocking access to magic required to defeat it.
    """

    vanilla_spots = boss_rando_options.vanilla_boss_spots
    nizbel_ids = (bty.BossID.NIZBEL, bty.BossID.NIZBEL_2)

    # The general strategy is just find a random boss who is not a nizbel
    # or retinite.  Then swap that with the offending boss

    recruit_boss_spot_pairs: tuple[tuple[ctenums.RecruitID, bty.BossSpotID], ...] = (
        (ctenums.RecruitID.CASTLE, bty.BossSpotID.MANORIA_CATHERDAL),
        (ctenums.RecruitID.DEATH_PEAK, bty.BossSpotID.DEATH_PEAK)
    )

    bad_spots: list[bty.BossSpotID] = []
    for recruit_id, boss_spot_id in recruit_boss_spot_pairs:
        recruit = recruit_assign_dict[recruit_id]
        boss = boss_assign_dict[boss_spot_id]

        lit_lock = (boss in nizbel_ids) and recruit == ctenums.CharID.CRONO
        water_lock = (boss == bty.BossID.RETINITE and recruit in (
            ctenums.CharID.MARLE, ctenums.CharID.FROG
        ))

        if lit_lock or water_lock:
            bad_spots.append(boss_spot_id)

    if not bad_spots:
        return

    if len(bad_spots) == 2:
        spot1, spot2 = bad_spots
        boss_assign_dict[spot1], boss_assign_dict[spot2] = (
            boss_assign_dict[spot2], boss_assign_dict[spot1])
    elif len(bad_spots) == 1:
        bad_spot = bad_spots[0]
        bad_boss = boss_assign_dict[bad_spot]

        spots = [x for x in boss_assign_dict.keys() if x not in vanilla_spots]
        rng.shuffle(spots)
        for spot in spots:
            boss = boss_assign_dict[spot]
            if boss not in nizbel_ids + (bty.BossID.RETINITE,):
                boss_assign_dict[spot] = bad_boss
                boss_assign_dict[bad_spot] = boss
                break
        else:
            boss_assign_dict[bad_spot] = bty.BossID.YAKRA
    else:
        raise ValueError

    # nizbel_locks_crono = cathedral_boss in nizbel_ids and castle_recruit == ctenums.CharID.CRONO
    # retinite_locks_water = (
    #         cathedral_boss == bty.BossID.RETINITE and
    #         castle_recruit in (ctenums.CharID.FROG, ctenums.CharID.MARLE)
    # )
    #
    # if nizbel_locks_crono or retinite_locks_water:
    #     spots = [x for x in boss_assign_dict.keys() if x not in vanilla_spots]
    #     rng.shuffle(spots)
    #     for spot in spots:
    #         boss = boss_assign_dict[spot]
    #         if boss not in nizbel_ids + (bty.BossID.RETINITE,):
    #             boss_assign_dict[spot] = cathedral_boss
    #             boss_assign_dict[bty.BossSpotID.MANORIA_CATHERDAL] = boss
    #             break
    #     else:
    #         boss_assign_dict[bty.BossSpotID.MANORIA_CATHERDAL] = bty.BossID.YAKRA


def fix_boss_sprites_given_assignment(
        boss_dict: dict[bty.BossSpotID, bty.BossID],
        enemy_sprite_dict: dict[ctenums.EnemyID, enemystats.EnemySpriteData]
):
    """Update Sprite Data if it depends on assigned spot."""

    def change_enemy_sprite(
            from_enemy_id: ctenums.EnemyID,
            to_enemy_id: ctenums.EnemyID,
            keep_palette: bool = True,
    ):
        new_sprite = enemy_sprite_dict[to_enemy_id].get_copy()

        if keep_palette:
            orig_data = enemy_sprite_dict[from_enemy_id]
            new_sprite.palette = orig_data.palette

        enemy_sprite_dict[from_enemy_id] = new_sprite

    arris_boss = boss_dict[bty.BossSpotID.ARRIS_DOME]
    if arris_boss != bty.BossID.GUARDIAN:
        change_enemy_sprite(ctenums.EnemyID.GUARDIAN, ctenums.EnemyID.NU, True)

    woe_boss = boss_dict[bty.BossSpotID.MT_WOE]
    if woe_boss != bty.BossID.GIGA_GAIA:
        enemy_sprite_dict[ctenums.EnemyID.GIGA_GAIA_HEAD].set_affect_layer_1(False)

    claw_boss = boss_dict[bty.BossSpotID.GIANTS_CLAW]
    if claw_boss != bty.BossID.RUST_TYRANO:
        enemy_sprite_dict[ctenums.EnemyID.RUST_TYRANO].set_affect_layer_1(False)

    bad_mud_imp_spots = (
        bty.BossSpotID.KINGS_TRIAL, bty.BossSpotID.MAGUS_CASTLE_SLASH
    )

    bad_spots_assigned_bosses = [
        boss_dict[spot] for spot in bad_mud_imp_spots
    ]

    # In theory, all of these other changes are obsolute with decompressed gfx
    # if bty.BossID.MUD_IMP in bad_spots_assigned_bosses:
    #     change_enemy_sprite(ctenums.EnemyID.RED_BEAST, ctenums.EnemyID.NU)
    #     change_enemy_sprite(ctenums.EnemyID.BLUE_BEAST, ctenums.EnemyID.NU)
    #
    # ozzie_spots = [
    #     spot for spot, entry in boss_dict.items()
    #     if entry == bty.BossID.OZZIE_TRIO
    # ]
    # if ozzie_spots != [bty.BossSpotID.OZZIES_FORT_TRIO]:
    #     change_enemy_sprite(ctenums.EnemyID.FLEA_PLUS_TRIO, ctenums.EnemyID.R_SERIES, False)
    #     enemy_sprite_dict[ctenums.EnemyID.FLEA_PLUS_TRIO].palette = enemy_sprite_dict[ctenums.EnemyID.ATROPOS_XR].palette
    #     change_enemy_sprite(ctenums.EnemyID.SUPER_SLASH_TRIO, ctenums.EnemyID.R_SERIES, False)
    #
    # if bty.BossSpotID.OZZIES_FORT_TRIO not in ozzie_spots:
    #     ozzie_assign = boss_dict[bty.BossSpotID.OZZIES_FORT_TRIO]
    #     ozzie_assign_id = bty.get_default_scheme(ozzie_assign).parts[0].enemy_id
    #
    #     # Ozzie can't do Slash's spincut (freezes)
    #     # Really, this is OK for any small sprite.  Perhaps only force Ozzie for
    #     # Nizbel, Golem, ???
    #     if ozzie_assign_id not in (
    #         ctenums.EnemyID.SLASH_SWORD, ctenums.EnemyID.FLEA, ctenums.EnemyID.DALTON_PLUS
    #     ):
    #         change_enemy_sprite(ozzie_assign_id, ctenums.EnemyID.GREAT_OZZIE, False)


def fix_atropos_ribbon_buff(
        boss_dict: dict[bty.BossSpotID, bty.BossID],
        script_manager: ScriptManager
):
    spots = [
        spot for spot, entry in boss_dict.items()
        if entry== bty.BossID.ATROPOS_XR
    ]

    if bty.BossSpotID.GENO_DOME_MID not in spots:
        bass.remove_ribbon_from_geno_dome(script_manager)

    for spot in spots:
        bass.add_ribbon_buff_to_spot(script_manager, spot)


def determine_twin_scheme(
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID]
) -> bty.BossScheme:
    main_id =  boss_assign_dict[bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM]
    main_scheme = bty.get_default_scheme(main_id)
    main_part = main_scheme.parts[0]

    main_slot, alt_slot = bass.get_base_alt_slots(main_part)
    main_slot = 3
    main_part.slot = main_slot

    second_id = boss_assign_dict[bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT]
    second_scheme = bty.get_default_scheme(second_id)

    second_part =  second_scheme.parts[0]
    main_slot, alt_slot = bass.get_base_alt_slots(second_part)
    second_part.slot = alt_slot
    new_scheme = bty.BossScheme(main_part, second_part)

    return new_scheme


def determine_trio_scheme(
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID]
) -> bty.BossScheme:
    flea_assign = boss_assign_dict[bty.BossSpotID.OZZIES_FORT_FLEA_PLUS]
    slash_assign = boss_assign_dict[bty.BossSpotID.OZZIES_FORT_SUPER_SLASH]
    ozzie_assign = boss_assign_dict[bty.BossSpotID.OZZIES_FORT_TRIO]

    flea_scheme = bty.get_default_scheme(flea_assign)
    slash_scheme = bty.get_default_scheme(slash_assign)
    ozzie_scheme = bty.get_default_scheme(ozzie_assign)

    scheme = bty.BossScheme(
        ozzie_scheme.parts[0],
        slash_scheme.parts[0],
        flea_scheme.parts[0]
    )

    ids = [part.enemy_id for part in scheme.parts]
    use_slot_7 = (
        ctenums.EnemyID.FLEA_PLUS in ids or
        ctenums.EnemyID.SUPER_SLASH in ids
    )
    alt_slot = 6 if not use_slot_7 else 7
    scheme.parts[0].slot = 3
    if flea_scheme.parts[0].enemy_id == ctenums.EnemyID.GATO:
        scheme.parts[2].slot = 6
        scheme.parts[1].slot = 0x9
    elif slash_scheme.parts[0].enemy_id == ctenums.EnemyID.GATO:
        scheme.parts[1].slot = 6
        scheme.parts[2].slot = 9
    else:
        scheme.parts[1].slot = alt_slot
        scheme.parts[2].slot = 9

    return scheme

def write_bosses_to_ct_rom(
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        script_manager: ScriptManager,
):
    for boss_spot, boss_id in boss_assign_dict.items():
        if boss_id == _default_assignment_dict[boss_spot]:
            continue
        if boss_spot == bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT:
            continue  # handled by main spot

        assign_func = _assign_function_dict[boss_spot]
        if boss_spot == bty.BossSpotID.OZZIES_FORT_TRIO:
            scheme = determine_trio_scheme(boss_assign_dict)
        elif boss_spot == bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM:
            scheme = determine_twin_scheme(boss_assign_dict)
        else:
            scheme = bty.get_default_scheme(boss_id)

        assign_func(script_manager, scheme)

    wing_boss = boss_assign_dict[bty.BossSpotID.BLACKBIRD_LEFT_WING]
    epoch_boss = boss_assign_dict[bty.BossSpotID.EPOCH_REBORN]

    bass.write_blackbird_peek(script_manager, epoch_boss, wing_boss)

    # ozzie_scheme = bty.get_default_scheme(bty.BossID.OZZIE_TRIO)
    # ozzie_scheme.parts[0].enemy_id = ctenums.EnemyID.FLEA
    # ozzie_scheme.parts[0].slot = 3
    #
    # ozzie_scheme.parts[1].enemy_id = ctenums.EnemyID.DALTON_PLUS
    # ozzie_scheme.parts[1].slot = 9
    #
    # ozzie_scheme.parts[2].enemy_id = ctenums.EnemyID.GATO
    # ozzie_scheme.parts[2].slot = 6
    # bass.assign_ozzies_fort_final(script_manager, ozzie_scheme)




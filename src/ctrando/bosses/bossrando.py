from random import Random
import typing

from ctrando.arguments import bossrandooptions as bro
from ctrando.bosses import bosstypes as bty
from ctrando.bosses import bossrandoassign as bass
from ctrando.bosses.bossrandoassign import write_blackbird_peek
from ctrando.common import ctenums, random
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.arguments import bossrandooptions as bro
from ctrando.enemydata import enemystats
from ctrando.items import itemdata
from ctrando.strings import ctstrings
from ctrando.overworlds import owmanager

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
    bty.BossSpotID.BLACK_OMEN_ZEAL: bty.BossID.ZEAL,
    bty.BossSpotID.NORTH_CAPE: bty.BossID.MAGUS_NORTH_CAPE
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
    bty.BossSpotID.NORTH_CAPE: bass.assign_north_cape_boss,
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
        # Check for double Gato Ozzie's Fort

    else:
        rng.shuffle(boss_pool)

    base_dict.update(zip(spot_pool, boss_pool))

    # Guarantee Atropos in geno if she's not in the pool.
    if bty.BossID.ATROPOS_XR not in boss_pool:
        base_dict[bty.BossSpotID.GENO_DOME_MID] = bty.BossID.ATROPOS_XR

    # Don't allow double gato in Ozzie's Fort
    fort_assignments = set(
        [base_dict[bty.BossSpotID.OZZIES_FORT_FLEA_PLUS],
         base_dict[bty.BossSpotID.OZZIES_FORT_SUPER_SLASH]]
    )
    if fort_assignments == {bty.BossID.GATO}:
        if set(boss_pool) == {bty.BossID.GATO}:
            replacement = bty.BossID.FLEA_PLUS
        else:
            replacement_pool = [x for x in boss_pool if x != bty.BossID.GATO]
            replacement = rng.choice(replacement_pool)

        base_dict[bty.BossSpotID.OZZIES_FORT_FLEA_PLUS] = replacement

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
        return bty.BossID.GOLEM

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
        and spot not in _midboss_spots
    ]

    boss_pool: list[bty.BossID] = []
    twin_spots = (bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM,
                  bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT)
    if boss_rando_options.boss_randomization_type == bro.BossRandoType.SHUFFLE:
        # Don't add the alt twin to the pool or you get two golems
        boss_pool = [base_dict[spot] for spot in available_spots
                     if spot != bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT]

        temp_boss_pool = list(boss_pool)
        temp_available_spots = list(available_spots)

        for twin_spot in twin_spots:
            if twin_spot in available_spots:
                twin_assign = get_twin_spot_assignment(boss_pool, rng)
                temp_available_spots.remove(twin_spot)

                base_dict[twin_spot] = twin_assign

                # Only remove the boss from the pool if it's assigned to the main twin spot
                if twin_spot == bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM:
                    temp_boss_pool.remove(twin_assign)

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
                available_spots.remove(twin_spot)

        if bty.BossSpotID.OZZIES_FORT_TRIO in available_spots:
            ozzie_boss = get_ozzies_fort_assignment(boss_pool, available_spots, rng)
            base_dict[bty.BossSpotID.OZZIES_FORT_TRIO] = ozzie_boss
            available_spots.remove(bty.BossSpotID.OZZIES_FORT_TRIO)

        for spot in available_spots:
            base_dict[spot] = rng.choice(boss_pool)

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
        (ctenums.RecruitID.DEATH_PEAK, bty.BossSpotID.DEATH_PEAK),
        (ctenums.RecruitID.NORTH_CAPE, bty.BossSpotID.NORTH_CAPE)
    )

    bad_spots: list[bty.BossSpotID] = []
    for recruit_id, boss_spot_id in recruit_boss_spot_pairs:
        recruits = recruit_assign_dict[recruit_id]
        recruit = recruits[0] if recruits else None
        boss = boss_assign_dict[boss_spot_id]

        lit_lock = (boss in nizbel_ids) and recruit == ctenums.CharID.CRONO
        water_lock = (boss == bty.BossID.RETINITE and recruit in (
            ctenums.CharID.MARLE, ctenums.CharID.FROG
        ))

        if lit_lock or water_lock:
            bad_spots.append(boss_spot_id)

    if not bad_spots:
        return

    # There can only be two bad spots.
    # - Crono can block one Nizbel at most
    # - Marle/Frog can block at most Retinite

    if len(bad_spots) == 2:
        spot1, spot2 = bad_spots
        boss_assign_dict[spot1], boss_assign_dict[spot2] = (
            boss_assign_dict[spot2], boss_assign_dict[spot1])
    elif len(bad_spots) == 1:
        bad_spot = bad_spots[0]
        bad_boss = boss_assign_dict[bad_spot]
        midboss_ids = bty.get_midboss_ids()

        spots = [
            spot for spot, boss in boss_assign_dict.items()
            if spot not in vanilla_spots and boss not in midboss_ids
        ]
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

    change_giga_gaia = change_tyrano = False

    for spot, boss in boss_dict.items():
        if boss == bty.BossID.GIGA_GAIA and spot != bty.BossSpotID.MT_WOE:
            change_giga_gaia = True

        if boss == bty.BossID.RUST_TYRANO and spot != bty.BossSpotID.GIANTS_CLAW:
            change_tyrano = True


    if change_giga_gaia:
        enemy_sprite_dict[ctenums.EnemyID.GIGA_GAIA_HEAD].set_affect_layer_1(False)

    if change_tyrano:
        enemy_sprite_dict[ctenums.EnemyID.RUST_TYRANO].set_affect_layer_1(False)


def fix_atropos_ribbon_buff(
        boss_dict: dict[bty.BossSpotID, bty.BossID],
        script_manager: ScriptManager,
        mdef_levelup_cap: int,
):
    spots = [
        spot for spot, entry in boss_dict.items()
        if entry== bty.BossID.ATROPOS_XR
    ]

    if bty.BossSpotID.GENO_DOME_MID not in spots:
        bass.remove_ribbon_from_geno_dome(script_manager)
    else:
        bass.fix_vanilla_atropos_buff(script_manager, mdef_levelup_cap)

    for spot in spots:
        bass.add_ribbon_buff_to_spot(script_manager, spot, mdef_levelup_cap)


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


_dragon_tank_manuals: dict[bty.BossID, str] = {
    bty.BossID.DALTON_PLUS:
    "Dalton counters lightning or physical attacks with Iron Orb. " 
    "All other elements will be countered with a spell of the opposite element.{full break}"
    "Even if Dalton is defeated, he can summon the mighty Golem Boss to finish his foes!",
    bty.BossID.ELDER_SPAWN:
    "The Elder Lavos Spawn attacks with a mix of powerful physical attacks as well as shadow and water magic. "
    "Any attack on the Shell will be met with a devastating needle counterattack on the attacker.",
    bty.BossID.FLEA:
    "Flea specializes in status effects, being capable of inflicting chaos, sleep, poison, and blindness on the enemy. "
    "In addition to high magic defense, Flea has a natural resistance to all elements except fire."
    "{full break}"
    "When below half health, Flea may counterattack with The Stare."
    "The counterattack seems to fail unless there are exactly three enemies, "
    "but we are confident this can be fixed with more testing.",
    bty.BossID.GIGA_GAIA:
    "Unfortunately, we were unable to reconstruct Giga Gaia's body, and instead have "
    "installed state of the art levitation devices in its head and hands. "
    "Together, the hands perform powerful fire and shadow attacks. "
    "Separately, the left hand can heal the head and do water attacks while "
    "the right hand does fire attacks. "
    "The head alone can do nothing except revive the arms. ",
    bty.BossID.GIGA_MUTANT:
    "Giga Mutant comes equipped with powerful fire and lightning attacks as well as "
    "the ability to inflect sleep and poison. "
    "The Giga Mutant is nigh impervious to physical attacks, has naturally high magic defense, "
    "but no specific elemental resistances. {full break}"
    "The top half counters any attack with an MP draining attack."
    "The bottom half has the additional ability to reduce a target's life to 1 HP."
    "If the top is defeated the bottom will add HP-down effects on top of its 1 HP attacks.",
    bty.BossID.GOLEM:
    "The Golem adapts its attack to whatever element it is attacked with. "
    "Its physical, fire, and water modes take time to ramp up to their strongest attacks." 
    "The Golem is also vulnerable to all status effects except chaos. {full break}"
    "So long as the enemy does not exploit its status weaknesses and does not juggle the Golem between "
    "its weaker modes, it is unbeatable!",
    bty.BossID.GOLEM_BOSS:
    "The Golem Boss is a being of immense power.  In testing, no armor could withstand its might. {full break}"
    "Unfortunately, in the field the Golem Boss displays extreme cowardice, failing to use "
    "any of its incredible attacks and running away after some time. "
    "We will continue to iterate on its design.",
    bty.BossID.GUARDIAN:
    "We have managed to incorporate the Guardian technology into a Nu's body. "
    "The main body will counterattack while the Bits live. "
    "If the Bits fall, the main body can revive the bits after a brief charging period.",
    bty.BossID.HECKRAN:
    "Heckran is nigh impervious to all physical attacks but has no specific strength against magic attacks. "
    "Heckran possesses strong water magic including a devastating water counter to any foolish enough "
    "to attack while its claw is raised.{full break}"
    "We are working with Heckran to stop announcing its counter attack state. "
    "Once we do, we are certain it will be unstoppable!",
    bty.BossID.LAVOS_SPAWN:
    "The Lavos Spawn is the pinnacle of evolved live on this planet. "
    "Most of its threats come from devastating party-wide needle attacks. "
    "It has some weaker fire, sleep, and chaos attacks to supplement this. "
    "{full break}"
    "Any foe foolish enough attack the shell (or enticed to so so by chaos) will trigger more"
    "a party-wide needle attacks. "
    "Those without single-target attacks will surely perish against the mighty Lavos Spawn!",
    bty.BossID.MAGUS_NORTH_CAPE:
    "Based on a powerful wizard from 600 AD, Magus will attack with his scythe or do a powerful "
    "area magic spell. "
    "When below half health, Magus will also counterattack with one of these attacks. [full break}"
    "Unlike his namesake, this Magus has no form of elemental barriers. "
    "We are confident that with further research, we can harness this power and make "
    "Magus unstoppable!",
    bty.BossID.MASA_MUNE:
    "When he isn't waddling around, MasaMune can deliver powerful physical damage on a single target. "
    "His attack doubles at less than 50% HP. "
    "MasaMune can also charge up tornado energy which can only be dispelled by a wind Slash. "
    "{full break}"
    "Despite his great potential and high HP pool, MasaMune tends to die before doing anything meaningful. "
    "Certainly this is a target for future research. ",
    bty.BossID.MEGA_MUTANT:
    "Mega Mutant does not have the physical defenses of its mutant siblings. "
    "To make up for this it has powerful status attacks. "
    "The top half can use sleep and poison while the bottom uses Obstacle to inflict "
    "party-wide chaos.",
    bty.BossID.MOTHER_BRAIN:
    "The Mother Brain uses chaos attacks and shadow lasers, but the true threat lies in "
    "the support Displays. "
    "These show the pinnacle of our regeneration technologies. "
    "Each is capable of restoring a significant portion of the Mother Brain's health. "
    "It is unlikely that an enemy will be able to defeat the Mother Brain while the Displays live. "
    "Should the displays all fall, the Mother Brain will frenzy and grow more powerful."
    "{full break}"
    "Unless the enemy is able to sleep or stop the displays, this gives them an "
    "impossible dilemma!",
    bty.BossID.MUD_IMP:
    "The Mud Imp is one of our most obnoxious creations to date. "
    "Despite having low HP, the Mud Imp has amazing defensive capabilities while its beasts live. "
    "Additionally, the Mud Imp has some healing ability and is capable of inflicting sleep on its enemies. "
    "It will counter every attack with one of these abilities."
    "{full break}"
    "The only weakness of the Mud Imp is it's standard magic defense. "
    "In addition, the beasts are weak to the opposing element and status abilities. "
    "Opponents who do not find these weaknesses are doomed!",
    bty.BossID.NIZBEL:
    "Nizbel has nearly impenetrable defenses, both magic and physical, and is "
    "capable of doing strong physical attacks. "
    "If hit by lightning, however, it becomes stunned for some time and loses its defensive qualities. "
    "When it recovers from the stun, it releases the stored lightning energy back on its enemies. "
    "The lightning is even more powerful than its normal attacks. "
    "{full break}"
    "Surely the kingdom will be unassailable with this weapon!",
    bty.BossID.NIZBEL_2:
    "Nizbel 2 has strong physical defenses but no special resistance to magic. "
    "It attacks with strong physical attacks and has tremendous speed. "
    "Lightning attacks will lower its defense. After three lightning attacks it will "
    "unleash the stored energy in a savage electric attack. "
    "{full break}"
    "Foes foolish enough to continue attacking after the third lightning attack will "
    "get a special surprise.",
    bty.BossID.OZZIE_TRIO:
    "Ozzie, Flea, and Slash make an unstoppable trio. "
    "While Flea lives, attacking Flea or Slash will trigger a powerful fire counter attack. "
    "Attacking Ozzie directly will result in a shadow counter. "
    "The only weakness is that Flea is vulnerable to status ailments... "
    "Also, if Slash is defeated, Flea will flee..."
    "And also Ozzie can't do anything once a single member of the trio falls."
    "{full break}"
    "Otherwise, the Ozzie trio is unstoppable!",
    bty.BossID.RETINITE:
    "The Retinite has impenetrable physical defense and is highly evasive. "
    "Enemies who use elemental attacks will find that the magic does no damage "
    "or will even heal the core! "
    "Water-based attacks will remove the Retinite's physical defense and evasion.{full break}"
    "The top and bottom can heal themselves by drawing energy from the core. "
    "Should the core be destroyed, the remaining parts will frenzy and be near unstoppable. "
    "We are investigating developing a version of Retinite without a core so that it can begin "
    "in its frenzied state.",
    bty.BossID.R_SERIES:
    "The R-Series are six humanoid robots with powerful physical attacks. "
    "If the robots are not defeated simultaneously, they will begin to do powerful "
    "counter attacks as their numbers decrease. "
    "{full break}"
    "P.S. Whoever keeps throwing bricks through our windows which say {\"1}Buff R-Series{\"2} "
    "really needs to stop.",
    bty.BossID.RUST_TYRANO:
    "The Rust Tyrano is a refurbished relic found in a cave off the "
    "coast of Choras. Unfortunately, we were only able to salvage the head. "
    "After charging up, the head will unleash a powerful fire attack. "
    "Each subsequent fire attack is faster to charge and more powerful as well."
    "{full break}"
    "Those without sufficient DPS are no match for the mighty Rust Tyrano!",
    bty.BossID.SLASH_SWORD:
    "Slash has naturally high magic defense.  In addition. Slash takes 50% from"
    "fire, lightning, and shadow elements and no damage from water. "
    "When first entering battle Slash will only perform wind slashes. "
    "{full break}"
    "As its health depletes it begins to do powerful physical attacks. "
    "At critically low health, it even possesses auto-counter capabilities.",
    bty.BossID.SON_OF_SUN:
    "Son of Sun's Eye is impervious to all attacks and will counter any attack "
    "with a Flare. "
    "The surrounding flames can only be defeated by instant death attacks. "
    "Only by hitting the appropriate flame can the eye be damaged. "
    "Meanwhile, Son of Son will unleash devastating fire and shadow attacks. ",
    bty.BossID.TERRA_MUTANT:
    "The Terra Mutant uses Chaotic Zone to confuse its foes while striking with "
    "powerful fire, drain, and physical attacks. "
    "The bottom half is nearly indestructible and can be used as an HP reservoir for the top. "
    "Should either part be defeated, the other will fall as well. ",
    bty.BossID.YAKRA:
    "Yakra attacks with powerful physical attacks and has a large HP pool. "
    "In addition, Yakra can counter any attack with party-wide physical damage."
    "{full break}"
    "However, the counters tend to fail about half the time. "
    "Additionally, the counters will fail if the attacker is too close or if "
    "Yakra is not facing exactly three foes. "
    "We will continue to iterate on this design. ",
    bty.BossID.YAKRA_XIII:
    "Yakra XIII has mild chaos-inducing attacks and powerful needles. "
    "As its health is depleted, it will greatly increase its attack power. {full break}"
    "Should it fall in battle, it will release one final party-wide needle attack.",
    bty.BossID.ZEAL:
    "Zeal has tremendous attacks which reduce the enemy's HP to one so that any other "
    "attack will instantly defeat them.{full break}"
    "Unfortunately, we are currently experiencing difficulties making Zeal perform any "
    "other damaging attack. She seems to only perform one for every third attack. "
    "Once we solve this, Zeal will be unstoppable!",
    bty.BossID.ZOMBOR:
    "The top half of Zombor absorbs lightning and fire while the bottom half has "
    "strong physical defense and absorbs water and shadow. "
    "As their HP is depleted, Zombor will attack more frequently. "
    "If one half falls, the other will become more powerful. ",
}
def make_boss_manual_string(boss_id: bty.BossID) -> ctstrings.CTString:
    manual_body = _dragon_tank_manuals[boss_id]
    boss_name = bty.get_boss_dialogue_name(boss_id)
    intro_ct_str = ctstrings.CTString.from_str(
        "To the Prison Supervisor{linebreak+0}{line break}"
        "   {\"1}" + boss_name + "{\"2} Owner's Manual{full break}"
    )
    end_ct_str = ctstrings.CTString.from_str(
        "{line break}                     Guardia R & D{null}"
    )
    manual_ct_str = ctstrings.CTString.from_str(manual_body, compress=False)
    manual_ct_str = ctstrings.get_width_adjusted_ct_string(
        manual_ct_str, compress=False, indent_new_lines=False, indent_new_pages=False,
        null_terminate=False
    )

    out_str = ctstrings.CTString(intro_ct_str + manual_ct_str + end_ct_str)
    return out_str


def update_boss_names(
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        script_manager: ScriptManager,
        enemy_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        item_man: itemdata.ItemDB,
        ow_manager: owmanager.OWManager,
):
    """Add Peeks for various bosses."""
    # Cathedral
    spot_id = bty.BossSpotID.MANORIA_CATHERDAL
    boss_id = boss_assign_dict[spot_id]
    script = script_manager[ctenums.LocID.MANORIA_KITCHEN]

    boss_name = bty.get_boss_dialogue_name(boss_id)
    string = ctstrings.CTString.ct_bytes_to_ascii(script.strings[4])
    string = string.replace("Yakra", boss_name)
    if boss_id in (bty.BossID.ZEAL,):
        string = string.replace("His", "Her")
    script.strings[4] = ctstrings.CTString.from_str(string, True)

    # Guardia Prison
    spot_id = bty.BossSpotID.PRISON_CATWALKS
    boss_id = boss_assign_dict[spot_id]
    script = script_manager[ctenums.LocID.GUARDIA_THRONEROOM_1000]
    boss_name = bty.get_boss_dialogue_name(boss_id)

    new_ct_str = ctstrings.CTString.from_str(
        "The Chancellor lost it right around the{linebreak+0}"
        f"time he ordered that {boss_name} to{{linebreak+0}}"
        "be built!{null}"
    )
    script.strings[105] = new_ct_str
    script.strings[34] = ctstrings.CTString(new_ct_str)
    # for ind, ct_str in enumerate(script.strings):
    #     script.strings[ind] = ctstrings.CTString.from_str(string, True)
    #     print(f"{ind}: {ctstrings.CTString.ct_bytes_to_ascii(ct_str)}")
    # input()

    if boss_id != bty.BossID.DRAGON_TANK:
        if boss_id in _dragon_tank_manuals:
            script = script_manager[ctenums.LocID.PRISON_SUPERVISORS_OFFICE]
            pos, _ = script.find_command([0xC1], script.get_function_start(0x11, 1))
            str_id = script.data[pos+1]
            ct_str = make_boss_manual_string(boss_id)
            script.strings[str_id] = ct_str

        script = script_manager[ctenums.LocID.PRISON_CATWALKS]
        for ind, ct_str in enumerate(script.strings):
            string = str(ctstrings.CTString(ct_str))
            if "Dragon Tank" in string:
                string = string.replace("Dragon Tank", boss_name)
                script.strings[ind] = ctstrings.CTString.from_str(string)

    # Heckran Cave
    spot_id = bty.BossSpotID.HECKRAN_CAVE
    boss_id = boss_assign_dict[spot_id]
    script = script_manager[ctenums.LocID.MEDINA_INN]
    boss_name = bty.get_boss_dialogue_name(boss_id)

    string = ctstrings.CTString.ct_bytes_to_ascii(script.strings[9])
    string = string.replace("Heckran", boss_name)
    script.strings[9] = ctstrings.CTString.from_str(string, True)

    if boss_id != bty.BossID.HECKRAN:
        ow_manager.name_dict[19] = f"{bty.get_abbrev_name(boss_id)} Cave"


    # Denadoro
    spot_id = bty.BossSpotID.DENADORO_MTS
    boss_id = boss_assign_dict[spot_id]
    if boss_id != bty.BossID.MASA_MUNE:
        script = script_manager[ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE]
        masa_part, mune_part = bty.get_split_name(boss_id)
        enemy_dict[ctenums.EnemyID.MASA].name = masa_part.capitalize()
        enemy_dict[ctenums.EnemyID.MUNE].name = mune_part.capitalize()

        for ind, ct_str in enumerate(script.strings):
            if ind == 2:
                continue
            string = ctstrings.CTString.ct_bytes_to_ascii(ct_str)
            string = string.replace("MASA", masa_part.upper())
            string = string.replace("Masa", masa_part.capitalize())
            string = string.replace("MUNE", mune_part.upper())
            string = string.replace("Mune", mune_part.capitalize())
            script.strings[ind] = ctstrings.CTString.from_str(string, True)
        #     print(f"{ind}: {ctstrings.CTString.ct_bytes_to_ascii(script.strings[ind])}")
        # input()

    # Ozzie
    spot_id = bty.BossSpotID.OZZIES_FORT_TRIO
    boss_id = boss_assign_dict[spot_id]
    if boss_id != bty.BossID.OZZIE_TRIO:
        boss_name = bty.get_boss_dialogue_name(boss_id)
        ow_manager.name_dict[33] = f"{bty.get_abbrev_name(boss_id)}'s Fort"
        # for key, val in ow_manager.name_dict.items():
        #     print(key, val)
        #
        # input()

    # Arris
    spot_id = bty.BossSpotID.ARRIS_DOME
    boss_id = boss_assign_dict[spot_id]
    # This is dumb, but I don't want to carry the rng through to postconfig
    rng = Random("".join(str(x) for x in boss_assign_dict.values()))
    category_dict = bty.get_arris_categories()
    categories = list(category_dict.keys())
    rng.shuffle(categories)
    chosen_category: str = ""
    for category in categories:
        if boss_id in category_dict[category]:
            chosen_category = category
            break
    else:
        chosen_category = bty.get_abbrev_name(boss_id)

    script = script_manager[ctenums.LocID.ARRIS_DOME]
    string = ctstrings.CTString.ct_bytes_to_ascii(script.strings[11])
    string = string.replace("robot guards", chosen_category)
    script.strings[11] = ctstrings.CTString.from_str(string, True)

    # Geno Dome
    spot_id = bty.BossSpotID.GENO_DOME_FINAL
    boss_id = boss_assign_dict[spot_id]
    script = script_manager[ctenums.LocID.GENO_DOME_LABS]
    string = ctstrings.CTString.ct_bytes_to_ascii(script.strings[9])
    string = string.replace(
        "Mother Brain", bty.get_boss_dialogue_name(boss_id)
    )
    script.strings[9] = ctstrings.CTString.from_str(string, True)


    # Reptite Lair
    spot_id = bty.BossSpotID.REPTITE_LAIR
    boss_id = boss_assign_dict[spot_id]
    boss_name = bty.get_boss_dialogue_name(boss_id)

    script = script_manager[ctenums.LocID.REPTITE_LAIR_AZALA_ROOM]
    for str_id in (6, 7):
        string = ctstrings.CTString.ct_bytes_to_ascii(script.strings[str_id])
        string = string.replace("Nizbel", boss_name)
        script.strings[str_id] = ctstrings.CTString.from_str(string)

    # Ozzie's Fort
    spot_id = bty.BossSpotID.OZZIES_FORT_TRIO
    boss_id = boss_assign_dict[spot_id]
    ozzie_id = bty.get_default_scheme(boss_id).parts[0].enemy_id
    ozzie_charm = enemy_dict[ozzie_id].charm_item
    if ozzie_charm == ctenums.ItemID.NONE:
        ozzie_charm_name = "Nothing"
    else:
        ozzie_charm_name = str(ctstrings.CTString(item_man[ozzie_charm].name[1:]))

    slash_bid = boss_assign_dict[bty.BossSpotID.OZZIES_FORT_SUPER_SLASH]
    slash_id = bty.get_default_scheme(slash_bid).parts[0].enemy_id
    slash_name = bty.get_boss_dialogue_name(slash_bid)
    slash_charm = enemy_dict[slash_id].charm_item
    if slash_charm == ctenums.ItemID.NONE:
        slash_charm_name = "Nothing"
    else:
        slash_charm_name = str(ctstrings.CTString(item_man[slash_charm].name[1:]))
    flea_bid = boss_assign_dict[bty.BossSpotID.OZZIES_FORT_FLEA_PLUS]
    flea_id = bty.get_default_scheme(flea_bid).parts[0].enemy_id
    flea_name = bty.get_boss_dialogue_name(flea_bid)

    flea_charm = enemy_dict[flea_id].charm_item
    if flea_charm == ctenums.ItemID.NONE:
        flea_charm_name = "Nothing"
    else:
        flea_charm_name = str(ctstrings.CTString(item_man[flea_charm].name[1:]))
    ozzie_name = bty.get_boss_dialogue_name(boss_id)

    script = script_manager[ctenums.LocID.OZZIES_FORT_LAST_STAND]
    for ind, ct_str in enumerate(script.strings):
        string = ctstrings.CTString.ct_bytes_to_ascii(ct_str)
        if "OZZIE" in string:
            string = string.replace("OZZIE", ozzie_name.upper())
        if "Ozzie Pants" in string:
            string = string.replace("Ozzie Pants", ozzie_charm_name)
        if "FLEA" in string:
            string = string.replace("FLEA", flea_name.upper())
        if "Flea Vest" in string:
            string = string.replace("Flea Vest", flea_charm_name)
        if "SLASH" in string:
            string = string.replace("SLASH", slash_name.upper())
        if "Slasher 2" in string:
            string = string.replace("Slasher 2", slash_charm_name)

        new_ct_str = ctstrings.CTString.from_str(string)
        if new_ct_str != ct_str:
            new_ct_str = new_ct_str.translate(
                bytes.maketrans(b'\x05\x06', b'\xEF\xEF')
            )
            new_ct_str = ctstrings.get_width_adjusted_ct_string(new_ct_str, indent_new_lines=True)
        script.strings[ind] = new_ct_str

    loc_ids = (ctenums.LocID.OZZIES_FORT_FLEA_PLUS, ctenums.LocID.OZZIES_FORT_SUPER_SLASH)
    names = ("Flea", "Slash")
    repl_names = (flea_name, slash_name)

    for loc_id, name in zip(loc_ids, names):
        script = script_manager[loc_id]
        for ind, ct_str in enumerate(script.strings):
            string = ctstrings.CTString.ct_bytes_to_ascii(ct_str)
            if "FLEA" in string:
                string = string.replace("FLEA", flea_name.upper())
            if "Flea" in string:
                string = string.replace("Flea", flea_name)
            if "SLASH" in string:
                string = string.replace("SLASH", slash_name.upper())
            if "Slash" in string:
                string = string.replace("Slash", slash_name)
            new_ct_str = ctstrings.CTString.from_str(string)
            if new_ct_str != ct_str:
                new_ct_str = new_ct_str.translate(
                    bytes.maketrans(b'\x05\x06', b'\xEF\xEF')
                )
                new_ct_str = ctstrings.get_width_adjusted_ct_string(new_ct_str, indent_new_lines=True)
                script.strings[ind] = new_ct_str
            #     print(f"{ind:02X}:{ctstrings.CTString.ct_bytes_to_ascii(ct_str)}")
            #
            # input()



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




"""Module for Randomizing Equipment Stats"""
import typing
from collections.abc import Callable

from ctrando.arguments import gearrandooptions
from ctrando.arguments.gearrandooptions import DSItem
from ctrando.common import ctenums, ctrom, distribution
from ctrando.common.ctenums import ArmorEffects, WeaponEffects, BoostID
from ctrando.common.random import RNGType
from ctrando.items import itemdata


def normalize_ayla_fist(ct_rom: ctrom.CTRom):
    """
    Do not auto-equip Ayla with a new fist depending on level.
    Do not ignore equipping Ayla's fist in the Equip Item event command.
    """

    # There are many options for eliminating this check.
    # We're going to NOP out the part where the new fist is written in.
    # This will avoid conflicts with other possible ayla modifications.

    write_addrs = (0x01FAD3, 0x01FAEB, 0x01FB03)
    payload = b"\xEA\xEA\xEA"

    for write_addr in write_addrs:
        ct_rom.seek(write_addr)
        ct_rom.write(payload)

    # There's a special case for Ayla so she never equips a fist. Remove it
    ct_rom.seek(0x028DB6)
    ct_rom.write(b'\x80')

    # Modify the empty weapon 00 to be a fist so that Ayla sounds normal
    # on Blackbird
    ct_rom.seek(0x0D6D4C)
    ct_rom.write(b'\xE7')

    ct_rom.seek(0x0D6DAC)
    ct_rom.write(b'\xE8')


T5: typing.TypeAlias = itemdata.Type_05_Buffs
T6: typing.TypeAlias = itemdata.Type_06_Buffs
T8: typing.TypeAlias = itemdata.Type_08_Buffs
T9: typing.TypeAlias = itemdata.Type_09_Buffs


def get_random_good_accessory_effect(
        rng: RNGType
) -> itemdata.BuffIterable:
    """Pick out a random good buff for an accessory"""

    acc_buff_dist: dict[itemdata.BuffIterable, float] = {
        (T5.GREENDREAM,): 10,
        (T6.PROT_STOP,): 10,
        (T6.PROT_BLIND, T6.PROT_CHAOS, T6.PROT_HPDOWN, T6.PROT_LOCK,
         T6.PROT_POISON, T6.PROT_SLEEP, T6.PROT_SLOW, T6.PROT_STOP): 2,
        (T8.HASTE,): 1,
        (T9.BARRIER,): 10,
        (T9.SHIELD,): 10,
        (T9.BARRIER, T9.SHIELD): 2,
        (T9.SHADES,): 5,
        (T9.SPECS,): 1
    }

    buffs, weights = zip(*acc_buff_dist.items())
    battle_buffs = rng.choices(buffs, weights=weights, k=1)[0]
    return battle_buffs


def get_random_good_accessory_stat_boost(rng: RNGType) -> BoostID:
    """Pick out a random good stat boost for an accssory"""
    acc_boosts = (BoostID.SPEED_2, BoostID.MDEF_12, BoostID.HIT_10,
                  BoostID.MAGIC_6, BoostID.MAG_MDEF_5, BoostID.POWER_STAMINA_10)
    return rng.choice(acc_boosts)


def assign_random_hp_mp_mod(
        stats: itemdata.AccessoryStats,
        rng: RNGType
):
    """Pick out a random hp and/or mp mod for the given accessory stats."""
    is_stronger_buff = rng.random() < 0.5
    is_hp_only = rng.random() < 0.5
    is_both = rng.random() < 0.1

    if is_hp_only or is_both:
        stats.has_hp_mod = True
        stats.hp_mod = 50 if is_stronger_buff else 25

    if (not is_hp_only) or is_both:
        stats.has_mp_mod = True
        stats.mp_mod = 75 if is_stronger_buff else 50


def randomize_good_accessory_effects(
        item_db: itemdata.ItemDB,
        rng: RNGType
):
    """Put random effects on rocks."""
    for item_id in (ctenums.ItemID.BLUE_ROCK, ctenums.ItemID.BLACK_ROCK,
                    ctenums.ItemID.GOLD_ROCK, ctenums.ItemID.SILVERROCK,
                    ctenums.ItemID.WHITE_ROCK,
                    ctenums.ItemID.HERO_MEDAL):
        item = item_db[item_id]
        item.stats = get_random_acc_stats(0.4, 0.4, 0.2, rng)


def randomize_top_tier_gear(
        item_db: itemdata.ItemDB,
        rng: RNGType
):
    """Give random effects to top tier gear"""

    # Prismspecs can become Haste
    if rng.random() < 0.25:
        item = item_db[ctenums.ItemID.PRISMSPECS]
        item.stats.battle_buffs = [T8.HASTE]
        item.set_name_from_str("{acc}HasteSpecs")


def get_random_acc_stats(
        buff_prob: float,
        stat_prob: float,
        hp_mp_prob: float,
        rng: RNGType
) -> itemdata.AccessoryStats:
    """Returns a randomized AccessoryStats"""

    buff_thresh = buff_prob
    stat_thresh = stat_prob + buff_thresh
    hp_mp_thresh = hp_mp_prob + stat_thresh

    stats = itemdata.AccessoryStats()
    rand_type = rng.random()

    if rand_type < buff_thresh:
        battle_buffs = get_random_good_accessory_effect(rng)
        stats.has_battle_buff = True
        stats.battle_buffs = battle_buffs
    elif rand_type < stat_thresh:
        stats.has_stat_boost = True
        boost = get_random_good_accessory_stat_boost(rng)
        stats.stat_boost_index = boost
    elif rand_type < hp_mp_thresh:
        assign_random_hp_mp_mod(stats, rng)

    return stats


def modify_equipability(
        item_db: itemdata.ItemDB,
        prob_gain: float,
        prob_lose: float
):
    pass


def make_ds_replacement_weapons(
        item_db: itemdata.ItemDB,
        ds_weapon_pool: list[gearrandooptions.DSItem],
        replacement_chance: float,
        rng: RNGType
):
    """Possibly replace weapons with ds-exclusive equivalents"""

    # Rainbow to Dreamseeker
    if DSItem.DREAMSEEKER in ds_weapon_pool and rng.random() < replacement_chance:
        rainbow = item_db[ctenums.ItemID.RAINBOW]
        rainbow.stats.attack = 240
        rainbow.stats.critical_rate = 90
        rainbow.set_name_from_str("{blade}DreamSeekr")

    # Valk to Venus
    if DSItem.VENUS_BOW in ds_weapon_pool and rng.random() < replacement_chance:
        valk = item_db[ctenums.ItemID.VALKERYE]
        valk.stats.attack = 0
        # valk.stats.critical_rate = 0
        valk.stats.has_effect = True
        valk.stats.effect_id = WeaponEffects.VENUS_BOW
        valk.set_name_from_str("{bow}Venus Bow")

    # Wondershot to SpellSlinger or Turboshot
    wonder_targets = [DSItem.SPELLSLINGER, DSItem.TURBOSHOT]
    wonder_targets = [x for x in wonder_targets if x in ds_weapon_pool]
    if wonder_targets and rng.random() < replacement_chance:
        wondershot = item_db[ctenums.ItemID.WONDERSHOT]
        replacement = rng.choice(wonder_targets)
        if replacement == DSItem.SPELLSLINGER:
            wondershot.stats.effect_id = WeaponEffects.SPELLSLINGER
            wondershot.stats.attack = 0
            wondershot.set_name_from_str("{gun}Spellslngr")
        elif replacement == DSItem.TURBOSHOT:
            wondershot.stats.attack = 140
            wondershot.stats.has_effect = False
            wondershot.secondary_stats.has_stat_boost = True
            wondershot.stats.stat_boost_index = BoostID.SPEED_3
            wondershot.set_name_from_str("{gun}Turboshot")
        else:
            raise ValueError

    # Crisis to Apocalypse/Dragon
    crisis_targets = [DSItem.APOCALYPSE_ARM, DSItem.DRAGON_ARM]
    crisis_targets = [x for x in crisis_targets if x in ds_weapon_pool]
    if crisis_targets and ds_weapon_pool and rng.random() < replacement_chance:
        crisis_arm = item_db[ctenums.ItemID.CRISIS_ARM]
        replacement = rng.choice(crisis_targets)
        if replacement == DSItem.APOCALYPSE_ARM:
            crisis_arm.stats.attack = 0
            crisis_arm.stats.critical_rate = 10
            crisis_arm.stats.has_effect = True
            crisis_arm.stats.effect_id = WeaponEffects.CRIT_9999
            crisis_arm.set_name_from_str(f"{arm}Apoc. Arm")
        elif replacement == DSItem.DRAGON_ARM:
            crisis_arm.stats.has_effect = False
            crisis_arm.stats.attack = 170
            crisis_arm.stats.critical_rate = 10



    # Doomsickle to Judgement/Reaper
    doomsickle_targets = [
        x for x in (DSItem.JUDGEMENT_SCYTHE, DSItem.DREAMREAPER)
        if x in ds_weapon_pool
    ]
    if doomsickle_targets and rng.random() < replacement_chance:
        doomsickle = item_db[ctenums.ItemID.DOOMSICKLE]
        replacement = rng.choice(doomsickle_targets)
        if replacement == DSItem.JUDGEMENT_SCYTHE:
            doomsickle.stats.has_effect = WeaponEffects.STOP_60
            doomsickle.stats.attack = 155
            doomsickle.set_name_from_str("{scythe}JudgeScyth")
        elif replacement == DSItem.DREAMREAPER:
            doomsickle.stats.has_effect = WeaponEffects.CRIT_4X
            doomsickle.stats.attack = 180
            doomsickle.set_name_from_str("{scythe}Dreamreapr")
        else:
            raise ValueError


    # Demon hit to Dino Blade(ish)
    if DSItem.DINOBLADE in ds_weapon_pool and rng.random() < replacement_chance:
        demon_hit = item_db[ctenums.ItemID.DEMON_HIT]
        demon_hit.stats.attack = 160
        demon_hit.stats.has_effect = False
        demon_hit.secondary_stats.has_stat_boost = True
        demon_hit.secondary_stats.stat_boost_index = BoostID.POWER_5
        demon_hit.set_name_from_str("{sword}Dino Blade")


def make_ds_replacement_armors(
        item_db: itemdata.ItemDB,
        ds_item_pool: list[DSItem],
        replacement_chance: float,
        rng: RNGType
):
    """Possibly replace weapons with ds-exclusive equivalents"""
    # Gloom Cape -> Shadowplume Robe
    if DSItem.SHADOWPLUME_ROBE in ds_item_pool and rng.random() < replacement_chance:
        cape = item_db[ctenums.ItemID.GLOOM_CAPE]
        cape.stats.defense = 90
        cape.secondary_stats.stat_boost_index = BoostID.MDEF_20
        cape.stats.has_effect = True
        cape.stats.effect_id = ArmorEffects.BARRIER_SHIELD
        cape.set_name_from_str("{armor}ShadowRobe")

    # Moon Armor to Regal Plate
    if DSItem.REGAL_PLATE in ds_item_pool and rng.random() < replacement_chance:
        item = item_db[ctenums.ItemID.MOON_ARMOR]
        item.stats.defense = 88
        item.secondary_stats.stat_boost_index = BoostID.MDEF_STAMINA_10
        item.set_name_from_str("{armor}RegalPlate")

    # Prism Dress to Regal Gown
    if DSItem.REGAL_GOWN in ds_item_pool and rng.random() < replacement_chance:
        item = item_db[ctenums.ItemID.PRISMDRESS]
        item.stats.defense = 90
        item.stats.effect_id = ArmorEffects.BARRIER_SHIELD
        item.set_name_from_str("{armor}Regal Gown")

    # Nova Armor to Dragon Armor
    if DSItem.DRAGON_ARMOR in ds_item_pool and rng.random() < replacement_chance:
        item = item_db[ctenums.ItemID.NOVA_ARMOR]
        item.stats.defense = 83
        item.secondary_stats.stat_boost_index = BoostID.POWER_10
        item.stats.has_effect = False
        item.set_name_from_str("{armor}Drgn Armor")

    # Zodiac Cape to Reptite Dress
    if DSItem.REPTITE_DRESS in ds_item_pool and rng.random() < replacement_chance:
        item = item_db[ctenums.ItemID.ZODIACCAPE]
        item.stats.defense = 82
        item.secondary_stats.stat_boost_index = BoostID.MAGIC_10
        item.stats.has_effect = False
        item.set_name_from_str("{armor}Rept Dress")

    # Taban Suit to Elemental Aegis
    if DSItem.ELEMENTAL_AEGIS in ds_item_pool and rng.random() < replacement_chance:
        item = item_db[ctenums.ItemID.TABAN_SUIT]
        item.stats.defense = 92
        item.secondary_stats.elemental_protection_magnitude = 0
        item.secondary_stats.stat_boost_index = BoostID.NOTHING
        item.stats.has_effect = True
        item.stats.effect_id = ArmorEffects.IMMUNE_ELEMENTS
        item.set_name_from_str("{armor}Elem Aegis")


    def make_saurian_leather(item: itemdata.Item):
        item.stats.defense = 88
        item.secondary_stats.elemental_protection_magnitude = 0
        item.secondary_stats.stat_boost_index = BoostID.SPD_POW_3
        item.secondary_stats.set_equipable_by(list(ctenums.CharID))
        item.stats.has_effect = False
        item.stats.effect_id = ArmorEffects.NONE
        item.set_name_from_str("{armor}SaurLeathr")


    def make_dragonhead(item: itemdata.Item):
        item.stats.defense = 36
        item.secondary_stats.stat_boost_index = BoostID.POWER_5
        item.secondary_stats.elemental_protection_magnitude = 0
        item.secondary_stats.set_equipable_by(
            [ctenums.CharID.CRONO, ctenums.CharID.FROG, ctenums.CharID.ROBO, ctenums.CharID.MAGUS])
        item.stats.has_effect = False
        item.stats.effect_id = ArmorEffects.NONE
        item.set_name_from_str("{helm}DragonHead")


    def make_reptite_tiara(item: itemdata.Item):
        item.stats.defense = 35
        item.secondary_stats.elemental_protection_magnitude = 0
        item.secondary_stats.stat_boost_index = BoostID.MAGIC_5
        item.secondary_stats.set_equipable_by(
            [ctenums.CharID.MARLE, ctenums.CharID.LUCCA, ctenums.CharID.AYLA])
        item.stats.has_effect = False
        item.stats.effect_id = ArmorEffects.NONE
        item.set_name_from_str("{helm}Rept.Tiara")


    def make_masters_crown(item: itemdata.Item):
        item.stats.defense = 40
        item.secondary_stats.stat_boost_index = BoostID.NOTHING
        item.secondary_stats.set_equipable_by(
            [ctenums.CharID.CRONO, ctenums.CharID.FROG, ctenums.CharID.ROBO, ctenums.CharID.MAGUS])
        item.stats.has_effect = True
        item.stats.effect_id = ArmorEffects.MASTERS_CROWN
        item.set_name_from_str("{helm}MastrCrown")


    def make_angel_tiara(item: itemdata.Item):
        item.stats.defense = 36
        item.secondary_stats.stat_boost_index = BoostID.NOTHING
        item.secondary_stats.set_equipable_by(
            [ctenums.CharID.MARLE, ctenums.CharID.LUCCA, ctenums.CharID.AYLA])
        item.stats.has_effect = False
        item.stats.effect_id = ArmorEffects.ANGEL_TIARA
        item.set_name_from_str("{helm}AngelTiara")

    if DSItem.MASTERS_CROWN in ds_item_pool and rng.random() < replacement_chance:
        make_masters_crown(item_db[ctenums.ItemID.PRISM_HELM])

    if DSItem.ANGELS_TIARA in ds_item_pool and rng.random() < replacement_chance:
        make_angel_tiara(item_db[ctenums.ItemID.HASTE_HELM])


    good_helms = [
        ctenums.ItemID.RBOW_HELM, ctenums.ItemID.DARK_HELM, ctenums.ItemID.MERMAIDCAP,
        ctenums.ItemID.SIGHT_CAP, ctenums.ItemID.MEMORY_CAP, ctenums.ItemID.TIME_HAT
    ]

    replacement_helms = [
        x for x  in (DSItem.DRAGONHEAD, DSItem.REPTITE_TIARA)
        if x in ds_item_pool
    ]
    num_good_helms = len(replacement_helms)
    replaced_helms: list[ctenums.ItemID] = rng.sample(good_helms, num_good_helms)
    replacement_fns: list[Callable[[itemdata.Item], None]] = rng.sample([make_dragonhead, make_reptite_tiara],
                                                                        num_good_helms, )

    for helm_id, replacement_fn in zip(replaced_helms, replacement_fns):
        if rng.random() < replacement_chance:
            replacement_fn(item_db[helm_id])


    good_armors = [
        ctenums.ItemID.RUBY_ARMOR, ctenums.ItemID.RED_MAIL, ctenums.ItemID.BLACK_MAIL,
        ctenums.ItemID.BLUE_MAIL, ctenums.ItemID.WHITE_MAIL,
    ]

    if DSItem.SAURIAN_LEATHERS in ds_item_pool and rng.random() < replacement_chance:
        item_id = rng.choice(good_armors)
        make_saurian_leather(item_db[item_id])


def modify_bronze_fist(
        item_db: itemdata.ItemDB,
        bronze_fist_policy: gearrandooptions.BronzeFistPolicy,
        rng: RNGType
):
    """Modify the Bronze Fist according to settings"""
    if bronze_fist_policy == gearrandooptions.BronzeFistPolicy.VANILLA:
        return

    bronze_fist = item_db[ctenums.ItemID.BRONZEFIST]
    if bronze_fist_policy == gearrandooptions.BronzeFistPolicy.CRIT_4x:
        bronze_fist.stats.effect_id = WeaponEffects.CRIT_4X
    elif bronze_fist_policy == gearrandooptions.BronzeFistPolicy.RANDOM_OTHER:
        bronze_fist.stats.effect_id = rng.choice(
            [WeaponEffects.CRIT_4X, WeaponEffects.WONDERSHOT, WeaponEffects.DOOMSICKLE,
             WeaponEffects.CRISIS]
        )
        bronze_fist.secondary_stats.stat_boost_index = rng.choice(
            [BoostID.POWER_STAMINA_10, BoostID.MDEF_STAMINA_10,
             BoostID.MAGIC_10, BoostID.SPEED_1, BoostID.NOTHING]
        )


_special_atk_effects = (WeaponEffects.CRISIS, WeaponEffects.SPELLSLINGER,
                        WeaponEffects.CRIT_9999, WeaponEffects.VENUS_BOW)


def randomize_weapons_group(
        item_db: itemdata.ItemDB,
        group_options: gearrandooptions.WeaponRandoGroup,
        rng: RNGType
):
    weapon_pool = group_options.pool
    weapon_pool = sorted(weapon_pool)

    if (
            group_options.effect_scheme == gearrandooptions.GearRandoScheme.SHUFFLE_LINKED or
            group_options.boost_scheme == gearrandooptions.GearRandoScheme.SHUFFLE_LINKED
    ):
        rng.shuffle(weapon_pool)
        effects = [item_db[weapon].stats.effect_id for weapon in weapon_pool]
        boosts = [item_db[weapon].secondary_stats.stat_boost_index for weapon in weapon_pool]
    else:
        if group_options.effect_scheme == gearrandooptions.GearRandoScheme.SHUFFLE:
            effects = [item_db[weapon].stats.effect_id for weapon in weapon_pool]
            # boosts = [item_db[weapon].secondary_stats.stat_boost_index for weapon in weapon_pool]
            rng.shuffle(effects)
        elif group_options.effect_scheme == gearrandooptions.GearRandoScheme.RANDOM:
            effects = list(group_options.forced_effects)
            effect_dist = gearrandooptions.get_weapon_effect_distribution(
                group_options.random_effect_spec
            )
            while len(effects) < len(weapon_pool):
                effects.append(effect_dist.get_random_item(rng))
            rng.shuffle(effects)
        else:
            effects = []

        if group_options.boost_scheme == gearrandooptions.GearRandoScheme.SHUFFLE:
            boosts = [item_db[weapon].secondary_stats.stat_boost_index for weapon in weapon_pool]
            rng.shuffle(boosts)
        elif group_options.boost_scheme == gearrandooptions.GearRandoScheme.RANDOM:
            boosts = list(group_options.forced_boosts)
            boost_dist = gearrandooptions.get_stat_boot_distribution(
                group_options.random_boost_spec
            )
            while len(boosts) < len(weapon_pool):
                boosts.append(boost_dist.get_random_item(rng))
            rng.shuffle(boosts)
        else:
            boosts = []


    special_atk_effects = _special_atk_effects

    if group_options.effect_scheme != gearrandooptions.GearRandoScheme.NO_CHANGE:
        for item_id, effect in zip(weapon_pool, effects):
            cur_stats = item_db[item_id].stats
            cur_stats.has_effect = False

            if effect != WeaponEffects.NONE:
                cur_stats.has_effect = True
                cur_stats.effect_id = effect
                if effect in special_atk_effects:
                    cur_stats.attack = 0
                    if effect == WeaponEffects.CRIT_9999:
                        cur_stats.critical_rate = 10

    if group_options.boost_scheme != gearrandooptions.GearRandoScheme.NO_CHANGE:
        for item_id, boost in zip(weapon_pool, boosts):
            cur_secondary_stats = item_db[item_id].secondary_stats
            cur_secondary_stats.stat_boost_index = boost


def randomize_gear(
        item_db: itemdata.ItemDB,
        gear_rando_options: gearrandooptions.GearRandoOptions,
        rng: RNGType
):

    IID = ctenums.ItemID
    # weapon_pool = [
    #     IID.RAINBOW, IID.SHIVA_EDGE, IID.SWALLOW, IID.RED_KATANA, IID.SLASHER,
    #     IID.VALKERYE, IID.SIREN, IID.SONICARROW,
    #     IID.WONDERSHOT, IID.SHOCK_WAVE, IID.PLASMA_GUN,
    #     IID.TERRA_ARM, IID.CRISIS_ARM,
    #     IID.MASAMUNE_2, IID.BRAVESWORD, IID.RUNE_BLADE, IID.DEMON_HIT,  IID.PEARL_EDGE,
    #     IID.IRON_FIST, IID.BRONZEFIST,
    #     IID.DOOMSICKLE
    # ]

    ds_replacement_rate = gear_rando_options.ds_replacement_chance / 100

    make_ds_replacement_weapons(
        item_db, gear_rando_options.ds_item_pool,
        gear_rando_options.ds_replacement_chance / 100, rng)
    make_ds_replacement_armors(
        item_db, gear_rando_options.ds_item_pool,
        gear_rando_options.ds_replacement_chance / 100, rng)

    modify_bronze_fist(item_db, gear_rando_options.bronze_fist_policy, rng)

    for group in gear_rando_options.rando_groups:
        randomize_weapons_group(item_db, group, rng)

    special_atk_effects = _special_atk_effects
    # Do Ultimate weapon checks
    crisis_arm = item_db[ctenums.ItemID.CRISIS_ARM]
    if crisis_arm.stats.effect_id not in special_atk_effects and crisis_arm.stats.attack <= 1:
        crisis_arm.stats.attack = 170
        crisis_arm.stats.critical_rate = 10
        crisis_arm.set_name_from_str("{arm}Dragon Arm")
    if crisis_arm.stats.effect_id == WeaponEffects.CRIT_9999:
        crisis_arm.set_name_from_str("{arm}Apocal.Arm")

    # If spellslinger gets moved, fix it
    wondershot = item_db[ctenums.ItemID.WONDERSHOT]
    if wondershot.stats.effect_id not in special_atk_effects and wondershot.stats.attack == 0:
        wondershot.stats.attack = 250

    # If Venus bow gets moved, fix it
    valk = item_db[ctenums.ItemID.VALKERYE]
    if valk.stats.effect_id not in special_atk_effects and valk.stats.attack == 0:
        valk.stats.attack = 180


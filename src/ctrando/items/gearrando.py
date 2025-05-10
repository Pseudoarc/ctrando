"""Module for Randomizing Equipment Stats"""
# import random
import typing

from ctrando.common import ctenums, ctrom
from ctrando.common.ctenums import WeaponEffects
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
    ct_rom.write(b'\xE8')

    ct_rom.seek(0x0D6DAC)
    ct_rom.write(b'\xE7')


T5: typing.TypeAlias = itemdata.Type_05_Buffs
T6: typing.TypeAlias = itemdata.Type_06_Buffs
T8: typing.TypeAlias = itemdata.Type_08_Buffs
T9: typing.TypeAlias = itemdata.Type_09_Buffs


class BoostID(ctenums.StrIntEnum):
    NOTHING = 0x00
    SPEED_1 = 0x01
    HIT_2 = 0x02
    POWER_2 = 0x03
    STAMINA_2 = 0x04
    MAGIC_2 = 0x05
    MDEF_5 = 0x06
    SPEED_3 = 0x07
    HIT_10 = 0x08
    POWER_6 = 0x09
    MAGIC_6 = 0x0A
    MDEF_10 = 0x0B
    POWER_4 = 0x0C
    SPEED_2 = 0x0D
    MDEF_15 = 0x0E
    STAMINA_6 = 0x0F
    MAGIC_4 = 0x10
    MDEF_12 = 0x11
    MAG_MDEF_5 = 0x12
    POWER_STAMINA_10 = 0x13
    MDEF_5_DUP = 0x14
    MDEF_9 = 0x15


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


def randomize_weapons(
        item_db: itemdata.ItemDB,  # + Settings
        rng: RNGType
):

    IID = ctenums.ItemID
    weapon_pool = [
        IID.RAINBOW, IID.SHIVA_EDGE, IID.SWALLOW, IID.RED_KATANA, IID.SLASHER,
        IID.VALKERYE, IID.SIREN, IID.SONICARROW,
        IID.WONDERSHOT, IID.SHOCK_WAVE, IID.PLASMA_GUN,
        IID.TERRA_ARM, IID.CRISIS_ARM,
        IID.MASAMUNE_2, IID.BRAVESWORD, IID.RUNE_BLADE, IID.DEMON_HIT,  IID.PEARL_EDGE,
        IID.IRON_FIST, IID.BRONZEFIST,
        IID.DOOMSICKLE
    ]

    stats_pool = [
        (item_db[item_id].stats.get_copy(), item_db[item_id].secondary_stats.get_copy())
        for item_id in weapon_pool
    ]

    rng.shuffle(stats_pool)

    for item_id, (stats, sec_stats) in zip(weapon_pool, stats_pool):
        cur_stats = item_db[item_id].stats
        cur_secondary_stats = item_db[item_id].secondary_stats

        cur_stats.has_effect = False

        if stats.has_effect:
            cur_stats.has_effect = True
            cur_stats.effect_id = stats.effect_id
            if stats.effect_id == WeaponEffects.CRISIS:
                stats.attack = 1

        cur_secondary_stats.stat_boost_index = sec_stats.stat_boost_index

    # Do Ultimate weapon checks
    crisis_arm = item_db[ctenums.ItemID.CRISIS_ARM]
    if crisis_arm.stats.effect_id != WeaponEffects.CRISIS:
        crisis_arm.stats.attack = 170
        crisis_arm.stats.critical_rate = 10
        crisis_arm.set_name_from_str("{arm}Dragon Arm")


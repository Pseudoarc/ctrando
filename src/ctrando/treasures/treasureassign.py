"""
Module for assigning random treasure to RewardSpots
"""
import collections.abc
import typing
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import auto, Enum
import math

from ctrando.arguments.gearrandooptions import DSItem
from ctrando.locations.scriptmanager import ScriptManager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.arguments import treasureoptions, gearrandooptions
from ctrando.base.openworld import iokatradingpost
from ctrando.common import ctenums, ctrom, distribution, piecewiselinear as pwl
from ctrando.common.ctenums import TreasureID as TID
from ctrando.common.random import RNGType
from ctrando.items import itemdata
from ctrando.entranceshuffler import entrancefiller, maptraversal, regionmap
from ctrando.shops import shoprando
from ctrando.treasures import treasuretypes as ttypes, itemtiers, treasurespottiers
from ctrando.strings import ctstrings

@dataclass
class ChargeData:
    base_item: ctenums.ItemID
    upgrade_list: list[ctenums.ItemID] = field(default_factory=list)


_treasure_tier_dist: distribution.Distribution[shoprando.ItemTier] = distribution.Distribution(
    (5, shoprando.ItemTier.CONS_D),
    (34, shoprando.ItemTier.CONS_C),  # Staple consumables are here.
    (19, shoprando.ItemTier.CONS_B),
    (71, shoprando.ItemTier.CONS_A),
    (42, shoprando.ItemTier.CONS_S),
    (8, shoprando.ItemTier.WEAPON_D),
    (4, shoprando.ItemTier.WEAPON_C),
    (5, shoprando.ItemTier.WEAPON_B),
    (9, shoprando.ItemTier.WEAPON_A),
    (6, shoprando.ItemTier.WEAPON_S),
    (3, shoprando.ItemTier.ARMOR_D),
    (8, shoprando.ItemTier.ARMOR_C),
    (11, shoprando.ItemTier.ARMOR_B),
    (17, shoprando.ItemTier.ARMOR_A),
    (13, shoprando.ItemTier.ARMOR_S),
    (3, shoprando.ItemTier.ACCESSORY_D),
    (2, shoprando.ItemTier.ACCESSORY_C),
    (7, shoprando.ItemTier.ACCESSORY_B),
    (12, shoprando.ItemTier.ACCESSORY_A),
    (8, shoprando.ItemTier.ACCESSORY_S),
    (5, shoprando.ItemTier.ACCESSORY_ROCK),
    (1, shoprando.ItemTier.KEY_PROGRESSION)
)


_IID = ctenums.ItemID
_charge_progressions: list[tuple[ctenums.ItemID, ctenums.ItemID]] = [
    (_IID.RED_VEST, _IID.RED_MAIL),
    (_IID.BLUE_VEST, _IID.BLUE_MAIL),
    (_IID.WHITE_VEST, _IID.WHITE_MAIL),
    (_IID.BLACK_VEST, _IID.BLACK_MAIL),
    (_IID.KALI_BLADE, _IID.SHIVA_EDGE),
    (_IID.SIREN, _IID.VALKERYE),
    (_IID.NOVA_ARMOR, _IID.MOON_ARMOR),
    (_IID.SUN_SHADES, _IID.PRISMSPECS),
    (_IID.SILVERSTUD, _IID.GOLD_STUD),
    (_IID.SILVERERNG, _IID.GOLD_ERNG),
    (_IID.TABAN_VEST, _IID.TABAN_SUIT),
    (_IID.RUBY_VEST, _IID.RUBY_ARMOR),
    (_IID.SIGHT_CAP, _IID.VIGIL_HAT),
    (_IID.MEMORY_CAP, _IID.VIGIL_HAT),
    (_IID.TIME_HAT, _IID.VIGIL_HAT),
    (_IID.SPEED_BELT, _IID.DASH_RING),
    (_IID.RAGE_BAND, _IID.FRENZYBAND),
    (_IID.LUMIN_ROBE, _IID.ZODIACCAPE)
]


def fill_trading_post(
        assignment: dict[ctenums.TreasureID, ttypes.RewardType],
        item_pool: list[ttypes.RewardType],
        spot_pool: list[ctenums.TreasureID],
        rng: RNGType
):
    equipment_pool = list(set([
        reward for reward in item_pool
        if isinstance(reward, ctenums.ItemID) and reward < ctenums.ItemID.ACCESSORY_END_BC
    ]))

    post_spots = [
        TID.TRADING_POST_PETAL_FANG_BASE, TID.TRADING_POST_HORN_FEATHER_BASE,
        TID.TRADING_POST_PETAL_HORN_BASE, TID.TRADING_POST_FANG_FEATHER_BASE,
        TID.TRADING_POST_PETAL_FEATHER_BASE, TID.TRADING_POST_FANG_HORN_BASE,

        TID.TRADING_POST_PETAL_FANG_UPGRADE, TID.TRADING_POST_FANG_HORN_UPGRADE,
        TID.TRADING_POST_PETAL_HORN_UPGRADE, TID.TRADING_POST_FANG_FEATHER_UPGRADE,
        TID.TRADING_POST_PETAL_FEATHER_UPGRADE, TID.TRADING_POST_HORN_FEATHER_UPGRADE,
        TID.TRADING_POST_SPECIAL
    ]
    available_spots = [x for x in post_spots if x in spot_pool]

    num_taken_items = min(len(equipment_pool), len(available_spots))
    taken_items = rng.sample(equipment_pool, num_taken_items)
    for item in taken_items:
        item_pool.remove(item)

    while len(taken_items) < len(available_spots):
        while True:
            tier = rng.choice([shoprando.ItemTier.WEAPON_A, shoprando.ItemTier.ARMOR_A,
                               shoprando.ItemTier.WEAPON_B, shoprando.ItemTier.ARMOR_B])
            item = shoprando.get_item_dist_dict()[tier].get_random_item(rng)
            if item not in taken_items:
                break
        taken_items.append(item)

    rng.shuffle(taken_items)
    taken_items = sorted(taken_items, key=treasure_sort_key)

    for spot, item in zip(available_spots, taken_items):
        assignment[spot] = item
        spot_pool.remove(spot)



def make_trading_post_spoiler_string(
        petal_fang_item: ctenums.ItemID,
        petal_horn_item: ctenums.ItemID,
        petal_feather_item: ctenums.ItemID,
        fang_horn_item: ctenums.ItemID,
        fang_feather_item: ctenums.ItemID,
        horn_feather_item: ctenums.ItemID,
        item_man: itemdata.ItemDB
) -> str:

    return (
        'Many things for trade!{line break}'
        f'Petal, Fang: {item_man.item_dict[petal_fang_item].get_name_as_str(True)}'
        '{line break}'
        f'Petal, Horn: {item_man.item_dict[petal_horn_item].get_name_as_str(True)}'
        '{line break}'
        f'Petal, Feather: {item_man.item_dict[petal_feather_item].get_name_as_str(True)}'
        '{page break}'
        f'Fang, Horn: {item_man.item_dict[fang_horn_item].get_name_as_str(True)}'
        '{line break}'
        f'Fang, Feather: {item_man.item_dict[fang_feather_item].get_name_as_str(True)}'
        '{line break}'
        f'Horn, Feather: {item_man.item_dict[horn_feather_item].get_name_as_str(True)}'
        '{null}'
    )


def update_trading_post_costs(
        base_cost: int | None,
        upgrade_cost: int | None,
        special_cost: int | None,
        script_manager: ScriptManager
):
    script = script_manager[ctenums.LocID.IOKA_TRADING_POST]
    iokatradingpost.EventMod.set_materials_required(
        script, base_cost, upgrade_cost, special_cost
    )


def update_trading_post_strings(
        assignment: dict[ctenums.TreasureID, ttypes.RewardType],
        script_manager: ScriptManager,
        item_manager: itemdata.ItemDB
):
    script = script_manager[ctenums.LocID.IOKA_TRADING_POST]
    pos, cmd = script.find_command([0xBB], script.get_function_start(9, FID.ACTIVATE))

    base_string_id = cmd.args[0]
    new_string = make_trading_post_spoiler_string(
        assignment[TID.TRADING_POST_PETAL_FANG_BASE],
        assignment[TID.TRADING_POST_PETAL_HORN_BASE],
        assignment[TID.TRADING_POST_PETAL_FEATHER_BASE],
        assignment[TID.TRADING_POST_FANG_HORN_BASE],
        assignment[TID.TRADING_POST_FANG_FEATHER_BASE],
        assignment[TID.TRADING_POST_HORN_FEATHER_BASE],
        item_manager
    )
    script.strings[base_string_id] = ctstrings.CTString.from_str(new_string, True)

    pos += len(cmd)
    pos, cmd = script.find_command([0xBB], pos)
    upgrade_str_id = cmd.args[0]
    new_string = make_trading_post_spoiler_string(
        assignment[TID.TRADING_POST_PETAL_FANG_UPGRADE],
        assignment[TID.TRADING_POST_PETAL_HORN_UPGRADE],
        assignment[TID.TRADING_POST_PETAL_FEATHER_UPGRADE],
        assignment[TID.TRADING_POST_FANG_HORN_UPGRADE],
        assignment[TID.TRADING_POST_FANG_FEATHER_UPGRADE],
        assignment[TID.TRADING_POST_HORN_FEATHER_UPGRADE],
        item_manager
    )
    script.strings[upgrade_str_id] = ctstrings.CTString.from_str(new_string, True)


def fill_chargeable_chests(
        assignment: dict[ctenums.TreasureID, ttypes.RewardType],
        item_pool: list[ttypes.RewardType],
        spot_pool: list[ctenums.TreasureID],
        rng: RNGType
):
    """
    Assign treasures to the chargeable chests
    """

    charge_pairs = [
        (TID.TRUCE_INN_SEALED_600, TID.TRUCE_INN_SEALED_1000),
        (TID.GUARDIA_CASTLE_SEALED_600, TID.GUARDIA_CASTLE_SEALED_1000),
        (TID.PORRE_ELDER_SEALED_1, TID.PORRE_MAYOR_SEALED_1),
        (TID.PORRE_ELDER_SEALED_2, TID.PORRE_MAYOR_SEALED_2),
        (TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600, TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000),
        (TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600, TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000),
        (TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600, TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000)
    ]

    charge_progressions = [
        (base_item, charge_item) for (base_item, charge_item) in _charge_progressions
        if base_item in item_pool and charge_item in item_pool
    ]

    charge_options = list(set(
        charge_item for base_item, charge_item in charge_progressions
    ))

    charge_spot_pairs = [
        (base_spot, charge_spot) for (base_spot, charge_spot) in charge_pairs
        if base_spot in spot_pool and charge_spot in spot_pool
    ]
    rng.shuffle(charge_pairs)

    for (base_tid, charge_tid) in charge_spot_pairs:
        if not charge_options:
            break
        charge_choice = rng.choice(charge_options)
        charge_options.remove(charge_choice)

        possible_routes = [
            (base_item, charge_item) for base_item, charge_item in charge_progressions
            if charge_item == charge_choice
        ]
        base_item, charge_item = rng.choice(possible_routes)

        if base_tid in spot_pool:
            assignment[base_tid] =  base_item
            spot_pool.remove(base_tid)
            item_pool.remove(base_item)
            # print(f"Assign {base_item} to {base_tid}")

        if charge_tid in spot_pool:
            assignment[charge_tid] = charge_item
            spot_pool.remove(charge_tid)
            item_pool.remove(charge_item)
            # print(f"Assign {charge_item} to {charge_tid}")


def get_vanilla_treasure_pool(
    extra_ds_items: Sequence[gearrandooptions.DSItem],
) -> list[ttypes.RewardType]:

    base_assignment = ttypes.get_vanilla_assignment()
    item_pool = list(base_assignment.values())
    if gearrandooptions.DSItem.DRAGONS_TEAR in extra_ds_items:
        item_pool[item_pool.index(ctenums.ItemID.MEGAELIXIR)] = ctenums.ItemID.DRAGON_TEAR
    if gearrandooptions.DSItem.VALOR_CREST in extra_ds_items:
        item_pool[item_pool.index(ctenums.ItemID.ELIXIR)] = ctenums.ItemID.VALOR_CREST

    return item_pool


def get_random_treasure_pool(
        extra_ds_items: Sequence[gearrandooptions.DSItem],
        rng: RNGType
) -> list[ttypes.RewardType]:
    pool: list[ttypes.RewardType] = []

    dist_dict = shoprando.get_item_dist_dict()
    total_items = set()
    for tier, dist in dist_dict.items():
        if tier not in (shoprando.ItemTier.KEY_NONPROGRESSION, shoprando.ItemTier.KEY_PROGRESSION):
            total_items.update(dist.get_all_items())

    if DSItem.DRAGONS_TEAR not in extra_ds_items:
        total_items.discard(ctenums.ItemID.DRAGON_TEAR)

    if DSItem.VALOR_CREST not in extra_ds_items:
        total_items.discard(ctenums.ItemID.VALOR_CREST)

    item_list = list(total_items)
    for tid in ctenums.TreasureID:
        is_gold = rng.random() < 0.05

        if is_gold:
            gold_val = rng.randrange(1, 600) * 100
            pool.append(ttypes.Gold(gold_val))
        else:
            item = rng.choice(item_list)
            pool.append(item)

    return pool


_gold_inv_cdf = pwl.PiecewiseLinear(
    (0.0, 10),
    (0.25, 10),
    (0.50, 100),
    (0.75, 150),
    (0.90, 350),
    (0.95, 500),
    (0.99, 600)
)


def get_random_tiered_treasure_pool(
        extra_ds_items: Sequence[gearrandooptions.DSItem],
        rng: RNGType
) -> list[ttypes.RewardType]:
    pool: list[ttypes.RewardType] = []

    restricted_items = shoprando.get_items_in_tiers(
        [shoprando.ItemTier.KEY_PROGRESSION, shoprando.ItemTier.KEY_NONPROGRESSION]
    )

    if DSItem.VALOR_CREST not in extra_ds_items:
        restricted_items.append(ctenums.ItemID.VALOR_CREST)

    if DSItem.DRAGONS_TEAR not in extra_ds_items:
        restricted_items.append(ctenums.ItemID.DRAGON_TEAR)

    dist_dict = shoprando.get_restricted_dist_dict(restricted_items)
    tier_dist = _treasure_tier_dist

    remove_tiers =  [x for x in shoprando.ItemTier if x not in dist_dict]
    tier_dist = tier_dist.get_restricted_distribution(remove_tiers)

    for tid in ctenums.TreasureID:
        is_gold = rng.random() < 0.05

        if is_gold:
            x = rng.random()
            gold_val = _gold_inv_cdf(x) * 100
            pool.append(ttypes.Gold(gold_val))
        else:
            item = shoprando.get_random_tiered_item(tier_dist, dist_dict, rng)
            pool.append(item)

    return pool


_tier_dict: dict[int, list[ctenums.ItemID]] = {
    0: shoprando.get_items_in_tiers(
        (shoprando.ItemTier.CONS_D, shoprando.ItemTier.ACCESSORY_D,
         shoprando.ItemTier.WEAPON_D, shoprando.ItemTier.ARMOR_D,
         shoprando.ItemTier.KEY_NONPROGRESSION)
    ),
    1: shoprando.get_items_in_tiers(
        (
            shoprando.ItemTier.CONS_C, shoprando.ItemTier.ACCESSORY_C,
            shoprando.ItemTier.WEAPON_C, shoprando.ItemTier.ARMOR_C
        )
    ),
    2: shoprando.get_items_in_tiers(
        (
            shoprando.ItemTier.CONS_B, shoprando.ItemTier.ACCESSORY_B,
            shoprando.ItemTier.WEAPON_B, shoprando.ItemTier.ARMOR_B
        )
    ),
    3: shoprando.get_items_in_tiers(
        (
            shoprando.ItemTier.CONS_A, shoprando.ItemTier.ACCESSORY_A,
            shoprando.ItemTier.WEAPON_A, shoprando.ItemTier.ARMOR_A
        )
    ),
    4: shoprando.get_items_in_tiers(
        (
            shoprando.ItemTier.CONS_S, shoprando.ItemTier.ACCESSORY_S,
            shoprando.ItemTier.WEAPON_S, shoprando.ItemTier.ARMOR_S,
            shoprando.ItemTier.ACCESSORY_ROCK
        )
    )
}

def treasure_sort_key(
        treasure: ttypes.RewardType
) -> int:
    if isinstance(treasure, ttypes.Gold):
        return round(math.log(treasure/3500, 2))
    elif isinstance(treasure, ctenums.ItemID):
        for tier, item_list in _tier_dict.items():
            if treasure in item_list:
                return tier
        return 0


def default_assignment(
        existing_assignment: dict[ctenums.TreasureID, ctenums.ItemID],
        treasure_options: treasureoptions.TreasureOptions,
        extra_ds_items: Sequence[gearrandooptions.DSItem],
        exclude_pool: collections.abc.Sequence[ctenums.ItemID],
        region_map: regionmap.RegionMap,
        recruit_assignment: dict[ctenums.RecruitID, ctenums.CharID | None],
        starter_rewards: list[typing.Any],
        rng: RNGType
) -> dict[ctenums.TreasureID, ttypes.RewardType]:
    """
    Call after KIs are in.
    1) Fill chargeable chests before those items are taken out of the pool.
    2)
    """

    # This could be hardcoded
    base_assignment = ttypes.get_vanilla_assignment()
    assigned_spots, assigned_item_pool = zip(*{key: val for key, val in existing_assignment.items()
                                               if val != ctenums.ItemID.NONE}.items())

    assigned_item_pool = assigned_item_pool + tuple(exclude_pool)

    final_assignment: dict[ctenums.TreasureID, ttypes.RewardType] = {}
    final_assignment.update(existing_assignment)

    if treasure_options.loot_pool == treasureoptions.TreasurePool.VANILLA:
        item_pool = get_vanilla_treasure_pool(extra_ds_items)
    elif treasure_options.loot_pool == treasureoptions.TreasurePool.RANDOM:
        item_pool = get_random_treasure_pool(extra_ds_items, rng)
    elif treasure_options.loot_pool == treasureoptions.TreasurePool.RANDOM_TIERED:
        item_pool = get_random_tiered_treasure_pool(extra_ds_items, rng)
    else:
        raise ValueError

    forced_keys = entrancefiller.get_forced_key_items()

    for item in assigned_item_pool:
        # By default there are 2x Moonstone (SoS and Porre Mayor).
        if item in forced_keys:
            while item in item_pool:
                item_pool.remove(item)
        elif item in item_pool:
            item_pool.remove(item)
        # else:
        #     print(f"MISSING: {item}")

    spot_pool = [tid for tid in ctenums.TreasureID if tid not in assigned_spots]

    fill_good_stuff(item_pool, spot_pool, treasure_options.good_loot_spots, treasure_options.good_loot,
                    treasure_options.good_loot_rate, final_assignment, rng)
    fill_chargeable_chests(final_assignment, item_pool, spot_pool, rng)
    fill_trading_post(final_assignment, item_pool, spot_pool, rng)

    num_filler = max(0, len(spot_pool) - len(item_pool))
    if num_filler > 0:
        item_pool.extend([ctenums.ItemID.TONIC]*num_filler)

    if treasure_options.loot_assignment_scheme == treasureoptions.TreasureScheme.SHUFFLE:
        rng.shuffle(item_pool)

        for tid, reward in zip(spot_pool, item_pool):
            final_assignment[tid] = reward
    elif treasure_options.loot_assignment_scheme == treasureoptions.TreasureScheme.LOGIC_DEPTH:
        sphere_dict = maptraversal.get_sphere_dict(
            region_map, existing_assignment, recruit_assignment, starter_rewards
        )
        max_sphere = max(sphere_dict.values())
        sphere_tid_dict: dict[int, list[TID]] = {
            ind: [] for ind in range(max_sphere+1)
        }
        temp_spot_pool = set(spot_pool)
        for name, sphere in sphere_dict.items():
            if name in region_map.loc_region_dict:
                region = region_map.loc_region_dict[name]
                sphere_tid_dict[sphere].extend(
                    x for x in region.reward_spots
                    if isinstance(x, TID) and x in temp_spot_pool
                )

        sorted_tids: list[TID] = []
        for sphere, tid_list in sphere_tid_dict.items():
            rng.shuffle(tid_list)
            sorted_tids.extend(tid_list)

        sorted_pool = sorted(item_pool, key=treasure_sort_key)
        sorted_pool = sorted_pool[-len(sorted_tids):]

        for item, spot in zip(sorted_pool, sorted_tids):
            final_assignment[spot] = item

        num_shuffle = round(len(sorted_tids) * treasure_options.post_assign_shuffle_rate)
        shuffle_tids = rng.sample(sorted_tids, num_shuffle)
        vals = [final_assignment[tid] for tid in shuffle_tids]
        rng.shuffle(vals)

        for tid, val in zip(shuffle_tids, vals):
            final_assignment[tid] = val
    else:
        raise ValueError

    return final_assignment


def fill_good_stuff(
        item_pool: list[ctenums.ItemID],
        spot_pool: list[ctenums.TreasureID],
        good_stuff_spots: Sequence[ctenums.TreasureID],
        good_stuff_rewards: Sequence[ctenums.ItemID],
        good_stuff_rate: float,
        assignment_dict: dict[ctenums.TreasureID, ttypes.RewardType],
        rng: RNGType
):
    """
    Fill the good stuff spots with good stuff.
    """

    available_good_stuff_spots = [
        x for x in good_stuff_spots if x in spot_pool
    ]
    available_good_stuff = [x for x in item_pool if x in good_stuff_rewards]

    rng.shuffle(available_good_stuff)
    rng.shuffle(available_good_stuff_spots)
    num_spots = round(len(available_good_stuff_spots) * good_stuff_rate)
    for spot, reward in zip(available_good_stuff_spots[:num_spots], available_good_stuff):
        assignment_dict[spot] = reward
        item_pool.remove(reward)
        spot_pool.remove(spot)


def get_current_assignment(
        ct_rom: ctrom.CTRom,
        script_manager: ScriptManager,
        treasure_type_dict: typing.Optional[dict[ctenums.TreasureID, ttypes.RewardSpot]] = None
) -> dict[ctenums.TreasureID, ttypes.RewardType]:
    """
    Looks in the given state to get the currently assigned treasures.
    """
    if treasure_type_dict is None:
        treasure_type_dict = ttypes.get_base_treasure_dict()

    # for spot, treasure in treasure_type_dict.items():
    #     print(spot)
    #     treasure.read_reward_from_ct_rom(ct_rom, script_manager)

    assignment = {
        spot: treasure.read_reward_from_ct_rom(ct_rom, script_manager)
        for spot, treasure in treasure_type_dict.items()
    }

    return assignment




"""Implement the Default KI filler for CTRando."""
# import random
from copy import deepcopy

import arguments.logicoptions
from ctrando.common import ctenums
from logic.rewardstructure import RewardStructure
from ctrando.logic import simplerandomfiller, randomweighteddecayfiller
import logic.rewardfiller as rfill


def fill_key_items(
        reward_structure: RewardStructure,
        key_item_list: list[ctenums.ItemID],
        prohibited_spots: list[ctenums.TreasureID],
        forced_spots: list[ctenums.TreasureID],
        incentive_spots: list[ctenums.ItemID],
        incentive_factor: float,
        decay_factor: float
):
    num_iter = 0
    while num_iter < 1000:
        try:
            _fill_key_items_filler(
                reward_structure, key_item_list, prohibited_spots,
                forced_spots, incentive_spots, incentive_factor, decay_factor
            )
            return
        except rfill.FailedFillException:
            num_iter += 1

    raise rfill.FailedFillException

def _fill_key_items_filler(
        reward_structure: RewardStructure,
        key_item_list: list[ctenums.ItemID],
        prohibited_spots: list[ctenums.TreasureID],
        forced_spots: list[ctenums.TreasureID],
        incentive_spots: list[ctenums.ItemID],
        incentive_factor: float,
        decay_factor: float
):
    # Test input to make sure prohibited, forced, incentive are disjoint?

    working_rs = deepcopy(reward_structure)

    for tid in prohibited_spots:
        if tid in working_rs.treasure_dict:
            group_name = working_rs.treasure_dict[tid].group_name
            working_rs.group_dict[group_name].treasure_spots.remove(tid)
            del(working_rs.treasure_dict[tid])

    key_item_list.sort()

    # Create a RS with only the forced spots
    forced_spot_set = set(forced_spots)
    forced_rs = deepcopy(reward_structure)
    for name, group in forced_rs.group_dict.items():
        group.treasure_spots = group.treasure_spots.intersection(forced_spot_set)

    forced_rs.treasure_dict = {
        key: val for key,val in forced_rs.treasure_dict.items()
        if key in forced_spots
    }

    random.shuffle(key_item_list)
    forced_keys = key_item_list[0: len(forced_spots)]
    simplerandomfiller.fill_random(forced_rs, forced_keys)
    working_rs.update_assignment(forced_rs)

    if len(forced_spots) < len(key_item_list):
        remaining_keys = key_item_list[len(forced_spots):]
        spot_weights: dict[ctenums.TreasureID, float] = {
            spot: (incentive_factor if spot in incentive_spots else 1)
            for spot in ctenums.TreasureID
        }

        working_rs = randomweighteddecayfiller.fill_weighted_random_decay(
            working_rs, remaining_keys, spot_weights, decay_factor=decay_factor
        )

    working_rs.print_assignment()

    if rfill.prove_fill(working_rs):
        reward_structure.update_assignment(working_rs)
        print("Valid")
    else:
        print("Not Valid")
        raise rfill.FailedFillException


def default_fill_key_items(
        reward_structure: RewardStructure,
        logic_options: arguments.logicoptions.LogicOptions,
):
    """Fill the reward structure with key items according to logic options."""
    ItemID = ctenums.ItemID
    forced_key_items = [
        ItemID.C_TRIGGER, ItemID.CLONE,
        ItemID.PENDANT, ItemID.PENDANT_CHARGE, ItemID.DREAMSTONE,
        ItemID.RUBY_KNIFE, ItemID.JETSOFTIME,
        ItemID.TOOLS, ItemID.RAINBOW_SHELL,
        ItemID.PRISMSHARD, ItemID.JERKY, ItemID.JERKY,
        ItemID.BENT_HILT, ItemID.BENT_SWORD,
        ItemID.HERO_MEDAL, ItemID.MASAMUNE_1,
        # ItemID.MASAMUNE_2,  This doesn't unlock anything so not forced
        ItemID.TOMAS_POP, ItemID.MOON_STONE, ItemID.SUN_STONE,
        ItemID.BIKE_KEY, ItemID.SEED, ItemID.GATE_KEY
    ]

    key_items = forced_key_items + logic_options.additional_key_items

    TID = ctenums.TreasureID
    # Chargeable chests are forced excluded.
    forced_excluded_spots = [
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000,
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000,
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000,
        TID.TRUCE_INN_SEALED_1000, TID.GUARDIA_FOREST_SEALED_1000,
        TID.GUARDIA_CASTLE_SEALED_1000, TID.PORRE_MAYOR_SEALED_1,
        TID.PORRE_MAYOR_SEALED_2, TID.NORTHERN_RUINS_BASEMENT_1000
    ]

    excluded_spots = forced_excluded_spots + logic_options.excluded_spots
    excluded_spots = list(set(excluded_spots))
    forced_spots = list(logic_options.forced_spots)

    spot_entry = reward_structure.recruit_dict[ctenums.RecruitID.STARTER]
    group = reward_structure.group_dict[spot_entry.group_name]
    group.group_rewards = set(logic_options.starter_rewards)


#
# def default_fill_key_items(reward_structure: RewardStructure):
#     ItemID = ctenums.ItemID
#
#     key_items = [
#         ItemID.C_TRIGGER, ItemID.CLONE,
#         ItemID.PENDANT, ItemID.PENDANT_CHARGE, ItemID.DREAMSTONE,
#         ItemID.RUBY_KNIFE, ItemID.JETSOFTIME,
#         ItemID.TOOLS, ItemID.RAINBOW_SHELL,
#         ItemID.PRISMSHARD, ItemID.JERKY, ItemID.JERKY,
#         ItemID.BENT_HILT, ItemID.BENT_SWORD,
#         ItemID.HERO_MEDAL, ItemID.MASAMUNE_1, ItemID.MASAMUNE_2,
#         ItemID.TOMAS_POP, ItemID.MOON_STONE, ItemID.SUN_STONE,
#         ItemID.BIKE_KEY, ItemID.SEED, ItemID.GATE_KEY
#     ]
#
#     TID = ctenums.TreasureID
#     prohibited_spots = [
#         TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000,
#         TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000,
#         TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000,
#         TID.TRUCE_INN_SEALED_1000, TID.GUARDIA_FOREST_SEALED_1000,
#         TID.GUARDIA_CASTLE_SEALED_1000, TID.PORRE_MAYOR_SEALED_1,
#         TID.PORRE_MAYOR_SEALED_2, TID.NORTHERN_RUINS_BASEMENT_1000
#     ]
#
#     # Dreamstone?  JoT?  Gate Key?
#     forced_spots = [
#         TID.EOT_GASPAR_REWARD,  # Trigger
#         TID.BEKKLER_KEY,  # Clone
#         TID.FAIR_PENDANT, TID.ZEAL_MAMMON_MACHINE,  # Pendant, charge
#         TID.MT_WOE_KEY,  # Knife
#         TID.LAZY_CARPENTER,  # Tools
#         TID.GIANTS_CLAW_KEY,  # Shell
#         TID.KINGS_TRIAL_KEY,  # Shard
#         TID.YAKRAS_ROOM, # TID.ZENAN_BRIDGE_CHEF,
#         TID.SNAIL_STOP_KEY,  # Jerky x2
#         TID.DENADORO_MTS_KEY,   # Blade
#         TID.FROGS_BURROW_LEFT,  # Hilt
#         TID.MELCHIOR_FORGE_MASA,  # Masa
#         TID.CYRUS_GRAVE_KEY,  # Masa2
#         TID.TATA_REWARD,  # Medal
#         TID.FIONA_KEY, # TID.TOMA_REWARD,  # Pop
#         TID.SUN_KEEP_2300,  # Moonstone
#         TID.JERKY_GIFT,  # Also Moonstone... makes room for JoT/Dreamstone
#         TID.ARRIS_DOME_DOAN_KEY,  # Bike Key
#         TID.ARRIS_DOME_FOOD_LOCKER_KEY,  # Seed
#         TID.REPTITE_LAIR_KEY,  # Like Rbow Shell
#         TID.TABAN_GIFT_VEST,   # Like Gate Key
#         TID.GENO_DOME_BOSS_1,  # Like JoT
#     ]

    num_iterations = 0

    while num_iterations < 1000:
        try:
            fill_key_items(reward_structure, key_items,
                           excluded_spots, forced_spots, [],
                           1, 0.3)
            break
        except rfill.FailedFillException:
            pass



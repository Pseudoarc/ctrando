"""
Module for assigning random treasure to RewardSpots
"""
import typing
from collections.abc import Sequence
from dataclasses import dataclass, field
from enum import auto, Enum
from ctrando.locations.scriptmanager import ScriptManager


from ctrando.arguments import treasureoptions
from ctrando.common import ctenums, ctrom
from ctrando.common.ctenums import TreasureID as TID
from ctrando.common.random import RNGType
from ctrando.treasures import treasuretypes as ttypes, itemtiers, treasurespottiers


@dataclass
class ChargeData:
    base_item: ctenums.ItemID
    upgrade_list: list[ctenums.ItemID] = field(default_factory=list)


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


def default_assignment(
        existing_assignment: dict[ctenums.TreasureID, ctenums.ItemID],
        treasure_options: treasureoptions.TreasureOptions,
        rng: RNGType
) -> dict[ctenums.TreasureID, ttypes.RewardType]:
    """
    Call after KIs are in.
    1) Fill chargeable chests before those items are taken out of the pool.
    2)
    """

    # This could be hardcoded
    base_assignment = ttypes.get_vanilla_assignment()


    # This should only
    assigned_spots, assigned_item_pool = zip(*{key: val for key, val in existing_assignment.items()
                                               if val != ctenums.ItemID.NONE}.items())
    final_assignment: dict[ctenums.TreasureID, ttypes.RewardType] = {}
    final_assignment.update(existing_assignment)

    item_pool = list(base_assignment.values())
    for item in assigned_item_pool:
        # By default there are 2x Moonstone (SoS and Porre Mayor).
        while item in item_pool:
            item_pool.remove(item)
        # else:
        #     print(f"MISSING: {item}")

    # Do some manual item pool manipulation
    item_pool[item_pool.index(ctenums.ItemID.MEGAELIXIR)] = ctenums.ItemID.BRONZEFIST
    item_pool[item_pool.index(ctenums.ItemID.ELIXIR)] = ctenums.ItemID.IRON_FIST
    item_pool[item_pool.index(ctenums.ItemID.HYPERETHER)] = ctenums.ItemID.RUBY_ARMOR

    spot_pool = [
        tid for tid in base_assignment if tid not in assigned_spots
    ]

    fill_chargeable_chests(final_assignment, item_pool, spot_pool, rng)
    fill_good_stuff(item_pool, spot_pool, treasure_options.good_loot_spots, treasure_options.good_loot,
                    treasure_options.good_loot_rate, final_assignment, rng)
    rng.shuffle(item_pool)

    for tid, reward in zip(spot_pool, item_pool):
        final_assignment[tid] = reward

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

    # print(len(available_good_stuff_spots))
    # print(len(available_good_stuff))
    # input()

    rng.shuffle(available_good_stuff)
    rng.shuffle(available_good_stuff_spots)
    num_spots = round(len(available_good_stuff_spots) * good_stuff_rate)
    for spot, reward in zip(available_good_stuff_spots[:num_spots], available_good_stuff):
        assignment_dict[spot] = reward
        item_pool.remove(reward)
        #
        # print(spot)
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




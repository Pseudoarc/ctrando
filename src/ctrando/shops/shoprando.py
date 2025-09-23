import copy
import enum
import math
import typing

from ctrando.items import itemdata
from ctrando.shops import shoptypes
from ctrando.arguments import shopoptions, gearrandooptions
from ctrando.common import ctenums, distribution
from ctrando.common.ctenums import ItemID as IID
from ctrando.common.random import RNGType


def randomize_shops(
        shop_manager: shoptypes.ShopManager,
        shop_options: shopoptions.ShopOptions
):
    ...


class ItemTier(enum.Enum):
    CONS_D = enum.auto()
    CONS_C = enum.auto()
    CONS_B = enum.auto()
    CONS_A = enum.auto()
    CONS_S = enum.auto()
    WEAPON_D = enum.auto()
    WEAPON_C = enum.auto()
    WEAPON_B = enum.auto()
    WEAPON_A = enum.auto()
    WEAPON_S = enum.auto()
    ARMOR_D = enum.auto()
    ARMOR_C = enum.auto()
    ARMOR_B = enum.auto()
    ARMOR_A = enum.auto()
    ARMOR_S = enum.auto()
    ACCESSORY_D = enum.auto()
    ACCESSORY_C = enum.auto()
    ACCESSORY_B = enum.auto()
    ACCESSORY_A = enum.auto()
    ACCESSORY_S = enum.auto()
    ACCESSORY_ROCK = enum.auto()
    KEY_NONPROGRESSION = enum.auto()
    KEY_PROGRESSION = enum.auto()


ItemDist = distribution.Distribution[IID]


_item_dist_dict: dict[ItemTier, ItemDist] = {
    ItemTier.CONS_D: distribution.Distribution[IID](
        (1, [IID.POWER_MEAL, IID.TONIC])
    ),
    ItemTier.CONS_C: distribution.Distribution[IID](
        (1, [IID.MID_TONIC, IID.SHELTER, IID.REVIVE, IID.HEAL])
    ),
    ItemTier.CONS_B: distribution.Distribution[IID](
        (1, [IID.FULL_TONIC, IID.ETHER])
    ),
    ItemTier.CONS_A: distribution.Distribution[IID](
        (1, [IID.MID_ETHER, IID.LAPIS, IID.BARRIER, IID.SHIELD, IID.MAGIC_TAB,
             IID.POWER_TAB])
    ),
    ItemTier.CONS_S: distribution.Distribution[IID](
        (5, IID.FULL_ETHER),
        (3, IID.HYPERETHER),
        (2, IID.ELIXIR),
        (1, IID.MEGAELIXIR)
    ),
    ItemTier.ACCESSORY_D: distribution.Distribution[IID](
        (1, [IID.WALLET, IID.CHARM_TOP, IID.THIRD_EYE])
    ),
    ItemTier.ACCESSORY_C: distribution.Distribution[IID](
        (1, [IID.RIBBON, IID.POWERGLOVE, IID.DEFENDER, IID.SIGHTSCOPE])
    ),
    ItemTier.ACCESSORY_B: distribution.Distribution[IID](
        (1, [IID.BANDANA, IID.POWERSCARF, IID.MAGICSCARF, IID.MUSCLERING, IID.BERSERKER, IID.RAGE_BAND])
    ),
    ItemTier.ACCESSORY_A: distribution.Distribution[IID](
        (1, [IID.HIT_RING, IID.POWER_RING, IID.MAGIC_RING, IID.FRENZYBAND, IID.WALL_RING,
             IID.MAGIC_SEAL, IID.SPEED_BELT, IID.SILVERSTUD, IID.SILVERERNG])
    ),
    ItemTier.ACCESSORY_S: distribution.Distribution[IID](
        (1, IID.GREENDREAM),
        (3, IID.POWER_SEAL),
        (1, IID.GOLD_ERNG),
        (1, IID.GOLD_STUD),
        (2, IID.SUN_SHADES),
        (1, IID.PRISMSPECS),
        (1, IID.DASH_RING),
        (1, IID.AMULET),
        (2, IID.FLEA_VEST),
        (1, IID.DRAGON_TEAR),
        (1, IID.VALOR_CREST),
    ),
    ItemTier.WEAPON_D: distribution.Distribution[IID](
        (1, [IID.WOOD_SWORD, IID.IRON_BLADE, IID.STEELSABER, IID.LODE_SWORD, IID.BOLT_SWORD,
             IID.BRONZE_BOW, IID.IRON_BOW, IID.LODE_BOW,
             IID.AIR_GUN, IID.DART_GUN, IID.AUTO_GUN,
             IID.TIN_ARM, IID.HAMMER_ARM,
             IID.BRONZEEDGE, IID.IRON_SWORD])
    ),
    ItemTier.WEAPON_C: distribution.Distribution[IID](
        (1, [IID.RED_KATANA, IID.FLINT_EDGE, IID.AEON_BLADE,
             IID.ROBIN_BOW, IID.SAGE_BOW,
             IID.PLASMA_GUN, IID.RUBY_GUN,
             IID.MIRAGEHAND, IID.STONE_ARM, IID.DOOMFINGER, IID.MAGMA_HAND,
             IID.FLASHBLADE, IID.PEARL_EDGE])
    ),
    ItemTier.WEAPON_B: distribution.Distribution[IID](
        (1, [IID.DEMON_EDGE, IID.ALLOYBLADE, IID.STAR_SWORD,
             IID.DREAM_BOW, IID.COMETARROW,
             IID.DREAM_GUN, IID.MEGABLAST,
             IID.BIG_HAND, IID.KAISER_ARM, IID.GIGA_ARM,
             IID.RUNE_BLADE, IID.DEMON_HIT,
             IID.DARKSCYTHE])
    ),
    ItemTier.WEAPON_A: distribution.Distribution[IID](
        (1, [IID.VEDICBLADE, IID.KALI_BLADE, IID.SHIVA_EDGE, IID.SLASHER_2]),
        (1, [IID.SONICARROW, IID.SIREN]),
        (1, IID.SHOCK_WAVE),
        (1, IID.TERRA_ARM),
        (1, IID.BRAVESWORD),
        (1, IID.STARSCYTHE)
    ),
    ItemTier.WEAPON_S: distribution.Distribution[IID](
        (1, [IID.RAINBOW, IID.VALKERYE, IID.WONDERSHOT, IID.CRISIS_ARM,
             IID.DOOMSICKLE, #IID.MASAMUNE_2
            ])
    ),
    ItemTier.ARMOR_D: distribution.Distribution[IID](
        (1, [IID.HIDE_TUNIC, IID.KARATE_GI, IID.BRONZEMAIL, IID.MAIDENSUIT,
             IID.IRON_SUIT,
             IID.HIDE_CAP, IID.BRONZEHELM, IID.IRON_HELM, IID.BERET]),
    ),
    ItemTier.ARMOR_C: distribution.Distribution[IID](
        (1, [IID.TITAN_VEST, IID.GOLD_SUIT, IID.DARK_MAIL, IID.MIST_ROBE,
             IID.GOLD_HELM, IID.ROCK_HELM])
    ),
    ItemTier.ARMOR_B: distribution.Distribution[IID](
        (1, [IID.RUBY_VEST, IID.MESO_MAIL, IID.LUMIN_ROBE, IID.FLASH_MAIL,
             IID.WHITE_VEST, IID.BLACK_VEST, IID.BLUE_VEST, IID.RED_VEST,
             IID.CERATOPPER, IID.GLOW_HELM, IID.TABAN_HELM])
    ),
    ItemTier.ARMOR_A: distribution.Distribution[IID](
        (1, [IID.LODE_VEST, IID.AEON_SUIT, IID.TABAN_VEST, IID.WHITE_MAIL,
             IID.BLACK_MAIL, IID.BLUE_MAIL, IID.RED_MAIL,
             IID.LODE_HELM, IID.AEON_HELM, IID.DOOM_HELM,
             IID.DARK_HELM, IID.RBOW_HELM, IID.MERMAIDCAP,
             IID.SIGHT_CAP, IID.MEMORY_CAP, IID.TIME_HAT])
    ),
    ItemTier.ARMOR_S: distribution.Distribution[IID](
        (1, IID.ZODIACCAPE),
        (1, IID.NOVA_ARMOR),
        (1, IID.PRISMDRESS),
        (3, IID.MOON_ARMOR),
        (1, IID.GLOOM_CAPE),
        (1, IID.TABAN_SUIT),
        (3, IID.VIGIL_HAT),
        (1, IID.PRISM_HELM),
        (1, IID.GLOOM_HELM),
        (1, IID.HASTE_HELM),
        (1, IID.SAFE_HELM),
    ),
    ItemTier.KEY_NONPROGRESSION: distribution.Distribution[IID](
        (1, [IID.PETAL, IID.FANG, IID.HORN, IID.FEATHER,
             IID.PETALS_2, IID.FANGS_2, IID.HORNS_2, IID.FEATHERS_2,])
    )
}


_tier_dist: distribution.Distribution[ItemTier] = distribution.Distribution(
    (5, ItemTier.CONS_D),
    (30, ItemTier.CONS_C),  # Staple consumables are here.
    (5, ItemTier.CONS_B),
    (2, ItemTier.CONS_A),
    (1, ItemTier.CONS_S),
    (5, ItemTier.WEAPON_D),
    (10, ItemTier.WEAPON_C),
    (5, ItemTier.WEAPON_B),
    (2, ItemTier.WEAPON_A),
    (1, ItemTier.WEAPON_S),
    (5, ItemTier.ARMOR_D),
    (10, ItemTier.ARMOR_C),
    (5, ItemTier.ARMOR_B),
    (2, ItemTier.ARMOR_A),
    (1, ItemTier.ARMOR_S),
    (5, ItemTier.ACCESSORY_D),
    (10, ItemTier.ACCESSORY_C),
    (5, ItemTier.ACCESSORY_B),
    (2, ItemTier.ACCESSORY_A),
    (1, ItemTier.ACCESSORY_S),

)

# https://maxhalford.github.io/blog/weighted-sampling-without-replacement/


def get_random_tiered_item(rng: RNGType) -> ctenums.ItemID:
    tier = _tier_dist.get_random_item(rng)
    dist = _item_dist_dict[tier]
    item_id = dist.get_random_item(rng)

    return item_id


def get_random_tiered_shop_items(
        capacity: int,
        restricted_items: list[ctenums.ItemID],
        rng: RNGType,
) -> list[ctenums.ItemID]:
    chosen_items: list[ctenums.ItemID] = []

    while len(chosen_items) < capacity:
        next_item = get_random_tiered_item(rng)
        if next_item not in chosen_items and next_item not in restricted_items:
            chosen_items.append(next_item)

    return chosen_items


_crono_weapons = [
    IID.MOP, IID.WOOD_SWORD, IID.IRON_BLADE, IID.STEELSABER, IID.LODE_SWORD,
    IID.BOLT_SWORD, IID.RED_KATANA, IID.FLINT_EDGE, IID.DARK_SABER,
    IID.SLASHER, IID.AEON_BLADE,
    IID.DEMON_EDGE, IID.ALLOYBLADE, IID.STAR_SWORD, IID.VEDICBLADE,
    IID.KALI_BLADE, IID.SLASHER_2, IID.SWALLOW, IID.RAINBOW
]
_marle_weapons = [
    IID.BRONZE_BOW, IID.IRON_BOW, IID.LODE_BOW, IID.ROBIN_BOW,
    IID.SAGE_BOW, IID.DREAM_BOW, IID.COMETARROW, IID.SONICARROW,
    IID.SIREN, IID.VALKERYE
]
_lucca_weapons = [
    IID.AIR_GUN, IID.DART_GUN, IID.AUTO_GUN, IID.PICOMAGNUM,
    IID.PLASMA_GUN, IID.RUBY_GUN, IID.GRAEDUS, IID.DREAM_GUN, IID.MEGABLAST,
    IID.SHOCK_WAVE, IID.WONDERSHOT
]
_robo_weapons = [
    IID.TIN_ARM, IID.HAMMER_ARM, IID.MIRAGEHAND, IID.STONE_ARM,
    IID.DOOMFINGER, IID.MAGMA_HAND, IID.MEGATONARM, IID.BIG_HAND,
    IID.KAISER_ARM, IID.GIGA_ARM, IID.TERRA_ARM, IID.CRISIS_ARM
]
_frog_weapons = [
    IID.BRONZEEDGE, IID.IRON_SWORD, IID.MASAMUNE_1, IID.FLASHBLADE,
    IID.PEARL_EDGE, IID.RUNE_BLADE, IID.DEMON_HIT, IID. BRAVESWORD,
    IID.MASAMUNE_2
]
_magus_weapons = [
    IID.DARKSCYTHE, IID.HURRICANE, IID.DOOMSICKLE
]


def shop_item_sort_index(item_id: ctenums.ItemID):

    weapon_lists: list[list[IID]] = [
        _crono_weapons, _marle_weapons, _lucca_weapons, _robo_weapons, _frog_weapons,
        _magus_weapons
    ]

    cur_index = 0
    for weapon_list in weapon_lists:
        if item_id in weapon_list:
            return cur_index + weapon_list.index(item_id)
        cur_index += len(weapon_list)

    return item_id

# Some shop peculiarities:
# - Kajar Shop (0xA) copies the Enhasa shop (0xB) until the charged pendant is obtained
# - Last Village Shop (0x7) upgrades to shop 0x9 after the Blackbird in vanilla.
#   In rando, it's always shop 0x9.
# This means that logic-wise there are no permanently missable shops.


def randomize_shop_inventory(
        shop_manager: shoptypes.ShopManager,
        shop_options: shopoptions.ShopOptions,
        ds_item_pool: list[gearrandooptions.DSItem],
        rng: RNGType
):

    if shop_options.shop_inventory_randomization == shopoptions.ShopInventoryType.VANILLA:
        return

    no_assign_shop_ids = [ctenums.ShopID.EMPTY_12, ctenums.ShopID.EMPTY_14,
                          ctenums.ShopID.LAST_VILLAGE]
    if shop_options.shop_inventory_randomization == shopoptions.ShopInventoryType.SHUFFLE:

        shop_ids = [shop_id for shop_id in ctenums.ShopID
                    if shop_id not in no_assign_shop_ids]
        inventories = [
            copy.deepcopy(shop_manager.shop_dict[shop_id])
            for shop_id in shop_ids
        ]
        rng.shuffle(shop_ids)
        for shop_id, inventory in zip(shop_ids, inventories):
            shop_manager.shop_dict[shop_id] = inventory
    else:
        # Get shop capacities
        shop_capacity_dict = {
            shop_id: len(shop_manager.shop_dict[shop_id])
            for shop_id in ctenums.ShopID
            if shop_id not in no_assign_shop_ids
        }

        if shop_options.shop_capacity_randomization == shopoptions.ShopCapacityType.SHUFFLE:
            new_capacities = list(shop_capacity_dict.values())
            rng.shuffle(new_capacities)
            shop_capacity_dict = dict(zip(shop_capacity_dict.keys(), new_capacities))
        elif shop_options.shop_inventory_randomization == shopoptions.ShopCapacityType.RANDOM:
            shop_capacity_dict = {
                key: rng.randrange(2, 10)
                for key in shop_capacity_dict
            }

        item_pool = list(ctenums.ItemID)
        removed_items = shop_options.not_buyable_items + shopoptions.ShopOptions.unused_items
        if gearrandooptions.DSItem.DRAGONS_TEAR not in ds_item_pool:
            removed_items += ctenums.ItemID.DRAGON_TEAR
        if gearrandooptions.DSItem.VALOR_CREST not in ds_item_pool:
            removed_items += ctenums.ItemID.VALOR_CREST

        item_pool = [
            item_id for item_id in item_pool
            if item_id not in removed_items and item_id not in shop_options.not_buyable_items
        ]

        inv_type = shop_options.shop_inventory_randomization
        for shop_id, capacity in shop_capacity_dict.items():
            if inv_type == shopoptions.ShopInventoryType.TIERED_RANDOM:
                new_items = get_random_tiered_shop_items(capacity,
                                                         shop_options.not_buyable_items,
                                                         rng)
            elif inv_type == shopoptions.ShopInventoryType.FULL_RANDOM:
                new_items = rng.sample(item_pool, k=capacity)
            else:
                raise ValueError

            new_items = sorted(new_items, key=shop_item_sort_index)
            shop_manager.shop_dict[shop_id] = new_items


def set_balanced_prices(
        item_man: itemdata.ItemDB
):
    prices: dict[ctenums.ItemID, int] = {
        ctenums.ItemID.ZODIACCAPE: 40000,
        ctenums.ItemID.NOVA_ARMOR: 65000,
        ctenums.ItemID.PRISMDRESS: 65000,
        ctenums.ItemID.MOON_ARMOR: 40000,
        ctenums.ItemID.RUBY_ARMOR: 30000,
        ctenums.ItemID.GLOOM_CAPE: 20000,
        ctenums.ItemID.WHITE_MAIL: 20000,
        ctenums.ItemID.BLACK_MAIL: 20000,
        ctenums.ItemID.BLUE_MAIL: 20000,
        ctenums.ItemID.RED_MAIL: 20000,
        ctenums.ItemID.PRISM_HELM: 65000,
        ctenums.ItemID.GLOOM_HELM: 65000,
        ctenums.ItemID.SAFE_HELM: 40000,
        ctenums.ItemID.SIGHT_CAP: 30000,
        ctenums.ItemID.MEMORY_CAP: 20000,
        ctenums.ItemID.TIME_HAT: 25000,
        ctenums.ItemID.VIGIL_HAT: 50000,
        ctenums.ItemID.OZZIEPANTS: 10000,
        ctenums.ItemID.RBOW_HELM: 30000,
        ctenums.ItemID.MERMAIDCAP: 30000,
    }

    for item_id, price in prices.items():
        item_man.item_dict[item_id].price = price


def set_max_prices(
        item_man: itemdata.ItemDB
):
    for item_id in ctenums.ItemID:
        if item_id in item_man.item_dict:
            item_man.item_dict[item_id].price = 65000


def update_unsellable_prices(
        item_man: itemdata.ItemDB
):
    key_items = [
        IID.MASAMUNE_1, IID.MASAMUNE_2, IID.BENT_HILT, IID.BENT_SWORD, IID.DREAMSTONE,
        IID.SEED, IID.BIKE_KEY, IID. PENDANT, IID.GATE_KEY, IID.PRISMSHARD,
        IID.C_TRIGGER, IID.TOOLS, IID.JERKY, IID.RACE_LOG, IID.MOON_STONE,
        IID.SUN_STONE, IID.RUBY_KNIFE, IID.YAKRA_KEY, IID.CLONE, IID.TOMAS_POP,
        IID.PENDANT_CHARGE, IID.JETSOFTIME, IID.RAINBOW_SHELL, IID.HERO_MEDAL
    ]

    for key_item in key_items:
        item_man[key_item].price = 65000

    # Completely made-up, moslty-arbitrary prices
    item_man[IID.POWER_MEAL].price = 100
    item_man[IID.SLASHER].price = 20000
    item_man[IID.SLASHER_2].price = 45000
    item_man[IID.TABAN_VEST].price = 20000
    item_man[IID.TABAN_HELM].price = 10000
    item_man[IID.TABAN_SUIT].price = 65000
    item_man[IID.OZZIEPANTS].price = 65000
    item_man[IID.BANDANA].price = 5000
    item_man[IID.RIBBON].price = 1000
    item_man[IID.POWERGLOVE].price = 1000
    item_man[IID.DEFENDER].price = 1000
    item_man[IID.MAGICSCARF].price = 5000
    item_man[IID.AMULET].price = 65000
    item_man[IID.DASH_RING].price = 65000
    item_man[IID.HIT_RING].price = 10000
    item_man[IID.POWER_RING].price = 5000
    item_man[IID.MAGIC_RING].price = 5000
    item_man[IID.WALL_RING].price = 10000
    item_man[IID.SILVERERNG].price = 20000
    item_man[IID.GOLD_ERNG].price = 50000
    item_man[IID.SILVERSTUD].price = 30000
    item_man[IID.GOLD_STUD].price = 65000
    item_man[IID.SIGHTSCOPE].price = 1000
    item_man[IID.CHARM_TOP].price = 10000
    item_man[IID.RAGE_BAND].price = 5000
    item_man[IID.FRENZYBAND].price = 10000
    item_man[IID.THIRD_EYE].price = 5000
    item_man[IID.WALLET].price = 5000
    item_man[IID.GREENDREAM].price = 65000
    item_man[IID.BERSERKER].price = 10000
    item_man[IID.POWERSCARF].price = 5000
    item_man[IID.SPEED_BELT].price = 30000
    item_man[IID.BLACK_ROCK].price = 65000
    item_man[IID.BLUE_ROCK].price = 65000
    item_man[IID.SILVERROCK].price = 65000
    item_man[IID.WHITE_ROCK].price = 65000
    item_man[IID.GOLD_ROCK].price = 65000
    item_man[IID.MUSCLERING].price = 10000
    item_man[IID.FLEA_VEST].price = 30000
    item_man[IID.MAGIC_SEAL].price = 25000
    item_man[IID.POWER_SEAL].price = 25000
    item_man[IID.SUN_SHADES].price = 40000
    item_man[IID.PRISMSPECS].price = 65000
    item_man[IID.PETAL].price = 1000
    item_man[IID.HORN].price = 1000
    item_man[IID.FANG].price = 1000
    item_man[IID.FEATHER].price = 1000
    item_man[IID.POWER_TAB].price = 20000
    item_man[IID.MAGIC_TAB].price = 20000
    item_man[IID.SPEED_TAB].price = 65000
    item_man[IID.CRISIS_ARM].price = 65000
    item_man[IID.DOOMSICKLE].price = 65000


def randomize_item_prices(
        item_man: itemdata.ItemDB,
        shop_options: shopoptions.ShopOptions,
        rng: RNGType
):
    if shop_options.item_price_randomization == shopoptions.ItemSalePrice.VANILLA:
        return

    for item_id, item in item_man.item_dict.items():
        if item_id in shop_options.item_price_randomization_exclusions:
            continue

        match shop_options.item_price_randomization:
            case shopoptions.ItemSalePrice.RANDOM:
                new_price = rng.randrange(2, 65000, 2)
            case shopoptions.ItemSalePrice.RANDOM_MULTIPLIER:
                # Temp values
                new_price = item.price * get_random_multiplier(shop_options.item_price_min_multiplier,
                                                               shop_options.item_price_max_multiplier,
                                                               rng.random)
            case _:
                new_price = item.price

        if new_price % 2 == 1:
            new_price += 1
        new_price = sorted([0, round(new_price), 65000])[1]
        item.price = new_price


def get_random_multiplier(
        min_multiplier: float,
        max_multiplier: float,
        rand_fn: typing.Callable[[], float]
) -> float:
    #  Get a random multiplier that balances above and below 1
    rand_val = rand_fn()

    log_val = math.log(min_multiplier) + math.log(max_multiplier/min_multiplier)*rand_val
    return math.exp(log_val)


def update_unsellable(
        item_man: itemdata.ItemDB,
        shop_options: shopoptions.ShopOptions
):
    forced_unsellable = (
        shopoptions.ShopOptions.unused_items +
        [
            ctenums.ItemID.MASAMUNE_1, ctenums.ItemID.MASAMUNE_2,
            ctenums.ItemID.BENT_HILT, ctenums.ItemID.BENT_SWORD,
            ctenums.ItemID.TOOLS, ctenums.ItemID.JERKY, ctenums.ItemID.RACE_LOG,
            ctenums.ItemID.MOON_STONE, ctenums.ItemID.SUN_STONE,
            ctenums.ItemID.SEED, ctenums.ItemID.BIKE_KEY, ctenums.ItemID.PENDANT,
            ctenums.ItemID.GATE_KEY, ctenums.ItemID.PRISMSHARD, ctenums.ItemID.C_TRIGGER,
            ctenums.ItemID.RUBY_KNIFE, ctenums.ItemID.YAKRA_KEY, ctenums.ItemID.CLONE,
            ctenums.ItemID.TOMAS_POP, ctenums.ItemID.PENDANT_CHARGE, ctenums.ItemID.RAINBOW_SHELL,
            ctenums.ItemID.SCALING_LEVEL, ctenums.ItemID.JETSOFTIME, ctenums.ItemID.DREAMSTONE
        ]
    )

    for item_id, item in item_man.item_dict.items():
        if item_id in forced_unsellable or item_id in shop_options.not_sellable_items:
            item.secondary_stats.is_unsellable = True
        else:
            item.secondary_stats.is_unsellable = False


def apply_shop_settings(
        item_man: itemdata.ItemDB,
        shop_man: shoptypes.ShopManager,
        shop_options: shopoptions.ShopOptions,
        ds_item_pool: list[gearrandooptions.DSItem],
        rng: RNGType
):
    update_unsellable_prices(item_man)
    if shop_options.item_base_prices == shopoptions.ItemBasePrice.BALANCED:
        set_balanced_prices(item_man)
    elif shop_options.item_base_prices == shopoptions.ItemBasePrice.MAX:
        set_max_prices(item_man)

    update_unsellable(item_man, shop_options)
    randomize_item_prices(item_man, shop_options, rng)
    randomize_shop_inventory(shop_man, shop_options, ds_item_pool, rng)

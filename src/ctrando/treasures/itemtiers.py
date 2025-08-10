from enum import Enum, auto
from ctrando.common.ctenums import ItemID as IID


class ItemTier(Enum):
    """Tier of an ItemID"""
    LOW_CONS = auto()
    MID_CONS = auto()
    HIGH_CONS = auto()
    TOP_CONS = auto()
    KEY = auto()


_tier_itemid_dict: dict[ItemTier, list[IID]] = {
    ItemTier.LOW_CONS: [
        IID.TONIC, IID.POWER_MEAL,
    ],
    ItemTier.MID_CONS: [
        IID.MID_TONIC
    ],
    ItemTier.HIGH_CONS: [

    ],
    ItemTier.TOP_CONS: [

    ]
}

_cons_tier_0 = [IID.TONIC, IID.POWER_MEAL]
_cons_tier_1 = [IID.MID_TONIC, IID.HEAL]
_cons_tier_2 = [IID.ETHER, IID.REVIVE, IID.SHELTER]
_cons_tier_3 = [IID.POWER_TAB, IID.MAGIC_TAB, IID.BARRIER, IID.SHIELD, IID.MID_ETHER, IID.FULL_TONIC]
_cons_tier_4 = [IID.FULL_TONIC, IID.FULL_ETHER, IID.LAPIS]
_cons_tier_top = [IID.HYPERETHER, IID.ELIXIR, IID.MEGAELIXIR, IID.SPEED_TAB]

_top_tier_cons_weights: dict[IID, float] = {
    IID.HYPERETHER: 10,
    IID.ELIXIR: 5,
    IID.MEGAELIXIR: 2.5,
    IID.SPEED_TAB: 1
}

_gear_tier_0 = [
    # Crono Gear
    IID.WOOD_SWORD, IID.IRON_BLADE, IID.STEELSABER, IID.LODE_SWORD,
    # Marle Gear
    IID.BRONZE_BOW, IID.IRON_BOW, IID.LODE_BOW,
    # Lucca Gear
    IID.AIR_GUN, IID.AUTO_GUN,
    # Robo Gear
    IID.TIN_ARM, IID.HAMMER_ARM,
    # Frog Gear
    IID.BRONZEEDGE, IID.IRON_SWORD,
    # Magus Gear
    # Helms
    IID.HIDE_CAP, IID.BRONZEHELM, IID.IRON_HELM, IID.BERET,
    # Armor
    IID.HIDE_TUNIC, IID.KARATE_GI, IID.BRONZEMAIL, IID.MAIDENSUIT, IID.IRON_SUIT,
    IID.TITAN_VEST,
    # Accessories
    IID.RIBBON, IID.POWERGLOVE, IID.DEFENDER, IID.MAGICSCARF, IID.SIGHTSCOPE,
]
_gear_tier_1 = [
    # Crono Gear
    IID.RED_KATANA, IID.FLINT_EDGE, IID.DARK_SABER, IID.AEON_BLADE,
    IID.SLASHER,
    # Marle Gear
    IID.ROBIN_BOW, IID.SAGE_BOW,
    # Lucca Gear
    IID.PICOMAGNUM, IID.PLASMA_GUN,
    # Robo Gear
    IID.MIRAGEHAND, IID.DOOMFINGER, IID.MAGMA_HAND,
    # Frog Gear
    # Magus Gear
    # Helms
    IID.GOLD_HELM, IID.ROCK_HELM, IID.CERATOPPER,
    # Armor
    IID.GOLD_SUIT, IID.RUBY_VEST, IID.DARK_MAIL, IID.MESO_MAIL, IID.MIST_ROBE,
    # Accessories
    IID.BERSERKER, IID.RAGE_BAND, IID.MAGICSCARF, IID.POWERSCARF, IID.THIRD_EYE
]
_gear_tier_2 = [
    # Crono Gear
    IID.DEMON_EDGE, IID.ALLOYBLADE, IID.STAR_SWORD,
    # Marle Gear
    IID.DREAM_BOW, IID.COMETARROW,
    # Lucca Gear
    IID.RUBY_GUN, IID.DREAM_GUN, IID.GRAEDUS, IID.TABAN_HELM, IID.TABAN_VEST,
    # Robo Gear
    IID.MEGATONARM, IID.BIG_HAND,
    # Frog Gear
    IID.FLASHBLADE,
    # Magus Gear
    IID.DARKSCYTHE,
    # Helms
    IID.GLOW_HELM, IID.LODE_HELM,
    # Armor
    IID.LUMIN_ROBE, IID.FLASH_MAIL, IID,
    # Accessories
    IID.HIT_RING, IID.POWER_RING, IID.MAGIC_RING
]
_gear_tier_3 = [
    # Crono Gear
    IID.VEDICBLADE, IID.KALI_BLADE, IID.SLASHER_2,
    # Marle Gear
    IID.SIREN,
    # Lucca Gear
    IID.MEGABLAST,
    # Robo Gear
    IID.KAISER_ARM, IID.GIGA_ARM,
    # Frog Gear
    IID.RUNE_BLADE, IID.DEMON_HIT,
    # Magus Gear
    IID.HURRICANE,
    # Helms
    IID.SIGHT_CAP, IID.MEMORY_CAP, IID.TIME_HAT, IID.AEON_HELM,
    # Armor
    IID.RED_VEST, IID.BLUE_VEST, IID.WHITE_VEST, IID.BLACK_VEST,
    # Accessories
    IID.POWER_SEAL, IID.MAGIC_SEAL, IID.WALL_RING, IID.SILVERERNG,
    IID.FRENZYBAND,
]
_gear_tier_4 = [
    # Crono Gear
    IID.SHIVA_EDGE, IID.SWALLOW,
    # Marle Gear
    IID.SIREN,
    # Lucca Gear
    IID.SHOCK_WAVE,
    # Robo Gear
    IID.TERRA_ARM,
    # Frog Gear
    IID.BRAVESWORD,
    # Magus Gear
    IID.STARSCYTHE,
    # Helms
    IID.RBOW_HELM, IID.MERMAIDCAP, IID.VIGIL_HAT, IID.DARK_HELM, IID.SAFE_HELM,
    IID.OZZIEPANTS,  # Where?
    # Armor
    IID.RED_MAIL, IID.BLUE_MAIL, IID.WHITE_MAIL, IID.BLACK_MAIL,
    IID.ZODIACCAPE, IID.MOON_ARMOR, IID.GLOOM_CAPE, IID.RUBY_ARMOR,
    # Accessories
    IID.SILVERSTUD, IID.GOLD_ERNG, IID.SUN_SHADES, IID.DASH_RING, IID.FLEA_VEST,
]
_gear_tier_top = [
    # Crono Gear
    IID.RAINBOW,
    # Marle Gear
    IID.VALKERYE,
    # Lucca Gear
    IID.WONDERSHOT, IID.TABAN_SUIT,
    # Robo Gear
    IID.CRISIS_ARM,
    # Frog Gear
    IID.MASAMUNE_1, IID.MASAMUNE_2,  # But also KIs so irrelevant
    # Magus Gear
    IID.DOOMSICKLE,
    # Helms
    IID.HASTE_HELM, IID.PRISM_HELM, IID.GLOOM_HELM,
    # Armor
    IID.NOVA_ARMOR, IID.PRISMDRESS,
    # Accessories
    IID.PRISMSPECS, IID.GOLD_STUD, IID.GREENDREAM, IID.AMULET,
]

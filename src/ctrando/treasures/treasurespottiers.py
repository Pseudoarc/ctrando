"""Define the tier of each TreasureID"""
from enum import Enum, auto

from ctrando.common.ctenums import TreasureID as TID

class TreasureIDTier(Enum):
    FREE = auto()
    LOW = auto()
    LOW_PLUS = auto()
    MID = auto()
    HIGH = auto()
    TOP = auto()
    SEALED = auto()


_tier_tid_dict: dict[TreasureIDTier, list[TID]] = {
    TreasureIDTier.FREE: [
        # Truce/Porre 1000
        TID.TRUCE_MAYOR_1F, TID.TRUCE_MAYOR_2F, TID.QUEENS_TOWER_1000,
        TID.QUEENS_ROOM_1000, TID.KINGS_TOWER_1000, TID.KINGS_ROOM_1000,
        TID.GUARDIA_COURT_TOWER, TID.PORRE_MAYOR_2F, TID.SNAIL_STOP_KEY,
        TID.FAIR_PENDANT,
        TID.GUARDIA_FOREST_POWER_TAB_1000,
        # Truce 600
        TID.TRUCE_CANYON_1, TID.TRUCE_CANYON_2, TID.ROYAL_KITCHEN,
        TID.ZENAN_BRIDGE_CHEF, TID.QUEENS_TOWER_600, TID.QUEENS_ROOM_600,
        TID.KINGS_TOWER_600, TID.KINGS_ROOM_600,
        TID.ZENAN_BRIDGE_CHEF_TAB,
        TID.GUARDIA_FOREST_POWER_TAB_600,
        # Dorino/Porre 600 Region
        TID.FIONAS_HOUSE_1, TID.FIONAS_HOUSE_2, TID.CURSED_WOODS_1,
        TID.CURSED_WOODS_2, TID.FROGS_BURROW_RIGHT,
        TID.PORRE_MARKET_600_POWER_TAB,
        TID.DORINO_BROMIDE_MAGIC_TAB,
        # Prehistory Open -- Partial
        TID.MYSTIC_MT_STREAM,
        TID.LARUBA_ROCK,
    ],
    TreasureIDTier.LOW: [
        # Crono's Trial
        TID.GUARDIA_JAIL_CELL,
        TID.GUARDIA_JAIL_OMNICRONE_1,
        TID.GUARDIA_JAIL_OMNICRONE_2,
        TID.GUARDIA_JAIL_OMNICRONE_3,
        TID.GUARDIA_JAIL_OMNICRONE_4,
        TID.GUARDIA_JAIL_HOLE_1,
        TID.GUARDIA_JAIL_HOLE_2,
        TID.GUARDIA_JAIL_FRITZ,
        TID.GUARDIA_JAIL_FRITZ_STORAGE,
        TID.GUARDIA_JAIL_OUTER_WALL,
        TID.PRISON_TOWER_1000,
        # Manoria Cathedral
        TID.MANORIA_CATHEDRAL_1,
        TID.MANORIA_CATHEDRAL_2,
        TID.MANORIA_CATHEDRAL_3,
        TID.MANORIA_BROMIDE_1,
        TID.MANORIA_BROMIDE_2,
        TID.MANORIA_BROMIDE_3,
        TID.MANORIA_INTERIOR_1,
        TID.MANORIA_INTERIOR_2,
        TID.MANORIA_INTERIOR_3,
        TID.MANORIA_INTERIOR_4,
        TID.MANORIA_SHRINE_MAGUS_1,
        TID.MANORIA_SHRINE_MAGUS_2,
        TID.MANORIA_INTERIOR_1,
        TID.MANORIA_INTERIOR_2,
        TID.MANORIA_INTERIOR_3,
        TID.MANORIA_INTERIOR_4,
        TID.MANORIA_SHRINE_SIDEROOM_1,
        TID.MANORIA_SHRINE_SIDEROOM_2,
        TID.YAKRAS_ROOM,
        TID.MANORIA_CONFINEMENT_POWER_TAB,
        TID.DORINO_BROMIDE_MAGIC_TAB,
        # Future Labs Open
        TID.LAB_16_1,
        TID.LAB_16_2,
        TID.LAB_16_3,
        TID.LAB_16_4,
        TID.LAB_32_1,
        # Future Sewers
        TID.SEWERS_1,
        TID.SEWERS_2,
        TID.SEWERS_3,
        TID.DEATH_PEAK_POWER_TAB,
        # Arris Dome
        TID.ARRIS_DOME_FOOD_STORE,
        TID.ARRIS_DOME_RATS,
        TID.ARRIS_DOME_FOOD_LOCKER_KEY,
    ],
    TreasureIDTier.LOW_PLUS: [
        # Future sort of locked
        TID.FACTORY_LEFT_AUX_CONSOLE, TID.FACTORY_LEFT_SECURITY_LEFT,
        TID.FACTORY_LEFT_SECURITY_RIGHT, TID.FACTORY_RIGHT_FLOOR_TOP,
        TID.FACTORY_RIGHT_FLOOR_LEFT, TID.FACTORY_RIGHT_FLOOR_BOTTOM,
        TID.FACTORY_RIGHT_FLOOR_SECRET, TID.FACTORY_RIGHT_CRANE_UPPER,
        TID.FACTORY_RIGHT_CRANE_LOWER, TID.FACTORY_RIGHT_INFO_ARCHIVE,
        TID.FACTORY_RIGHT_DATA_CORE_1, TID.FACTORY_RIGHT_DATA_CORE_2,
        TID.FACTORY_RUINS_GENERATOR,
        TID.LAB_32_RACE_LOG, TID.ARRIS_DOME_DOAN_KEY,
        # Heckran Cave
        TID.HECKRAN_CAVE_1, TID.HECKRAN_CAVE_2, TID.HECKRAN_CAVE_ENTRANCE,
        TID.HECKRAN_CAVE_SIDETRACK, TID.FOREST_RUINS, TID.TABAN_GIFT_VEST,
        TID.MEDINA_ELDER_SPEED_TAB,
        TID.MEDINA_ELDER_MAGIC_TAB,
        # Denadoro Mountains
        TID.DENADORO_MTS_SCREEN2_1,
        TID.DENADORO_MTS_SCREEN2_2,
        TID.DENADORO_MTS_SCREEN2_3,
        TID.DENADORO_MTS_FINAL_1,
        TID.DENADORO_MTS_FINAL_2,
        TID.DENADORO_MTS_FINAL_3,
        TID.DENADORO_MTS_WATERFALL_TOP_1,
        TID.DENADORO_MTS_WATERFALL_TOP_2,
        TID.DENADORO_MTS_WATERFALL_TOP_3,
        TID.DENADORO_MTS_WATERFALL_TOP_4,
        TID.DENADORO_MTS_WATERFALL_TOP_5,
        TID.DENADORO_MTS_ENTRANCE_1,
        TID.DENADORO_MTS_ENTRANCE_2,
        TID.DENADORO_MTS_SCREEN3_1,
        TID.DENADORO_MTS_SCREEN3_2,
        TID.DENADORO_MTS_SCREEN3_3,
        TID.DENADORO_MTS_SCREEN3_4,
        TID.DENADORO_MTS_AMBUSH,
        TID.DENADORO_MTS_SAVE_PT,
        TID.DENADORO_MTS_KEY,
        TID.DENADORO_MTS_SPEED_TAB,
    ],
    TreasureIDTier.MID: [
        # Hunting Range Nu
        TID.HUNTING_RANGE_NU_REWARD,
        # Reptite Lair and Forest Maze
        TID.REPTITE_LAIR_REPTITES_1, TID.REPTITE_LAIR_REPTITES_2,
        TID.REPTITE_LAIR_SECRET_B1_NE, TID.REPTITE_LAIR_SECRET_B1_SE,
        TID.REPTITE_LAIR_SECRET_B1_SW, TID.REPTITE_LAIR_SECRET_B2_NE_OR_SE_LEFT,
        TID.REPTITE_LAIR_SECRET_B2_SW, TID.REPTITE_LAIR_SECRET_B2_NE_RIGHT,
        TID.REPTITE_LAIR_SECRET_B2_SE_RIGHT, TID.REPTITE_LAIR_KEY,
        TID.FOREST_MAZE_1, TID.FOREST_MAZE_2, TID.FOREST_MAZE_3,
        TID.FOREST_MAZE_4, TID.FOREST_MAZE_5, TID.FOREST_MAZE_6,
        TID.FOREST_MAZE_7, TID.FOREST_MAZE_8, TID.FOREST_MAZE_9,
        # Dactyl Nest
        TID.DACTYL_NEST_1, TID.DACTYL_NEST_2, TID.DACTYL_NEST_3,
        # Taban Reward for Masa
        TID.TABAN_GIFT_HELM,
        # Zenan Bridge Captain  (Jerky lock)
        TID.ZENAN_BRIDGE_CAPTAIN,
        # Shared Claw/Tyrano
        TID.TYRANO_LAIR_KINO_CELL, TID.TYRANO_LAIR_TRAPDOOR,
        TID.TYRANO_LAIR_THRONE_1, TID.TYRANO_LAIR_THRONE_2,
        # Tyrano not Claw
        TID.TYRANO_LAIR_MAZE_1, TID.TYRANO_LAIR_MAZE_2,
        TID.TYRANO_LAIR_MAZE_3, TID.TYRANO_LAIR_MAZE_4,
        # Magus's Castle
        TID.MAGUS_CASTLE_RIGHT_HALL, TID.MAGUS_CASTLE_GUILLOTINE_1,
        TID.MAGUS_CASTLE_GUILLOTINE_2, TID.MAGUS_CASTLE_SLASH_ROOM_1,
        TID.MAGUS_CASTLE_SLASH_ROOM_2, TID.MAGUS_CASTLE_STATUE_HALL,
        TID.MAGUS_CASTLE_FOUR_KIDS, TID.MAGUS_CASTLE_OZZIE_1,
        TID.MAGUS_CASTLE_OZZIE_2, TID.MAGUS_CASTLE_ENEMY_ELEVATOR,
        TID.MAGUS_CASTLE_LEFT_HALL, TID.MAGUS_CASTLE_UNSKIPPABLES,
        TID.MAGUS_CASTLE_PIT_E, TID.MAGUS_CASTLE_PIT_NE, TID.MAGUS_CASTLE_PIT_NW,
        TID.MAGUS_CASTLE_PIT_W,
        TID.MAGUS_CASTLE_FLEA_MAGIC_TAB, TID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB,
        # Mt. Woe
        TID.MT_WOE_2ND_SCREEN_1, TID.MT_WOE_2ND_SCREEN_2,
        TID.MT_WOE_2ND_SCREEN_3, TID.MT_WOE_2ND_SCREEN_4,
        TID.MT_WOE_2ND_SCREEN_5, TID.MT_WOE_3RD_SCREEN_1,
        TID.MT_WOE_3RD_SCREEN_2, TID.MT_WOE_3RD_SCREEN_3,
        TID.MT_WOE_3RD_SCREEN_4, TID.MT_WOE_3RD_SCREEN_5,
        TID.MT_WOE_1ST_SCREEN, TID.MT_WOE_FINAL_1,
        TID.MT_WOE_FINAL_2, TID.MT_WOE_KEY,
        # Zeal
        TID.ENHASA_NU_BATTLE_MAGIC_TAB, TID.ENHASA_NU_BATTLE_SPEED_TAB,
        TID.KAJAR_ROCK, TID.KAJAR_SPEED_TAB, TID.KAJAR_NU_SCRATCH_MAGIC_TAB,
        # Ocean Palace
        TID.OCEAN_PALACE_MAIN_S, TID.OCEAN_PALACE_MAIN_N,
        TID.OCEAN_PALACE_E_ROOM, TID.OCEAN_PALACE_W_ROOM,
        TID.OCEAN_PALACE_SWITCH_NW, TID.OCEAN_PALACE_SWITCH_SW,
        TID.OCEAN_PALACE_SWITCH_NE, TID.OCEAN_PALACE_SWITCH_SECRET,
        TID.OCEAN_PALACE_FINAL,

    ],
    TreasureIDTier.HIGH: [
        # Northern Ruins
        TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000,
        TID.NORTHERN_RUINS_BASEMENT_600,
        TID.NORTHERN_RUINS_BASEMENT_1000,  # Froglocked
        # Rainbow Shell Quest
        TID.GUARDIA_TREASURY_1, TID.GUARDIA_TREASURY_2, TID.GUARDIA_TREASURY_3,
        TID.GUARDIA_BASEMENT_1, TID.GUARDIA_BASEMENT_2, TID.GUARDIA_BASEMENT_3,
        TID.KINGS_TRIAL_KEY,
        # Part of Moonstone Quest
        TID.JERKY_GIFT, TID.SUN_KEEP_2300, TID.TABAN_SUNSHADES, TID.SUN_PALACE_KEY,
        # Tabs in Future Sealed
        TID.TRANN_DOME_SEALED_MAGIC_TAB, TID.ARRIS_DOME_SEALED_POWER_TAB,
        TID.KEEPERS_DOME_MAGIC_TAB,
        TID.FROGS_BURROW_LEFT,  # Vanilla Bent Hilt. Maybe Mid?
        TID.TATA_REWARD,  # Vanilla Medal.
        TID.DENADORO_ROCK,
        TID.TOMA_REWARD, TID.SUN_KEEP_600_POWER_TAB,
        # Giant's Claw
        TID.GIANTS_CLAW_TRAPS, TID.GIANTS_CLAW_CAVES_1, TID.GIANTS_CLAW_CAVES_2,
        TID.GIANTS_CLAW_CAVES_3, TID.GIANTS_CLAW_CAVES_4, TID.GIANTS_CLAW_CAVES_5,
        TID.GIANTS_CLAW_ROCK, TID.GIANTS_CLAW_KEY,
        TID.GIANTS_CLAW_TRAPS_POWER_TAB, TID.GIANTS_CLAW_ENTRANCE_POWER_TAB,
        TID.GIANTS_CLAW_CAVERNS_POWER_TAB,
        # Ozzie's Fort
        TID.OZZIES_FORT_GUILLOTINES_1, TID.OZZIES_FORT_GUILLOTINES_2,
        TID.OZZIES_FORT_GUILLOTINES_3, TID.OZZIES_FORT_GUILLOTINES_4,
        TID.OZZIES_FORT_FINAL_1, TID.OZZIES_FORT_FINAL_2,
        # Sunken Desert
        TID.SUNKEN_DESERT_B1_NE, TID.SUNKEN_DESERT_B1_SE,
        TID.SUNKEN_DESERT_B1_NW, TID.SUNKEN_DESERT_B1_SW,
        TID.SUNKEN_DESERT_B2_N, TID.SUNKEN_DESERT_B2_NW,
        TID.SUNKEN_DESERT_B2_W, TID.SUNKEN_DESERT_B2_SW,
        TID.SUNKEN_DESERT_B2_SE, TID.SUNKEN_DESERT_B2_E,
        TID.SUNKEN_DESERT_B2_CENTER,
        TID.SUNKEN_DESERT_POWER_TAB,
        TID.FIONA_KEY,
        # Death Peak
        TID.DEATH_PEAK_SOUTH_FACE_KRAKKER, TID.DEATH_PEAK_SOUTH_FACE_SPAWN_SAVE,
        TID.DEATH_PEAK_SOUTH_FACE_SUMMIT, TID.DEATH_PEAK_FIELD,
        TID.DEATH_PEAK_KRAKKER_PARADE, TID.DEATH_PEAK_CAVES_LEFT,
        TID.DEATH_PEAK_CAVES_CENTER, TID.DEATH_PEAK_CAVES_RIGHT,
        TID.EOT_GASPAR_REWARD, TID.BEKKLER_KEY,
        # Geno Dome
        TID.GENO_DOME_1F_1, TID.GENO_DOME_1F_2, TID.GENO_DOME_1F_3,
        TID.GENO_DOME_1F_4, TID.GENO_DOME_ROOM_1, TID.GENO_DOME_ROOM_2,
        TID.GENO_DOME_PROTO4_1, TID.GENO_DOME_PROTO4_2,
        TID.GENO_DOME_2F_1, TID.GENO_DOME_2F_2, TID.GENO_DOME_2F_3,
        TID.GENO_DOME_2F_4,
        TID.GENO_DOME_BOSS_1, TID.GENO_DOME_BOSS_2,
        TID.GENO_DOME_LABS_MAGIC_TAB, TID.GENO_DOME_LABS_SPEED_TAB,
        TID.GENO_DOME_CORRIDOR_POWER_TAB, TID.GENO_DOME_ATROPOS_MAGIC_TAB,
        # Last Village
        TID.LAST_VILLAGE_NU_SHOP_MAGIC_TAB, TID.BLACKBIRD_DUCTS_MAGIC_TAB

    ],
    TreasureIDTier.TOP: [
        TID.MELCHIOR_RAINBOW_SHELL,  # Vanilla Prism Armors
        TID.MELCHIOR_SUNSTONE_RAINBOW,  # Vanilla Rainbow + PrismSpecs
        TID.MELCHIOR_SUNSTONE_SPECS,
        TID.TABAN_GIFT_SUIT,  # Vanilla Taban Suit
        TID.CYRUS_GRAVE_KEY,  # Vanilla Masa2
        TID.LUCCA_WONDERSHOT,  # Vanilla Wondershot
        # Black Omen
        TID.BLACK_OMEN_AUX_COMMAND_MID, TID.BLACK_OMEN_AUX_COMMAND_NE,
        TID.BLACK_OMEN_GRAND_HALL, TID.BLACK_OMEN_NU_HALL_NW,
        TID.BLACK_OMEN_NU_HALL_W, TID.BLACK_OMEN_NU_HALL_SW,
        TID.BLACK_OMEN_NU_HALL_NE, TID.BLACK_OMEN_NU_HALL_E,
        TID.BLACK_OMEN_NU_HALL_SE, TID.BLACK_OMEN_ROYAL_PATH,
        TID.BLACK_OMEN_RUMINATOR_PARADE, TID.BLACK_OMEN_EYEBALL_HALL,
        TID.BLACK_OMEN_TUBSTER_FLY, TID.BLACK_OMEN_MARTELLO,
        TID.BLACK_OMEN_ALIEN_SW, TID.BLACK_OMEN_ALIEN_NE,
        TID.BLACK_OMEN_ALIEN_NW, TID.BLACK_OMEN_TERRA_W,
        TID.BLACK_OMEN_TERRA_ROCK, TID.BLACK_OMEN_TERRA_NE,

    ],
    TreasureIDTier.SEALED: [
        # Northern Ruins
        TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000, TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000,
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000,TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600,
        TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600, TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600,
        TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600,
        TID.MELCHIOR_FORGE_MASA,  # Vanilla MasaMune
        # 1000
        TID.TRUCE_INN_SEALED_1000, TID.GUARDIA_CASTLE_SEALED_1000,
        TID.PORRE_MAYOR_SEALED_1, TID.PORRE_MAYOR_SEALED_2,
        TID.HECKRAN_SEALED_1, TID.HECKRAN_SEALED_2,
        TID.GUARDIA_FOREST_SEALED_1000,
        TID.PYRAMID_LEFT, TID.PYRAMID_RIGHT,
        # 600 noflight
        TID.TRUCE_INN_SEALED_600, TID.GUARDIA_CASTLE_SEALED_600,
        TID.PORRE_ELDER_SEALED_1, TID.PORRE_ELDER_SEALED_2,
        TID.GUARDIA_FOREST_SEALED_600,
        TID.MAGIC_CAVE_SEALED,
        # 2300
        TID.TRANN_DOME_SEAL_1, TID.TRANN_DOME_SEAL_2,
        TID.BANGOR_DOME_SEAL_1, TID.BANGOR_DOME_SEAL_2, TID.BANGOR_DOME_SEAL_3,
        TID.ARRIS_DOME_SEAL_1, TID.ARRIS_DOME_SEAL_2, TID.ARRIS_DOME_SEAL_3,
        TID.ARRIS_DOME_SEAL_4,

    ]
}

_tab_spots = [
    TID.GUARDIA_FOREST_POWER_TAB_600,
    TID.GUARDIA_FOREST_POWER_TAB_1000,
    TID.MANORIA_CONFINEMENT_POWER_TAB,
    TID.DORINO_BROMIDE_MAGIC_TAB,
    TID.PORRE_MARKET_600_POWER_TAB,
    TID.DENADORO_MTS_SPEED_TAB,
    TID.TOMAS_GRAVE_SPEED_TAB,
    TID.GIANTS_CLAW_CAVERNS_POWER_TAB,
    TID.GIANTS_CLAW_ENTRANCE_POWER_TAB,
    TID.GIANTS_CLAW_TRAPS_POWER_TAB,
    TID.SUN_KEEP_600_POWER_TAB,
    TID.MEDINA_ELDER_SPEED_TAB,
    TID.MEDINA_ELDER_MAGIC_TAB,
    TID.MAGUS_CASTLE_FLEA_MAGIC_TAB,
    TID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB,
    TID.TRANN_DOME_SEALED_MAGIC_TAB,
    TID.ARRIS_DOME_SEALED_POWER_TAB,
    TID.KEEPERS_DOME_MAGIC_TAB,
    TID.DEATH_PEAK_POWER_TAB,
    TID.BLACKBIRD_DUCTS_MAGIC_TAB,
    TID.GENO_DOME_ATROPOS_MAGIC_TAB,
    TID.GENO_DOME_CORRIDOR_POWER_TAB,
    TID.GENO_DOME_LABS_MAGIC_TAB,
    TID.GENO_DOME_LABS_SPEED_TAB,
    TID.ENHASA_NU_BATTLE_MAGIC_TAB,
    TID.ENHASA_NU_BATTLE_SPEED_TAB,
    TID.KAJAR_SPEED_TAB,
    TID.KAJAR_NU_SCRATCH_MAGIC_TAB,
    TID.LAST_VILLAGE_NU_SHOP_MAGIC_TAB,
    TID.SUNKEN_DESERT_POWER_TAB,
]

def get_tid_tier(treasure_id: TID) -> TreasureIDTier:
    """Get the tier of a TreasureID"""
    for tier in TreasureIDTier:
        if treasure_id in _tier_tid_dict[tier]:
            return tier

    raise ValueError
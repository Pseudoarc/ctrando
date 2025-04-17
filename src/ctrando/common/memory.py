from dataclasses import dataclass
import enum


class Memory(enum.IntEnum):
    """Enum for useful memory addresses."""
    DISABLE_MENU_00 = 0x000110
    DISABLE_MENU = 0x7E0110
    PREVIOUS_LOCATION_LO = 0x7E0105
    PREVIOUS_LOCATION_HI = 0x7E0106
    LOCEVENT_VALUE_STR_0 = 0x7E0200
    LOCEVENT_VALUE_STR_1 = 0x7E0201
    LOCEVENT_VALUE_STR_2 = 0x7E0202
    LOCEVENT_VALUE_STR_4 = 0x7E0203
    OW_MOVE_STATUS = 0x7E027E
    # Usually a copy of OW_MOVE_STATUS, but not always
    OW_MOVE_STATUS_EXTRA = 0x7E028F  # Unsure
    EPOCH_X_COORD_LO = 0x7E0290
    EPOCH_X_COORD_HI = 0x7E0291
    EPOCH_Y_COORD_LO = 0x7E0292
    EPOCH_Y_COORD_HI = 0x7E0293
    EPOCH_STATUS = 0x7E0294
    DACTYL_X_COORD_LO = 0x7E029A
    DACTYL_X_COORD_HI = 0x7E029B
    DACTYL_Y_COORD_LO = 0x7E029C
    DACTYL_Y_COORD_HI = 0x7E029D
    DACTYL_STATUS = 0x7E029E
    EPOCH_MAP_LO = 0x7E029F
    EPOCH_MAP_HI = 0x7E02A0
    OW_STORYLINE_COUNTER = 0x7E1BA6
    # Free Memory from Jets Time Gauge: [0x7E2881, 0x7E2980)
    SCALING_LEVEL = 0x7E2881
    ORIGINAL_LEVEL_TEMP = 0x7E2882
    FROM_SCALE_TEMP = 0x7E2883  # Used by scaling routines.
    TO_SCALE_TEMP = 0x7E2884
    TEMP_SCALED_XP_LO = 0x7E2885
    TEMP_SCALED_XP_HI = 0x7E2886
    # End old time gauge memory
    ACTIVE_PC1 = 0x7E2980
    ACTIVE_PC2 = 0x7E2981
    ACTIVE_PC3 = 0x7E2982
    RESERVE_PC1 = 0x7E2983
    RESERVE_PC2 = 0x7E2984
    RESERVE_PC3 = 0x7E2985
    RESERVE_PC4 = 0x7E2986
    RESERVE_PC5 = 0x7E2987
    RESERVE_PC6 = 0x7E2988
    RECRUITED_CHARACTERS = 0x7E29AF
    GOLD_LO = 0x7E2C53
    GOLD_MID = 0x7E2C54
    GOLD_HI = 0x7E2C55
    STORYLINE_COUNTER = 0x7F0000
    # Bytes 0x7F0001 through 0x7F004F are reserved for treasure chests.
    # There are only 0xF6 chests which use 0x1F bytes.  So we're free from
    # [0x7F0021, 0x7F0050)
    OBJECTIVES_COMPLETED = 0x7F0045
    KEY_ITEMS_OBTAINED = 0x7F0046
    RECRUITS_OBTAINED = 0x7F0047
    QUESTS_COMPLETED = 0x7F0048
    BOSSES_DEFEATED = 0x7F0049
    COURTFLAGS = 0x7F0050
    CRONO_TRIAL_PC1 = 0x7F0051  # Orig. Trial Innocent Votes
    FAIRFLAGS = 0x7F0054
    MARLEFLAGS = 0x7F0055  # MarleFlags
    CRONO_TRIAL_PC2 = 0x7F0056  # TELEPODFLAGS = 0x7F0056  # TelepodFlags
    CRONO_TRIAL_PC3 = 0x7F0059  # CRONO_TRIAL_COUNTER = 0x7F0059
    LUCCAFLAGS = 0x7F005A
    PORTAL_STATUS = 0x7F005B  # 1 when in use, other bits unused
    LOAD_SCREEN_STATUS = 0x7F0060
    ATTRACT_MODE_COUNTER = 0x7F0062
    KINGS_TRIAL_PROGRESS_COUNTER = 0x7F0069
    ENDING_COUNTER = 0x7F006E  # used for some special endings
    FOREST_PC1 = 0x7F00B4
    FOREST_PC2 = 0x7F00B5
    FOREST_PC3 = 0x7F00B6
    BLACKBIRD_CRONO_GEAR_MISSING_OLD = 0x7F00B4
    BLACKBIRD_MARLE_GEAR_MISSING_OLD = 0x7F00B5
    BLACKBIRD_LUCCA_GEAR_MISSING_OLD = 0x7F00B6
    BLACKBIRD_ROBO_GEAR_MISSING_OLD = 0x7F00B7
    BLACKBIRD_FROG_GEAR_MISSING_OLD = 0x7F00B8
    BLACKBIRD_AYLA_GEAR_MISSING_OLD = 0x7F00B9
    BLACKBIRD_GEAR_STATUS = 0x7F00B9
    BLACKBIRD_PC1_STOLEN_HELM = 0x7F00BB
    BLACKBIRD_PC1_STOLEN_ARMOR = 0x7F00BC
    BLACKBIRD_PC1_STOLEN_WEAPON = 0x7F00BD
    BLACKBIRD_PC1_STOLEN_ACCESSORY = 0x7F00BE
    BLACKBIRD_PC2_STOLEN_HELM = 0x7F00BF
    BLACKBIRD_PC2_STOLEN_ARMOR = 0x7F00C0
    BLACKBIRD_PC2_STOLEN_WEAPON = 0x7F00C1
    BLACKBIRD_PC2_STOLEN_ACCESSORY = 0x7F00C2
    BLACKBIRD_PC3_STOLEN_HELM = 0x7F00C3
    BLACKBIRD_PC3_STOLEN_ARMOR = 0x7F00C4
    BLACKBIRD_PC3_STOLEN_WEAPON = 0x7F00C5
    BLACKBIRD_PC3_STOLEN_ACCESSORY = 0x7F00C6
    BLACKBIRD_IMPRISONED_PC1 = 0x7F00C7
    BLACKBIRD_IMPRISONED_PC2 = 0x7F00C8
    BLACKBIRD_IMPRISONED_PC3 = 0x7F00C9
    BLACKBIRD_STOLEN_GOLD_LO = 0x7F00CA
    BLACKBIRD_STOLEN_GOLD_MID = 0x7F00CB
    FLYING_EPOCH_CUTSCENE_COUNTER = 0x7F00CD
    LAVOS_STATUS = 0x7F00CE
    # 3 --> Impossible Ocean Palace Lavos
    BLACKBIRD_LEFT_WING_CUTSCENE_COUNTER = 0x7F00D2
    BLACKBIRD_STOLEN_GOLD_HI = 0x7F00DC
    LAVOS_ATTACK_MODE_COUNTER = 0x7F00DE
    GURU_CUTSCENE_COUNTER = 0x7F00DB  # When lavos portals them, removable.
    TIME_GAUGE_FLAGS = 0x7F0105
    MOMFLAGS = 0x7F0140
    TRUCE_MAYOR_2F_GOLD_NPC_COUNTER = 0x7F0143  # Keeps track of listening to old man
    PROTO_DOME_PORTAL_TAB_COUNTER = 0x7F014C
    CREDITS_7F015C = 0x7F015C
    NUM_DAYS_TILL_EXECUTION = 0x7F0197
    ENDING_LEGENDARY_HERO_COUNTER = 0x7F01AA
    CHARLOCK = 0x7F01DF
    MAGIC_LEARNED = 0x7F01E0
    KEEPSONG = 0x7F01ED
    PARTYFOLLOW_TEMP_ADDR = 0x7F03FE


@dataclass
class FlagData:
    address: int
    bit: int


class Flags(enum.Enum):
    # 0x7E0294 (Epoch Status)
    # Two bits to give # of PCs on epoch
    EPOCH_NUM_PCS_1 = FlagData(Memory.EPOCH_STATUS, 0x01)
    EPOCH_NUM_PCS_2 = FlagData(Memory.EPOCH_STATUS, 0x02)
    EPOCH_UNK_OMEN = FlagData(Memory.EPOCH_STATUS, 0x04)
    EPOCH_ON_OMEN = FlagData(Memory.EPOCH_STATUS, 0x08)
    EPOCH_TIME_GAUGE = FlagData(Memory.EPOCH_STATUS, 0x10)
    EPOCH_CAN_FLY = FlagData(Memory.EPOCH_STATUS, 0x20)
    EPOCH_IS_FLYING = FlagData(Memory.EPOCH_STATUS, 0x40)
    EPOCH_OBTAINED = FlagData(Memory.EPOCH_STATUS, 0x80)
    # 7F0050 (Memory.CourtFlags)
    GUARDIA_BASEMENT_GNASHERS_BATTLE = FlagData(0x7F0050, 0x08)
    KINGS_TRIAL_COMPLETE = FlagData(Memory.COURTFLAGS, 0x40)
    OBTAINED_YAKRA_KEY = FlagData(Memory.COURTFLAGS, 0x80)
    # 0x07F0054
    FAIR_HAS_RETURNED_CAT = FlagData(Memory.FAIRFLAGS, 0x01)
    FAIR_TALKED_TO_CAT_GIRL = FlagData(Memory.FAIRFLAGS, 0x02)
    FAIR_ATE_LUNCH = FlagData(Memory.FAIRFLAGS, 0x04)
    FAIR_LUCCA_ASKED_CRONO_TELEPOD = FlagData(Memory.FAIRFLAGS, 0x08)
    FAIR_PENDANT_NOT_FOUND = FlagData(Memory.FAIRFLAGS, 0x10)
    FAIR_PENDANT_PICKED_UP = FlagData(Memory.FAIRFLAGS, 0x20)
    FAIR_NOT_GIVEN_PENDANT = FlagData(Memory.FAIRFLAGS, 0x40)
    FAIR_HAS_NOT_BUMPED_MARLE = FlagData(Memory.FAIRFLAGS, 0x80)
    # 7F0055 -- All can be overwritten
    MARLE_PENDANT_SOLD_OLD = FlagData(Memory.MARLEFLAGS, 0x01)
    HAS_FAIR_RECRUIT = FlagData(Memory.MARLEFLAGS, 0x01)
    PEDNANT_BEFORE_MARLE_OLD = FlagData(Memory.MARLEFLAGS, 0x02)
    MARLE_TALK_PENDANT_OLD = FlagData(Memory.MARLEFLAGS, 0x04)
    MARLE_WANTS_CANDY_OLD = FlagData(Memory.MARLEFLAGS, 0x08)
    MARLE_FORTUNE_OLD = FlagData(Memory.MARLEFLAGS, 0x10)  # what?
    MARLE_YELLING_KIDNAPPED_OLD = FlagData(Memory.MARLEFLAGS, 0x20)
    MARLE_GIVEN_PENDANT_OLD = FlagData(Memory.MARLEFLAGS, 0x40)  # Juror 5?
    SHOWN_MARLE_FAIR = FlagData(Memory.MARLEFLAGS, 0x80)  # Acitvate telepod?
    # 7F0056 -- Telepod Flags
    # CRONO_ASKED_TO_TRY_TELEPOD = FlagData(0x7F0056, 0x01)
    # CRONO_TRIED_TELEPOD = FlagData(0x7F0056, 0x02)
    # 0xFC unused
    # 0x7F0057  -- Used for a variety of cutscenes
    ZENAN_CYRUS_SCENE = FlagData(0x7F0057, 0x02)
    ATTRACT_MODE = FlagData(0x7F0057, 0x04)
    HAS_VIEWED_LAIR_RUINS_FIRST_SCENE = FlagData(0x7F0057, 0x08)
    HAS_VIEWED_DARKAGES_PORTAL_FIRST_SCENE = FlagData(0x7F0057, 0x10)
    OCEAN_PALACE_TIME_FREEZE_ACTIVE = FlagData(0x7F0057, 0x20)  # Unused now
    CRONO_REVIVED = FlagData(0x7F0057, 0x40)
    SKYWAYS_LOCKED = FlagData(0x7F0057, 0x80)
    # 0x7F0056
    FACTORY_DEFENSE_LASERS_OFF = FlagData(0x7F0058, 0x01)
    ROBO_USED_FACTORY_RUINS_ENTRANCE_COMPUTER = FlagData(0x7F0058, 0x04)
    # 0x7F005A
    # This was used for the time when Lucca leaves Crono to escore Marle to
    # the castle.  We free it up for rando.
    LUCCA_UNUSED_01 = FlagData(Memory.LUCCAFLAGS, 0x01)
    LUCCA_CHANGING_PAST = FlagData(Memory.LUCCAFLAGS, 0x02)
    # This should become unused
    # In vanilla set after visiting Lara's room after fair or after fiona
    # forest scene.
    LUCCA_UNUSED_04 = FlagData(Memory.LUCCAFLAGS, 0x04)
    LUCCA_MAKING_WONDERSHOT = FlagData(Memory.LUCCAFLAGS, 0x08)
    LUCCA_UNUSED_10 = FlagData(Memory.LUCCAFLAGS, 0x10)
    LUCCA_TRIED_CHANGING_PAST = FlagData(Memory.LUCCAFLAGS, 0x20)
    LARA_MACHINE_STARTED = FlagData(Memory.LUCCAFLAGS, 0x40)
    LUCCA_UNUSED_80 = FlagData(Memory.LUCCAFLAGS, 0x80)
    # 0x7F005C
    TYRANO_LAIR_ENTRANCE_SKULL_OPEN = FlagData(0x7F005C, 0x10)
    # 0x7F005E
    WON_CRONO_CLONE = FlagData(0x7F005E, 0x01)
    WON_MARLE_CLONE = FlagData(0x7F005E, 0x02)
    WON_LUCCA_CLONE = FlagData(0x7F005E, 0x04)
    WON_ROBO_CLONE = FlagData(0x7F005E, 0x08)
    WON_FROG_CLONE = FlagData(0x7F005E, 0x10)
    WON_AYLA_CLONE = FlagData(0x7F005E, 0x20)
    WON_MAGUS_CLONE = FlagData(0x7F005E, 0x40)
    # 0x7F0063
    KINO_AT_TYRANO_LAIR_ENTRANCE = FlagData(0x7F0063, 0x01)
    TYRANO_MAIN_CELL_RIGHT_BATTLE = FlagData(0x7F0063, 0x02)
    TYRANO_MAIN_CELL_LEFT_BATTLE = FlagData(0x7F0063, 0x04)
    TYRANO_PRISONERS_FREED = FlagData(0x7F0063, 0x08)
    TYRANO_ANTECHAMBERS_RIGHT_TRAPDOOR_OPEN = FlagData(0x7F0063, 0x10)
    TYRANO_ANTECHAMBERS_LEFT_TRAPDOOR_OPEN = FlagData(0x7F0063, 0x20)
    # 0x7F0064
    DEATH_PEAK_CAVE_LAVOS_SPAWN = FlagData(0x7F0064, 0x08)
    # 0x7F006A
    OCEAN_PALACE_DISASTER_SCENE = FlagData(0x7F006A, 0x01)
    MAGIC_CAVE_FIRST_BATTLE = FlagData(0x7F006A, 0x20)
    GUARDIA_THRONE_1000_BLOCKED = FlagData(0x7F006A, 0x80)  # During King's Trial
    # 0x7F006D
    MELCHIOR_IN_TREASURY = FlagData(0x7F006D, 0x10)
    MELCHIOR_TREASURY_FREE_ITEM_GIVEN = FlagData(0x7F006D, 0x20)
    # 0x7F0070
    OBTAINED_KEEPERS_DOME_POWER_TAB = FlagData(0x7F0070, 0x02)
    FOUGHT_SEWERS_B1_ENTRANCE_NEREID_BATTLE = FlagData(0x7F0070, 0x20)
    # This is set at the same time as the poyozo flag
    KEEPERS_NU_COMPLETE = FlagData(0x7F0070, 0x04)
    TURNED_KEEPERS_NU_OFF = FlagData(0x7F0070, 0x08)
    # 0x7F0076
    VIEWING_KEEPERS_FLASHBACK = FlagData(0x7F0076, 0x01)
    # 0x7F0079
    MAGIC_CAVE_SEALED_CHEST = FlagData(0x7F0079, 0x01)
    # 0x7F007A
    TABAN_VEST_GIVEN = FlagData(0x7F007A, 0x01)
    TABAN_HELM_GIVEN = FlagData(0x7F007A, 0x02)
    TABAN_SUIT_GIVEN = FlagData(0x7F007A, 0x04)
    # 0x7F007C
    # This is the vanilla C.Trigger check.  Gaspar likely won't give a KI
    # in rando though.
    HAS_GASPAR_ITEM = FlagData(0x7F007C, 0x01)
    KEEPERS_NU_SENT_POYOZOS = FlagData(0x7F007C, 0x02)
    # I think it sets 0x7F007C when the machine accident begins.  If the
    # player fails to save her, 0x20 is reset and 0x40 is set.  So 0x20 also
    # functions as Lara keeping her legs.
    STARTING_LUCCA_FOREST_SCENE = FlagData(0x7F007C, 0x10)
    LARA_ACCIDENT_STARTED = FlagData(0x7F007C, 0x20)
    LARA_LOSES_LEGS = FlagData(0x7F007C, 0x40)
    # 0x7F00A0
    QUEEN_600_GUARD_MOVED = FlagData(0x7F00A0, 0x20)
    # 0x7F00A1
    MARLE_DISMISS_ATTENDANTS = FlagData(0x7F00A1, 0x01)  # in 600AD Queen's
    MARLE_DISAPPEARED = FlagData(0x7F00A1, 0x02)
    GUARDIA_TREASURY_EXISTS = FlagData(0x7F00A1, 0x40)
    # 0x7F00A2
    BARRACKS_ESCAPE = FlagData(0x7F00A2, 0x01)
    # Old: 0x7F00A2 & 02 - Ask castle chef 1000 about jerky
    HAS_ESCAPED_GUARDIA_PRISON = FlagData(0x7F00A2, 0x02)
    # 0x7F00A2 & 04 - Set while escaping "no choice but to break through"
    LUCCA_RESCUED_CRONO = FlagData(0x7F00A2, 0x04)
    # 0x7F00A2 & 08 - Set when leaving the castle while escaping
    # 0x7F00A2 & 10 - Set during escape.
    # 0x7F00A2 & 20 - Chancellor lies to Marle (indirectly killed queen)
    OBTAINED_RAINBOW_SHELL_ITEM = FlagData(0x7F00A2, 0x80)
    # 0x7F00A3
    USING_SAVE_POINT_WARP = FlagData(0x7F00A3, 0x01)
    MAGUS_CASTLE_FLEA_DEFEATED = FlagData(0x7F00A3, 0x08)
    MAGUS_CASTLE_VISITED_SLASH_ROOM = FlagData(0x7F00A3, 0x10)
    MAGUS_CASTLE_VISITED_FLEA_ROOM = FlagData(0x7F00A3, 0x20)
    # 0x7F00A4
    OBTAINED_ARRIS_FOOD_ITEM = FlagData(0x7F00A4, 0x01)
    ARRIS_LAVOS_SCENE_02 = FlagData(0x7F00A4, 0x02)
    ARRIS_LAVOS_SCENE_04 = FlagData(0x7F00A4, 0x04)
    ARRIS_LAVOS_SCENE_08 = FlagData(0x7F00A4, 0x08)
    ARRIS_LAVOS_SCENE_10 = FlagData(0x7F00A4, 0x10)
    ARRIS_AUX_CONSOLE_LEFT_SWITCH = FlagData(0x7F00A4, 0x20)
    ARRIS_AUX_CONSOLE_RIGHT_SWITCH = FlagData(0x7F00A4, 0x40)
    ARRIS_LOWER_COMMONS_SWITCH = FlagData(0x7F00A4, 0x80)
    # 0x7F00A5
    SEEN_BANGOR_SCENE = FlagData(0x7F00A5, 0x01)
    # 0x7F00A6
    HAS_TRUCE_PORTAL = FlagData(0x7F00A6, 0x01)
    HAS_BANGOR_PORTAL = FlagData(0x7F00A6, 0x02)
    HAS_DARK_AGES_PORTAL = FlagData(0x7F00A6, 0x04)  # TODO: Split this one
    HAS_LAIR_RUINS_PORTAL = FlagData(0x7F00A6, 0x08)  # Probably use this to split
    UNUSED_7F00A6_08 = FlagData(0x7F00A6, 0x08)  # Probably use this to split
    ENTERING_EOT_FACTORY = FlagData(0x7F00A6, 0x10)
    ENTERING_EOT_MEDINA = FlagData(0x7F00A6, 0x20)
    ENTERING_EOT_BUCKET = FlagData(0x7F00A6, 0x40)
    ENTERING_EOT_MYSTIC_MTS = FlagData(0x7F00A6, 0x80)
    # 0x7F00A7 & 02 - Marle and King argue
    # 0x7F00A7 & 04 - Tried to give the king jerky
    # 0x7F00A7 & 08 - Chancellor suggests giving king jerky
    # 0x7F00A7 & 20 - Talked to the king (in chamber) without jerky
    RAINBOW_SHELL_QUEST_COMPLETE = FlagData(0x7F00A7, 0x40)
    RESCUE_CHANCELLOR_1000 = FlagData(0x7F00A7, 0x80)
    # 0x7F00A8
    ENTERING_EOT_FAIR = FlagData(0x7F00A8, 0x01)
    ENTERING_EOT_TRUCE = FlagData(0x7F00A8, 0x02)
    ENTERING_EOT_FOREST = FlagData(0x7F00A8, 0x04)
    ENTERING_EOT_BANGOR = FlagData(0x7F00A8, 0x08)
    ENTERING_EOT_TYRANO_RUINS = FlagData(0x7F00A8, 0x10)
    ENTERING_EOT_DARK_AGES = FlagData(0x7F00A8, 0x20)
    ROBO_JOINS_EOT = FlagData(0x7F00A8, 0x40)
    # 0x7F00A9
    LUCCA_EXPLAINED_PARADOXES = FlagData(0x7F00A9, 0x01)
    ZENAN_REQUESTED_FOOD = FlagData(0x7F00A9, 0x04)  # Can Remove
    CHEF_PIPE_DOWN = FlagData(0x7F00A9, 0x08)
    CHEF_GIVES_JERKY = FlagData(0x7F00A9, 0x10)
    RAINBOW_SHELL_CUTSCENE_PLAYING = FlagData(0x7F00A9, 0x80)
    # 0x7F00AA
    HAS_SEEN_LAVOS_EMERGE_1999 = FlagData(0x7F00AA, 0x02)
    ENTERED_LAVOS_FROM_BUCKET = FlagData(0x7F00AA, 0x10)
    LAVOS_FLAG_UNK_40 = FlagData(0x7F00AA, 0x40)
    LAVOS_FLAG_UNK_80 = FlagData(0x7F00AA, 0x80)
    # 0x7F00AB
    HAS_SEEN_GASPAR_BUCKET_WARNING = FlagData(0x7F00AB, 0x10)
    RETURNED_TO_EOT_AFTER_DEATH_PEAK = FlagData(0x7F00AB, 0x20)
    SPARED_MAGUS = FlagData(0x7F00AB, 0x40)  # Redundant, can remove
    EPOCH_IN_EOT = FlagData(0x7F00AB, 0x80)
    # 0x7F00AC
    MAGUS_CASTLE_GHOST_KIDS_BATTLE = FlagData(0x7F00AC, 0x01)
    MAGUS_CASTLE_OZZIE_LEFT_HALL_AGGRESSION = FlagData(0x7F00AC, 0x02)
    MAGUS_CASTLE_OZZIE_LEFT_GUILLOTINES = FlagData(0x7F00AC, 0x04)
    MAGUS_CASTLE_OZZIE_LEFT_PITS = FlagData(0x7F00AC, 0x08)
    MAGUS_CASTLE_OZZIE_LEFT_HALL_APPREHENSION = FlagData(0x7F00AC, 0x10)
    MAGUS_CASTLE_OZZIE_WELCOME_GUILLOTINES = FlagData(0x7F00AC, 0x20)
    MAGUS_CASTLE_OZZIE_FASTER_GUILLOTINES = FlagData(0x7F00AC, 0x40)
    # 0x7F00AE
    MAGUS_CASTLE_SLASH_GRABBED_SWORD = FlagData(0x7F00AE, 0x04)
    MAGUS_CASTLE_SLASH_SWORD_TREASURE = FlagData(0x7F00AE, 0x08)
    MAGUS_CASTLE_GHOST_KIDS_CHEST = FlagData(0x7F00AE, 0x80)
    # 0x7F00AF
    BLACKBIRD_FOUND_PC1_GEAR = FlagData(0x7F00AF, 0x01)
    BLACKBIRD_FOUND_PC2_GEAR = FlagData(0x7F00AF, 0x02)
    BLACKBIRD_FOUND_PC3_GEAR = FlagData(0x7F00AF, 0x04)
    BLACKBIRD_PLAYED_SICK = FlagData(0x7F00AF, 0x10)
    BLACKBIRD_SEEN_EXTERIOR = FlagData(0x7F00AF, 0x20)
    BLACKBIRD_GEAR_TAKEN = FlagData(0x7F00AF, 0x40)
    BLACKBIRD_USING_GRATES = FlagData(0x7F00AF, 0x80)
    # 0x7F00B3
    BLACKBIRD_NOTICED_DUCTS = FlagData(0x7F00B3, 0x40)
    # 0x7F00B9
    BLACKBIRD_CRONO_NO_GEAR = FlagData(0x7F00B9, 0x80)
    BLACKBIRD_MARLE_NO_GEAR = FlagData(0x7F00B9, 0x40)
    BLACKBIRD_LUCCA_NO_GEAR = FlagData(0x7F00B9, 0x20)
    BLACKBIRD_ROBO_NO_GEAR = FlagData(0x7F00B9, 0x10)
    BLACKBIRD_FROG_NO_GEAR = FlagData(0x7F00B9, 0x08)
    BLACKBIRD_AYLA_NO_GEAR = FlagData(0x7F00B9, 0x04)
    BLACKBIRD_MAGUS_NO_GEAR = FlagData(0x7F00B9, 0x02)
    BLACKBIRD_RESERVED_01 = FlagData(0x7F00B9, 0x01)
    # 0x7F00BA
    # Really, this is set after recovering the Epoch from Dalton.  It's just
    # easier to access a 7F flag than the 7E epoch status.
    BLACKBIRD_ITEMS_TAKEN = FlagData(0x7F00BA, 0x01)
    BLACKBIRD_ITEMS_RECOVERED = FlagData(0x7F00BA, 0x02)
    BLACKBIRD_MONEY_RECOVERED = FlagData(0x7F00BA, 0x04)
    BLACKBIRD_KNOCKED_OUT_GUARD_REMOVED = FlagData(0x7F00BA, 0x08)
    BLACKBIRD_COMING_DOWN_DUCT = FlagData(0x7F00BA, 0x10)
    BLACKBIRD_DUCT_FOUND = FlagData(0x7F00BA, 0x40)
    OBTAINED_EPOCH_FLIGHT = FlagData(0x7F00BA, 0x80)
    # 0x7F00D1
    CAN_FIGHT_ON_BLACKBIRD = FlagData(0x7F00D1, 0x80)
    HAS_SEEN_DALTON_ON_BLACKBIRD_SCAFFOLDING = FlagData(0x7F00D1, 0x40)
    # 0x7F00D3
    RETURNED_TO_BLACKBIRD_CELL = FlagData(0x7F00D3, 0x01)
    # 0x7F00D4
    BLACKBIRD_INVENTORY_BATTLE = FlagData(0x7F00D4, 0x08)
    # 0x7F00D5
    MAGUS_CASTLE_FLEA_MAGIC_TAB = FlagData(0x7F00D5, 0x01)
    BLACKBIRD_DUCTS_POWER_TAB = FlagData(0x7F00D5, 0x10)
    # 0x7F00D8
    ASKED_GASPAR_ABOUT_GURU_OF_TIME = FlagData(0x7F00D8, 0x01)
    RECEIVED_C_TRIGGER_FROM_GASPAR = FlagData(0x7F00D8, 0x02)
    GASPAR_CALLED_PARTY_BACK = FlagData(0x7F00D8, 0x04)  # after asking about guru
    GASPAR_TOLD_SIDEQUESTS = FlagData(0x7F00D8, 0x08)
    GASPAR_WANTS_TO_TALK_MAGIC = FlagData(0x7F00D8, 0x10)
    MET_PINK_NU_SPEKKIO = FlagData(0x7F00D8, 0x20)
    # 0x7F00DD
    HAS_SEEN_LAVOS_APOCALYPSE_SCENE = FlagData(0x7F00DD, 0x04)
    # 0x7F00EC
    GUARDIAN_DEFEATED = FlagData(0x7F00EC, 0x01)
    EPOCH_OUT_OF_HANGAR = FlagData(0x7F00EC, 0x04)
    VIEWED_KEEPERS_PLOT_SPARKLES = FlagData(0x7F00EC, 0x08)
    ARRIS_RAT_CATCHABLE = FlagData(0x7F00EC, 0x10)
    HAS_SEEN_ARRIS_RAT_INSTRUCTIONS = FlagData(0x7F00EC, 0x20)
    HAS_CAUGHT_ARRIS_RAT = FlagData(0x7F00EC, 0x40)
    BLACK_TYRANO_DEFEATED = FlagData(0x7F00EC, 0x80)
    # 0x7F00ED
    VIEWED_SEWERS_INTRO_SCENE = FlagData(0x7F00ED, 0x01)
    VIEWED_FIRST_BOSS_UNDERLING_SCENE = FlagData(0x7F00ED, 0x02)
    VIEWED_SEWERS_B2_SCENE = FlagData(0x7F00ED, 0x04)
    VIEWED_SECOND_BOSS_UNDERLING_SCENE = FlagData(0x7F00ED, 0x08)
    # 0x7F00EE
    NU_ENTERED_KEEPERS_HANGAR = FlagData(0x7F00EE, 0x02)
    VIEWED_TYRANO_THRONE_AZALA_MONOLOGUE = FlagData(0x7F00EE, 0x08)
    VIEWED_NAME_EPOCH_SCENE = FlagData(0x7F00EE, 0x80)
    TYRANO_LAIR_SWITCH_FALLING = FlagData(0x7F00EE, 0x20)
    # 0x7F00EF
    VIEWED_EPOCH_FIRST_FLIGHT_SCENE = FlagData(0x7F00EF, 0x10)
    # 0x7F00F3
    MASAMUNE_DEFEATED = FlagData(0x7F00F3, 0x20)
    # 0x7F00F4
    HAS_VIEWED_ENHASA_JANUS_SCENE = FlagData(0x7F00F4, 0x04)  # Removed
    HAS_VIEWED_SCHALAS_ROOM_SCENE = FlagData(0x7F00F4, 0x10)
    OBTAINED_BLACK_ROCK = FlagData(0x7F00F4, 0x20)
    FAILED_TO_OPEN_ZEAL_THRONE_DOOR = FlagData(0x7F00F4, 0x40)
    HAS_OPENED_ZEAL_THRONE_DOOR = FlagData(0x7F00F4, 0x80)
    # 0x7F00F4
    CAN_ACCESS_KAJAR_NU_SPECIAL_SHOP_UNUSED = FlagData(0x7F00F5, 0x04)
    DISCOVERED_NU_SCRATCH_POINT = FlagData(0x7F00F5, 0x08)
    # 0x7F00F6
    OCEAN_PALACE_ELEVATOR_MAGIC_TAB = FlagData(0x7F00F6, 0x01)
    NU_SCRATCH_MAGIC_TAB = FlagData(0x7F00F6, 0x08)
    # 0x7F00F7
    PLANT_LADY_SAVES_SEED = FlagData(0x7F00F7, 0x02)
    OBTAINED_GOLD_ROCK = FlagData(0x7F00F7, 0x08)
    # 0x7F00F8
    MAGUS_ENDING_FLAG_UNK = FlagData(0x7F00F8, 0x80)
    # 0x7F00FE
    OBTAINED_NAGAETTE_BROMIDE = FlagData(0x7F00FE, 0x02)
    # 0x7F00FF
    MANORIA_SANCTUARY_ORGAN = FlagData(0x7F00FF, 0x10)
    # There is a big gap in flag memory from 0x7F0100 to 0x7F0130 or so.
    # Use these for whatever extra is needed.
    # 0x7F0100
    MAGUS_DEFEATED = FlagData(0x7F0100, 0x01)
    PENDANT_CHARGED = FlagData(0x7F0100, 0x02)
    PYRAMID_RIGHT_CHEST = FlagData(0x7F0100, 0x04)
    MANORIA_SANCTUARY_NAGAETTE_BATTLE = FlagData(0x7F0100, 0x08)
    MANORIA_BOSS_DEFEATED = FlagData(0x7F0100, 0x10)
    MANORIA_RECRUIT_OBTAINED = FlagData(0x7F0100, 0x20)
    MANORIA_RETURN_SCENE_COMPLETE = FlagData(0x7F0100, 0x40)
    CASTLE_RECRUIT_OBTAINED = FlagData(0x7F0100, 0x80)
    # 0x7F0101
    TATA_SCENE_COMPLETE = FlagData(0x7F0101, 0x01)
    OBTAINED_DENADORO_KEY = FlagData(0x7F0101, 0x02)
    OBTAINED_TATA_ITEM = FlagData(0x7F0101, 0x04)
    REPAIRED_MASAMUNE = FlagData(0x7F0101, 0x08)
    HAS_SHOWN_MEDAL = FlagData(0x7F0101, 0x10)
    OBTAINED_BURROW_LEFT_ITEM = FlagData(0x7F0101, 0x20)
    HAS_BURROW_RECRUIT = FlagData(0x7F0101, 0x40)
    OBTAINED_DOAN_ITEM = FlagData(0x7F0101, 0x80)
    # 0x7F0102
    PROTO_DOME_RECRUIT_OBTAINED = FlagData(0x7F0102, 0x01)
    FACTORY_POWER_ACTIVATED = FlagData(0x7F0102, 0x02)
    R_SERIES_DEFEATED = FlagData(0x7F0102, 0x04)
    KINO_LEFT_FOREST_MAZE = FlagData(0x7F0102, 0x08)
    NIZBEL_DEFEATED = FlagData(0x7F0102, 0x10)
    HAS_DACYTL_PERMISSION = FlagData(0x7F0102, 0x20)
    HAS_USED_MAMMON_MACHINE = FlagData(0x7F0102, 0x40)
    ZEAL_THRONE_BOSS_DEFEATED = FlagData(0x7F0102, 0x80)
    # 0x7F0103
    OCEAN_PALACE_TWIN_BOSS_DEFEATED = FlagData(0x7F0103, 0x01)
    ZEAL_HAS_FALLEN = FlagData(0x7F0103, 0x02)
    BEAST_CAVE_BOSS_DEFEATED = FlagData(0x7F0103, 0x04)
    HAS_COMPLETED_BLACKBIRD = FlagData(0x7F0103, 0x08)
    # REBORN_EPOCH_BOSS_DEFEATED = FlagData(0x7F0103, 0x10)
    MELCHIOR_TREASURY_SUNSTONE_ITEM_GIVEN = FlagData(0x7F0103, 0x20)
    PORRE_JERKY_ITEM_OBTAINED = FlagData(0x7F0103, 0x40)
    MAGUS_CASTLE_OZZIE_DEFEATED = FlagData(0x7F0103, 0x80)
    # 0x7F0104
    HECKRAN_DEFEATED = FlagData(0x7F0104, 0x01)
    HAS_BEKKLER_ITEM = FlagData(0x7F0104, 0x02)
    HAS_FORGED_MASAMUNE = FlagData(0x7F0104, 0x04)
    MT_WOE_BOSS_DEFEATED = FlagData(0x7F0104, 0x08)
    REBORN_EPOCH_BOSS_DEFEATED = FlagData(0x7F0104, 0x10)
    BUCKET_AVAILABLE = FlagData(0x7F0104, 0x20)
    BLACK_OMEN_ZEAL_AVAILABLE = FlagData(0x7F0104, 0x40)
    OBTAINED_GIANTS_CLAW_KEY = FlagData(0x7F0104, 0x80)
    # 0x7F0105 -- Time Gauge Flags
    HAS_EOT_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x01)
    HAS_FUTURE_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x02)
    HAS_APOCALYPSE_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x04)
    HAS_PRESENT_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x08)
    HAS_MIDDLE_AGES_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x10)
    HAS_DARK_AGES_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x20)
    HAS_PREHISTORY_TIMEGAUGE_ACCESS = FlagData(0x7F0105, 0x40)
    HAS_ALGETTY_PORTAL = FlagData(0x7F0105, 0x80)
    # 0x7F0106 -- Objectives
    OBJECTIVE_1_COMPLETE = FlagData(0x7F0106, 0x01)
    OBJECTIVE_2_COMPLETE = FlagData(0x7F0106, 0x02)
    OBJECTIVE_3_COMPLETE = FlagData(0x7F0106, 0x04)
    OBJECTIVE_4_COMPLETE = FlagData(0x7F0106, 0x08)
    OBJECTIVE_5_COMPLETE = FlagData(0x7F0106, 0x10)
    OBJECTIVE_6_COMPLETE = FlagData(0x7F0106, 0x20)
    OBJECTIVE_7_COMPLETE = FlagData(0x7F0106, 0x40)
    OBJECTIVE_8_COMPLETE = FlagData(0x7F0106, 0x80)
    # 0x7F0107
    HAS_ATROPOS_RIBBON_BUFF = FlagData(0x7F0107, 0x01)
    HAS_OMEN_NU_SHOP_ACCESS = FlagData(0x7F0107, 0x02)
    EPOCH_OBTAINED_LOC = FlagData(0x7F0107, 0x04)
    # 0x7F0138
    NORTH_CAPE_RECRUIT_OBTAINED = FlagData(0x7F0138, 0x01)
    NORTH_CAPE_MAGUS_DEFEATED = FlagData(0x7F0138, 0x02)
    NORTH_CAPE_MAGUS_ITEM_OBTAINED = FlagData(0x7F0138, 0x04)
    UNUSED_7F0138_08 = FlagData(0x7F0138, 0x08)
    UNUSED_7F0138_10 = FlagData(0x7F0138, 0x10)
    UNUSED_7F0138_20 = FlagData(0x7F0138, 0x20)
    UNUSED_7F0138_40 = FlagData(0x7F0138, 0x40)
    VIEWING_NORTH_CAPE_MAGUS_FLASHBACK = FlagData(0x7F0138, 0x80)
    # 0x7F0139
    FOUND_MOONSTONE_MISSING_1000 = FlagData(0x7F0139, 0x01)
    FOUND_MOONSTONE_MISSING_2300 = FlagData(0x7F0139, 0x02)
    # 0x7F013A
    SUN_PALACE_BOSS_DEFEATED = FlagData(0x7F013A, 0x01)
    SUN_PALACE_ITEM_OBTAINED = FlagData(0x7F013A, 0x02)
    MOONSTONE_PLACED_PREHISTORY = FlagData(0x7F013A, 0x04)
    RECEIVED_ = FlagData(0x7F013A, 0x08)
    DISCOVERED_MOONSTONE_MISSING_OLD = FlagData(0x7F013A, 0x08)
    RECOVERED_MOONSTONE = FlagData(0x7F013A, 0x10)
    MOONSTONE_RETURNED_1000 = FlagData(0x7F013A, 0x20)
    MOONSTONE_COLLECTED_2300 = FlagData(0x7F013A, 0x40)
    WONDERSHOT_SUNSHADES_RECEIVED = FlagData(0x7F013A, 0x80)
    # 0x7F013B
    GENO_DOME_MOTHER_BRAIN_DEFEATED = FlagData(0x7F013B, 0x10)
    GENO_DOME_ATROPOS_DEFEATED = FlagData(0x7F013B, 0x20)
    GENO_DOME_WASTE_SCENE_VIEWED = FlagData(0x7F013B, 0x40)
    GENO_DOME_USING_DUST_CHUTE = FlagData(0x7F013B, 0x80)
    # 0x7F013C
    GENO_DOME_ENTRANCE_SCENE_VIEWED = FlagData(0x7F013C, 0x01)
    GENO_DOME_PC_HAS_CHARGE = FlagData(0x7F013C, 0x40)
    # 0x7F0140
    MOM_UNUSED = FlagData(Memory.MOMFLAGS, 0x01)  # Was Lucca's name
    MOM_GAVE_MONEY = FlagData(Memory.MOMFLAGS, 0x02)
    MOM_MET_MARLE = FlagData(Memory.MOMFLAGS, 0x04)
    MOM_MET_LUCCA = FlagData(Memory.MOMFLAGS, 0x08)
    MOM_MET_ROBO = FlagData(Memory.MOMFLAGS, 0x10)
    MOM_MET_FROG = FlagData(Memory.MOMFLAGS, 0x20)
    MOM_MET_AYLA = FlagData(Memory.MOMFLAGS, 0x40)
    MOM_MET_MAGUS = FlagData(Memory.MOMFLAGS, 0x80)
    # 0x7F0146
    FIRST_TRUCE_PORTAL_TRIP = FlagData(0x7F0146, 0x01)
    # 0x7F014A
    PROTO_DOME_PORTAL_POWER_TAB = FlagData(0x7F014A, 0x01)
    GENO_DOME_CORRIDOR_POWER_TAB = FlagData(0x7F014A, 0x08)
    LAST_VILLAGE_NU_SHOP_MAGIC_TAB = FlagData(0x7F014A, 0x10)
    # 0x7F014B
    GENO_DOME_ATROPOS_POWER_TAB = FlagData(0x7F014B, 0x02)
    # 0x7F014E
    GENO_DOME_CONVEYOR_ENTRANCE_MB_TEXT = FlagData(0x7F014E, 0x01)
    GENO_DOME_CONVEYOR_EXIT_MB_TEXT = FlagData(0x7F014E, 0x02)
    GENO_DOME_LABS_MB_TEXT = FlagData(0x7F014E, 0x04)
    GENO_DOME_CORRIDOR_MB_TEXT = FlagData(0x7F014E, 0x08)
    GENO_DOME_MAINFRAME_MB_TEXT = FlagData(0x7F014E, 0x10)

    # 0x7F0150
    PROTO_DOME_ENERTRON_BATTLE = FlagData(0x7F0150, 0x08)
    # 0x7F0154
    HAS_MET_JOHNNY = FlagData(0x7F0154, 0x01)
    JOHNNY_RACE_JUST_FINISHED = FlagData(0x7F0154, 0x02)
    JOHNNY_RACE_FROM_WEST = FlagData(0x7F0154, 0x04)
    HAS_ATTEMPTED_JOHNNY_RACE = FlagData(0x7F0154, 0x08)
    # 0x7F0156
    HAS_SEEN_AYLA_MYSTIC_GULCH = FlagData(0x7F0156, 0x01)
    # 0x7F0158
    FACTORY_ENTRANCE_RIGHT_ELEVATOR = FlagData(0x7F0158, 0x08)
    FACTORY_ENTRANCE_LEFT_ELEVATOR = FlagData(0x7F0158, 0x10)
    # 0x7F015A
    TERRA_MUTANT_DEFEATED = FlagData(0x7F015A, 0x01)
    BLACK_OMEN_FINAL_PANELS_DEFEATED = FlagData(0x7F015A, 0x04)
    OCEAN_PALACE_PLATFORM_DOWN = FlagData(0x7F015A, 0x08)
    # 0x7F0160
    # In vanilla the below flag as a slightly different purpose.  It tracks the
    # first part of a cutscene has having played.
    OBTAINED_DACTYLS = FlagData(0x7F0160, 0x10)
    # 0x7F0190
    CRONO_HAS_BEEN_IMPRISONED = FlagData(0x7F0190, 0x01)
    CRONO_WAKES_IN_CELL = FlagData(0x7F0190, 0x02)
    CRONO_FREE_FROM_CELL = FlagData(0x7F0190, 0x04)  # also set if Lucca saves
    PRISON_BLUE_SHIELD_BATTLE_W = FlagData(0x7F0190, 0x10)
    PRISON_BLUE_SHIELD_BATTLE_E = FlagData(0x7F0190, 0x20)
    PRISON_OMNICRONE_BATTLE = FlagData(0x7F0190, 0x40)
    HAS_USED_EOT_TO_MEDINA = FlagData(0x7F0190, 0x80)

    # 0x7F0191
    PRISON_STAIRS_GUARD_SW_OUT = FlagData(0x7F0191, 0x01)
    PRISON_STAIRS_GUARD_SE_OUT = FlagData(0x7F0191, 0x02)
    PRISON_STAIRS_GUARD_NW_OUT = FlagData(0x7F0191, 0x04)
    PRISON_TORTURE_ROOM_SWITCH_HIT = FlagData(0x7F0191, 0x80)
    USED_PRISON_HOLE_GOING_UP = FlagData(0x7F0191, 0x10)
    USED_PRISON_HOLE_GOING_DOWN = FlagData(0x7F0191, 0x20)
    # 0x7F0198
    PRISON_TORTURE_DECEDENT_BATTLE = FlagData(0x7F0198, 0x01)
    CRONO_TAKEN_EXECUTION = FlagData(0x7F0198, 0x10)
    PRISON_SUPERVISOR_GUARD_BATTLE = FlagData(0x7F0198, 0x20)
    PRISON_STAIRS_LUCCA_GUARDS_OUT = FlagData(0x7F0198, 0x40)
    PRISON_DECEDENT_BATTLE_NW = FlagData(0x7F0198, 0x80)
    # 0x7F0199
    PRISON_CATWALKS_GUARDS_BATTLE = FlagData(0x7F0199, 0x02)
    HAS_DEFEATED_DRAGON_TANK = FlagData(0x7F0199, 0x04)
    PRISON_DECEDENT_BATTLE_SE = FlagData(0x7F0199, 0x10)
    PRISON_JUMP_BACK_FROM_GUARD = FlagData(0x7F0199, 0x20)
    PRISON_STORAGE_GUARD_BATTLE = FlagData(0x7F0199, 0x40)
    MEDINA_PORTAL_FIRST_USE = FlagData(0x7F0199, 0x80)
    # 0x7F019A
    ZENAN_CAPTAIN_ITEM = FlagData(0x7F019A, 0x01)
    ZENAN_BATTLE_1 = FlagData(0x7F019A, 0x02)
    ZENAN_BATTLE_2 = FlagData(0x7F019A, 0x04)
    MELCHIOR_WORKSHOP_CANT_LEAVE = FlagData(0x7F019A, 0x40)  # Removed

    USED_VORTEX_POINT = FlagData(0x7F019A, 0x08)
    # 0x7F019B
    MELCHIOR_WORKSHOP_FORGE_SCENE = FlagData(0x7F019B, 0x10)  # Removed
    RESCUED_FRITZ = FlagData(0x7F019B, 0x40)
    RECEIVED_PRISON_CELL_GIFT = FlagData(0x7F019B, 0x80)
    # 0x7F019C
    PYRAMID_UNLOCKED = FlagData(0x7F019C, 0x04)
    HAS_SEEN_LARUBA_TAKE_KINO_SCENE = FlagData(0x7F019C, 0x08)
    # 0x7F019E
    ROBO_HELPS_FIONA = FlagData(0x7F019E, 0x01)
    ROBO_MISSING_FROM_HELPING = FlagData(0x7F019E, 0x08)  # Only checked EoT
    CHORAS_600_TALKED_TO_CARPENTER = FlagData(0x7F019E, 0x10)  # Can Remove
    CHORAS_1000_TOOLS_PERMISSION = FlagData(0x7F019E, 0x20)
    CHORAS_600_GAVE_CARPENTER_TOOLS = FlagData(0x7F019E, 0x40)
    CHORAS_1000_RECEIVED_TOOLS = FlagData(0x7F019E, 0x80)
    # 0x7F019F
    CHORAS_600_CARPENTER_AT_RUINS = FlagData(0x7F019F, 0x01)
    NORTHERN_RUINS_LANDING_REPAIRED = FlagData(0x7F019F, 0x02)  # 1st
    NORTHERN_RUINS_BASEMENT_CORRIDOR_REPAIRED = FlagData(0x7F019F, 0x04)  # 2nd
    NORTHERN_RUINS_ANTECHAMBER_REPAIRED = FlagData(0x7F019F, 0x08)  # 3rd
    NORTHERN_RUINS_BASEMENT_SENTRIES_CLEARED = FlagData(0x7F019F, 0x20)
    # 0x7F01A0
    PYRAMID_LEFT_CHEST = FlagData(0x7F01A0, 0x01)
    OBTAINED_TOMA_ITEM = FlagData(0x7F01A0, 0x02)
    # 0x7F01A1
    MEDINA_REDEEMED = FlagData(0x7F01A1, 0x80)
    # 0x7F01A2
    INITIAL_MEDINA_IMP_DIALOG = FlagData(0x7F01A2, 0x01)
    TALKED_TO_CHORAS_1000_CARPENTER = FlagData(0x7F01A2, 0x08)
    FIRST_VISIT_MEDINA_SQUARE = FlagData(0x7F01A2, 0x20)
    SAW_CHORAS_1000_CARPENTER_DRINK = FlagData(0x7F01A2, 0x80)
    # 0x7F01A3
    SUNKEN_DESERT_BOSS_DEFEATED = FlagData(0x7F01A3, 0x01)
    HECKRAN_CAVE_ENTRANCE_INITIAL_BATTLE = FlagData(0x7F01A3, 0x02)
    INSIDE_NORTHERN_RUINS_1000 = FlagData(0x7F01A3, 0x08)
    INSIDE_NORTHERN_RUINS_600 = FlagData(0x7F01A3, 0x10)
    MASAMUNE_UPGRADED = FlagData(0x7F01A3, 0x40)
    HAS_POURED_TOMAS_POP = FlagData(0x7F01A3, 0x80)
    # 0x7F01A4
    UNUSED_ALGETTY_POWER_TAB = FlagData(0x7F01A4, 0x08)
    BEAST_NEST_POWER_TAB = FlagData(0x7F01A4, 0x10)
    MT_WOE_MAGIC_TAB = FlagData(0x7F01A4, 0x20)
    CYRUS_GRAVE_POWER_TAB = FlagData(0x7F01A4, 0x80)
    # 0x7F01A5
    BLACK_OMEN_1F_PANELS_BOTTOM = FlagData(0x7F01A5, 0x40)
    BLACK_OMEN_1F_PANELS_TOP = FlagData(0x7F01A5, 0x80)
    # 0x7F01A8
    BLACK_OMEN_MEGA_MUTANT_BATTLE = FlagData(0x7F01A8, 0x01)
    IN_BLACK_OMEN_DARKAGES = FlagData(0x7F01A8, 0x02)
    IN_BLACK_OMEN_MIDDLE_AGES = FlagData(0x7F01A8, 0x04)
    IN_BLACK_OMEN_PRESENT = FlagData(0x7F01A8, 0x08)
    IN_BLACK_OMEN_FUTURE = FlagData(0x7F01A8, 0x10)
    BLACK_OMEN_1F_INCOGNITO_BATTLE = FlagData(0x7F01A8, 0x20)
    BLACK_OMEN_MAMMON_M_BATTLE = FlagData(0x7F01A8, 0x80)
    # 0x7F01A9
    BLACK_OMEN_ELDER_SPAWN = FlagData(0x7F01A9, 0x01)
    USING_OMEN_NU_CATAPULT = FlagData(0x7F01A9, 0x04)
    # 0x7F01AC
    NORTHERN_RUINS_BASEMENT_CHEST_1000_OBTAINED = FlagData(0x7F01AC, 0x01)
    NORTHERN_RUINS_BASEMENT_CHEST_600_OBTAINED = FlagData(0x7F01AC, 0x02)
    WEST_CAPE_SPEED_TAB = FlagData(0x7F01AC, 0x10)
    RECEIVED_SILVER_ROCK = FlagData(0x7F01AC, 0x20)
    TOMA_SHOWING_GIANTS_CLAW = FlagData(0x7F01AC, 0x40)
    NORTHERN_RUINS_REPAIRS_COMPLETE = FlagData(0x7F01AC, 0x80)
    # 0x7F01AF
    RECOVERED_RAINBOW_SHELL = FlagData(0x7F01AF, 0x02)
    # 0x7F01CF
    LAVOS_TELEPOD_ACTIVE = FlagData(0x7F01CF, 0x01)
    KEEP_SONG_ON_SWITCH = FlagData(0x7F01CF, 0x40)
    SAVE_GAME_ACTIVE = FlagData(0x7F01CF, 0x80)
    # 0x7F01D0
    FACTORY_XABY_ENTERED = FlagData(0x7F01D0, 0x01)
    FACTORY_WALLS_CLOSED = FlagData(0x7F01D0, 0x02)
    OBTAINED_SNAIL_STOP_ITEM = FlagData(0x7F01D0, 0x10)
    # 7F01D1
    HUNTING_RANGE_NU_REWARD = FlagData(0x7F01D1, 0x08)
    GUARDIA_FOREST_DEAD_END_SEALED_CHEST = FlagData(0x7F01D1, 0x20)
    # 7F01D2
    GAVE_AWAY_JERKY_PORRE = FlagData(0x7F01D2, 0x04)
    GIANTS_CLAW_VIEWED_THRONE_SCENE = FlagData(0x7F01D2, 0x08)
    GIANTS_CLAW_BOSS_DEFEATED = FlagData(0x7F01D2, 0x40)
    # 7F01D3
    PORRE_MARKET_600_TAB = FlagData(0x7F01D3, 0x01)
    # 0x7F01F0 (0x7E1BA7)
    OW_VORTEX_ACTIVE = FlagData(0x7F01F0, 0x01)
    # The rest can be repurposed
    OW_FIONA_SHRINE = FlagData(0x7F01F0, 0x02)
    OW_FERRY_TO_PORRE = FlagData(0x7F01F0, 0x04)
    OW_FERRY_TO_TRUCE = FlagData(0x7F01F0, 0x08)
    OW_ARRIS_SCENE_10 = FlagData(0x7F01F0, 0x10)
    OW_ARRIS_SCENE_20 = FlagData(0x7F01F0, 0x20)
    OW_ARRIS_SCENE_40 = FlagData(0x7F01F0, 0x40)
    OW_FACTORY_DRAG_ROBO = FlagData(0x7F01F0, 0x80)
    # 0x7F01F1 (0x7E1BA8)
    OW_MAGIC_CAVE_BEAM = FlagData(0x7F01F1, 0x01)
    OW_APOCALYPSE_LAVOS_EMERGE = FlagData(0x7F01F1, 0x02)  # ?
    OW_APOCALYPSE_BTFRTC = FlagData(0x7F01F1, 0x04)  # ?
    OW_OMEN_APPEARS = FlagData(0x7F01F1, 0x08)  # ?
    OW_PORRE_SUNSTONE = FlagData(0x7F01F1, 0x10)
    OW_PREHISTORY_LAVOS_FALL = FlagData(0x7F01F1, 0x20)
    OW_DARKAGES_LAVOS_EMERGE = FlagData(0x7F01F1, 0x40)  # Start of Zeal Fall
    OW_SUNKEN_DESERT_COMPLETE = FlagData(0x7F01F1, 0x80)
    # 0x7F01F2  (0x7E1BA9)
    OW_WOE_CHAINS_UP = FlagData(0x7F01F2, 0x01)
    OW_WOE_CHAINS_DOWN = FlagData(0x7F01F2, 0x02)
    # Used on 600 AD Map.  Related to where farmer Robo is?
    OW_UNKNOWN_F2_04 = FlagData(0x7F01F2, 0x04)
    OW_UNKNOWN_F2_08 = FlagData(0x7F01F2, 0x08)
    OW_UNKNOWN_F2_10 = FlagData(0x7F01F2, 0x10)
    OW_UNKNOWN_F2_20 = FlagData(0x7F01F2, 0x20)
    OW_APOCALYPSE_LAVOS_ARRIS_SCENE = FlagData(0x7F01F2, 0x40)
    OW_ZEAL_ATTRACT_MODE = FlagData(0x7F01F2, 0x80)
    # 0x7F01F3  (0x7E1BAA)
    OW_APOLCAYPSE_ATTRACT = FlagData(0x7F01F3, 0x01)
    OW_WOE_FALL = FlagData(0x7F01F3, 0x02)
    OW_PRESENT_ATTRACT_EPOCH = FlagData(0x7F01F3, 0x04)
    OW_ATTRACT_PREHISTORY = FlagData(0x7F01F3, 0x08)
    OW_RIDE_WIND = FlagData(0x7F01F3, 0x10)
    OW_UNKNOWN_F3_20 = FlagData(0x7F01F3, 0x20)
    OW_ZEAL_FALL_KAJAR = FlagData(0x7F01F3, 0x40)
    OW_ZEAL_FALL_LAVOS_EMERGE = FlagData(0x7F01F3, 0x80)
    # 0x7F01F4  (0x7E1BAB)
    OW_BTFRTC_TRUCE_DOME = FlagData(0x7F01F4, 0x01)
    OW_CRASH_EPOCH = FlagData(0x7F01F4, 0x02)
    OW_ZEAL_FALL_PARADISE_LOST = FlagData(0x7F01F4, 0x04)
    # Unsure of these two
    OW_APOCALYPSE_RUN_AWAY = FlagData(0x7F01F4, 0x08)
    OW_APOCALYPSE_SOMETHING = FlagData(0x7F01F4, 0x10)
    OW_OZZIE_DEFEATED = FlagData(0x7F01F4, 0x20)
    OW_CYRUS_GRAVE = FlagData(0x7F01F4, 0x40)
    OW_UNKNOWN_F4_80 = FlagData(0x7F01F4, 0x80)
    # 0x7F01F5  (0x7E1BAC)
    OW_UNKNOWN_F5_01 = FlagData(0x7F01F5, 0x01)
    # Set before leaving from Keeper's Dome.  Maybe immediately throws you
    # into the time gauge?
    OW_FUTURE_UNK = FlagData(0x7F01F5, 0x02)
    OW_SKYWAY_ENHASA_S = FlagData(0x7F01F5, 0x04)
    OW_LANDBRIDGE_ENHASA_S = FlagData(0x7F01F5, 0x08)
    OW_SKYWAY_ENHASA_N = FlagData(0x7F01F5, 0x10)
    OW_LANDBRIDGE_ENHASA_N = FlagData(0x7F01F5, 0x20)
    OW_SKYWAY_KAJAR = FlagData(0x7F01F5, 0x40)
    OW_LANDBRIDGE_KAJAR = FlagData(0x7F01F5, 0x80)
    # 0x7F01F6  (0x7E1BAD)
    # Removal candidate
    OW_600AD_YEAR_KNOWN = FlagData(0x7F01F6, 0x01)
    # Another removal candidate (happens when first getting flight)
    OW_DARKAGES_FLY_TO_LAST_VILLAGE = FlagData(0x7F01F6, 0x02)
    OW_DARKAGES_OMEN_APPEARS = FlagData(0x7F01F6, 0x04)
    # Scene when Zeal2 defeated.  Removable?
    OW_OMEN_ACTIVATE_LAVOS = FlagData(0x7F01F6, 0x08)
    OW_OMEN_ACTIVATE_LAVOS_2 = FlagData(0x7F01F6, 0x10)
    # Unsure exactly which cutscene (0x7F00DA is the counter)
    OW_LAVOS_SOME_CUTSCENE = FlagData(0x7F01F6, 0x20)
    OW_ZEAL_SHOW_ELEMENTAL_WEAPONS = FlagData(0x7F01F6, 0x40)
    OW_GIANTS_CLAW_OPEN = FlagData(0x7F01F6, 0x80)
    # 0x7F01F7  (0x7E1BAE)
    OW_ZEAL_SHOW_SUN_KEEP = FlagData(0x7F01F7, 0x01)
    OW_OMEN_DARKAGES = FlagData(0x7F01F7, 0x02)
    OW_OMEN_PAST = FlagData(0x7F01F7, 0x04)
    OW_OMEN_PRESENT = FlagData(0x7F01F7, 0x08)
    OW_OMEN_FUTURE = FlagData(0x7F01F7, 0x10)
    OW_FUTURE_SHOW_CREST = FlagData(0x7F01F7, 0x20)  # Can remove
    OW_EOT_SHOW_OZZIE_FORT = FlagData(0x7F01F7, 0x40)  # Can remove
    OW_EOT_SHOW_GENO_DOME = FlagData(0x7F01F7, 0x80)  # Can remove
    # 0x7F01F8  (0x7E1BAF)
    OW_EOT_SHOW_CYRUS_GRAVE = FlagData(0x7F01F8, 0x01)
    OW_TOMA_SHOW_GIANTS_CLAW = FlagData(0x7F01F8, 0x02)
    OW_EOT_SHOW_SUN_KEEP = FlagData(0x7F01F8, 0x04)  # Can remove
    OW_UNUSED_F8_08 = FlagData(0x7F01F8, 0x08)  # ?
    OW_UNUSED_F8_10 = FlagData(0x7F01F8, 0x10)
    OW_UNUSED_F8_20 = FlagData(0x7F01F8, 0x20)
    OW_UNUSED_F8_40 = FlagData(0x7F01F8, 0x40)
    OW_UNUSED_F8_80 = FlagData(0x7F01F8, 0x80)
    # 0x7F01F9  (0x7E1BB0) -- All new for rando
    OW_ZENAN_STARTED = FlagData(0x7F01F9, 0x01)
    OW_ZENAN_COMPLETE = FlagData(0x7F01F9, 0x02)
    OW_MAGUS_DEFEATED = FlagData(0x7F01F9, 0x04)
    OW_MAGIC_CAVE_OPEN = FlagData(0x7F01F9, 0x08)
    OW_BLACK_OMEN_RISEN = FlagData(0x7F01F9, 0x10)
    OW_LAVOS_HAS_FALLEN = FlagData(0x7F01F9, 0x20)

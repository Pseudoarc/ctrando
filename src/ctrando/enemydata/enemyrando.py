"""
Randomize which enemies appear in each dungeon.
"""

from ctrando.common import ctenums, random
from ctrando.common.ctenums import EnemyID as EID
from ctrando.enemydata import enemystats
from ctrando.locations import scriptmanager

# Weird interactions with base-defunct
# - Defunct can be solo (most of NR)
# - Base can make Defunct transform into Departed (Back of NR)
# - Defunct has trigger for when hit by enemy (will break if no departed present)
# - Base can hit enemies (may cause strange triggers)

_paired_enemies: list[tuple[EID, EID]] = [
    (EID.BANTAM_IMP, EID.STONE_IMP),
    (EID.BLUE_SHIELD, EID.INCOGNITO),
    (EID.GOLD_EAGLET, EID.RED_EAGLET),
    (EID.INCOGNITO, EID.PEEPINGDOOM),
    (EID.DEFUNCT, EID.DEPARTED),
]

_required_groups: list[tuple[EID, ...]] = [
    (EID.BOSS_ORB, EID.SIDE_KICK),
    (EID.JINN, EID.BARGHEST)
]

_probably_do_not_move_enemies: tuple[EID, ...] = (
    EID.RUBBLE, EID.BOSS_ORB, EID.TURRET,  # Lock all can make combos unbeatable
    # EID.SENTRY,  # requires magic, maybe remove immunity put give max def

    # Things get weird if 30 tp fights are easy to achieve
    EID.NU, EID.NU_2,

    # Has no graphics, tied to the room's background
    EID.PANEL
)

_good_enemies = (
    EID.REPTITE_GREEN, EID.TERRASAUR, EID.KILWALA, EID.HENCH_PURPLE,
    # EID.OMICRONE,
    EID.MARTELLO, EID.BELLBIRD,
    EID.BLUE_IMP, EID.GREEN_IMP, EID.ROLY, EID.POLY, EID.ROLYPOLY,
    EID.ROLY_RIDER, EID.BLUE_EAGLET, EID.AVIAN_CHAOS, EID.IMP_ACE,
    EID.GNASHER,
    EID.GNAWER,  # maybe not, tpole interaction
    EID.NAGA_ETTE, EID.RUMINATOR, EID.OCTOPOD, EID.OCTOBLUSH,
    EID.FLY_TRAP, EID.MEAT_EATER, EID.MAN_EATER, EID.KRAKKER,
    EID.EGDER, EID.DECEASED, EID.DECEDENT, EID.MACABRE, EID.REAPER,
    EID.GUARD, EID.SENTRY, EID.FREE_LANCER, EID.OUTLAW, EID.JUGGLER,
    EID.MAGE, EID.REPTITE_PURPLE, EID.JINN_BOTTLE, EID.EVILWEEVIL,
    EID.TEMPURITE, EID.DIABLOS, EID.GARGOYLE, EID.GRIMALKIN, EID.HENCH_BLUE,
    EID.T_POLE,  # maybe not, gnawer interaction
    EID.CROAKER, EID.AMPHIBITE, EID.MAD_BAT, EID.VAMP,
    EID.SCOUTER, # maybe not, other scout interactions
    EID.FLYCLOPS, EID.BUGGER, EID.DEBUGGER, EID.DEBUGGEST, EID.SORCERER,
    EID.CRATER, EID.VOLCANO, EID.SHITAKE, EID.HETAKE, EID.SHIST,
    EID.PAHOEHOE, EID.NEREID,
    EID.SAVE_POINT_ENEMY, # maybe not
    EID.MOHAVOR, EID.SHADOW,
    EID.BASE, # maybe not - hits other enemies, expecting defunct
    EID.ACID, EID.ALKALINE, # expect to be together
    EID.ION, EID.ANION, EID.THRASHER, EID.LASHER, EID.GOBLIN,
    EID.CAVE_BAT, EID.OGAN, EID.FLUNKY, EID.GROUPIE, EID.WINGED_APE,
    EID.CAVE_APE, EID.MEGASAUR, EID.OMNICRONE, EID.BEAST, EID.LIZARDACTYL,
    EID.AVIAN_REX, EID.BLOB, EID.ALIEN, EID.RAT, EID.GREMLIN,
    EID.RUNNER, EID.PROTO_2, EID.PROTO_3, EID.PROTO_4, EID.BUG,
    EID.BEETLE, EID.GOON, EID.RAIN_FROG, EID.SYNCHRITE, EID.MUTANT,
    EID.METAL_MUTE, EID.GIGASAUR, EID.LEAPER, EID.FOSSIL_APE, EID.OCTORIDER,
    EID.CYBOT, EID.TUBSTER, EID.GUARDIAN_BYTE, EID.RED_SCOUT, EID.BLUE_SCOUT,
    EID.LASER_GUARD, EID.HEXAPOD, EID.ROLY_BOMBER, EID.BASHER,
    # Safe paired enemies
    EID.STONE_IMP, EID.GOLD_EAGLET, EID.RED_EAGLET, EID.DEFUNCT, EID.DEPARTED,  # Small
    EID.BANTAM_IMP  #
)

_small_enemies = [
    EID.REPTITE_GREEN, EID.KILWALA, EID.HENCH_PURPLE, EID.MARTELLO, EID.BELLBIRD,
    EID.BLUE_IMP, EID.GREEN_IMP, EID.ROLY, EID.POLY, EID.ROLYPOLY, EID.BLUE_EAGLET,
    EID.AVIAN_CHAOS, EID.GNASHER, EID.GNAWER, EID.NAGA_ETTE, EID.RUMINATOR, EID.OCTOPOD,
    EID.OCTOBLUSH, EID.FLY_TRAP, EID.MEAT_EATER, EID.MAN_EATER, EID.KRAKKER, EID.EGDER,
    EID.DECEASED, EID.DECEDENT, EID.GUARD, EID.SENTRY, EID.FREE_LANCER, EID.OUTLAW,
    EID.JUGGLER, EID.MAGE, EID.REPTITE_PURPLE, EID.JINN_BOTTLE, EID.EVILWEEVIL,
    EID.TEMPURITE, EID.DIABLOS, EID.GARGOYLE, EID.GRIMALKIN, EID.HENCH_BLUE, EID.T_POLE,
    EID.CROAKER, EID.AMPHIBITE, EID.MAD_BAT, EID.VAMP, EID.SCOUTER, EID.FLYCLOPS,
    EID.BUGGER, EID.DEBUGGER, EID.DEBUGGEST, EID.SORCERER, EID.CRATER, EID.VOLCANO,
    EID.SHITAKE, EID.HETAKE, EID.SHIST, EID.PAHOEHOE, EID.NEREID, EID.SAVE_POINT_ENEMY,
    EID.MOHAVOR, EID.SHADOW, EID.BASE, EID.ACID, EID.ALKALINE, EID.ION, EID.ANION, EID.THRASHER,
    EID.LASHER, EID.GOBLIN, EID.CAVE_BAT, EID.BLOB, EID.RAT, EID.GREMLIN, EID.RUNNER,
    EID.PROTO_2, EID.PROTO_3, EID.PROTO_4, EID.BUG, EID.BEETLE, EID.RAIN_FROG, EID.LEAPER,
    EID.GUARDIAN_BYTE, EID.RED_SCOUT, EID.BLUE_SCOUT, EID.LASER_GUARD, EID.ROLY_BOMBER, EID.BASHER,
    # Safe paired enemies
    EID.STONE_IMP, EID.GOLD_EAGLET, EID.RED_EAGLET, EID.DEFUNCT, EID.DEPARTED,  # Small
]

_mid_enemies = [
    EID.TERRASAUR, EID.ROLY_RIDER, EID.IMP_ACE, EID.MACABRE, EID.REAPER, EID.OGAN,
    EID.FLUNKY, EID.GROUPIE, EID.WINGED_APE, EID.CAVE_APE, EID.MEGASAUR, EID.OMNICRONE,
    EID.BEAST, EID.LIZARDACTYL, EID.AVIAN_REX, EID.ALIEN, EID.MUTANT, EID.METAL_MUTE,
    EID.GIGASAUR, EID.FOSSIL_APE, EID.OCTORIDER, EID.TUBSTER, EID.HEXAPOD,
    # Safe paired enemies
    EID.BANTAM_IMP
]

_large_enemies = [EID.GOON, EID.SYNCHRITE, EID.CYBOT]


def generate_size_lists(sprite_data_dict):
    size_groups: list[list[EID]] = [[],[],[]]


def get_enemy_shuffle(
        shuffle_enemies: bool,
        rng: random.RNGType
):
    size_groups: list[list[EID]] = [_small_enemies, _mid_enemies, _large_enemies]

    # for enemy_id in _good_enemies:
    #     size_groups[sprite_data_dict[enemy_id].sprite_size].append(enemy_id)

    if not shuffle_enemies:
        return dict(zip(_good_enemies, _good_enemies))

    assign_dict: dict[EID, EID] = {}
    for ind in range(3):
        size_group = size_groups[ind]
        shuffled_group = list(size_group)
        rng.shuffle(shuffled_group)

        assign_dict.update(
            zip(size_group, shuffled_group)
        )

    # for key, val in assign_dict.items():
    #     print(f"{key} -> {val}")

    return assign_dict

_relevant_loc_ids = [
        ctenums.LocID.GUARDIA_FOREST_1000,
        ctenums.LocID.GUARDIA_BASEMENT,
        ctenums.LocID.PRISON_CATWALKS,  # Dtank
        ctenums.LocID.PRISON_SUPERVISORS_OFFICE,
        ctenums.LocID.PRISON_TORTURE_STORAGE_ROOM,
        ctenums.LocID.MEDINA_SQUARE,  # Maybe>
        ctenums.LocID.MEDINA_ELDER_1F, ctenums.LocID.MEDINA_ELDER_2F,
        ctenums.LocID.MEDINA_INN,
        ctenums.LocID.MEDINA_MARKET,
        ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS,
        ctenums.LocID.HECKRAN_CAVE_ENTRANCE,
        ctenums.LocID.HECKRAN_CAVE_UNDERGROUND_RIVER,
        ctenums.LocID.NORTHERN_RUINS_BASEMENT,
        ctenums.LocID.NORTHERN_RUINS_ANTECHAMBER,
        ctenums.LocID.NORTHERN_RUINS_VESTIBULE,
        ctenums.LocID.NORTHERN_RUINS_BACK_ROOM,
        ctenums.LocID.PRISON_CELLS,
        ctenums.LocID.PRISON_STAIRWELLS,  # Yodu De Exception
        ctenums.LocID.BLACK_OMEN_ELEVATOR_DOWN, ctenums.LocID.BLACK_OMEN_ELEVATOR_UP,
        ctenums.LocID.ANCIENT_TYRANO_LAIR,
        ctenums.LocID.ANCIENT_TYRANO_LAIR_TRAPS,
        ctenums.LocID.TRUCE_CANYON,
        ctenums.LocID.GUARDIA_FOREST_600,
        ctenums.LocID.MAGUS_CASTLE_DOPPLEGANGER_CORRIDOR,
        ctenums.LocID.GENO_DOME_CONVEYOR,
        ctenums.LocID.MANORIA_SANCTUARY,
        ctenums.LocID.MANORIA_MAIN_HALL,
        ctenums.LocID.MANORIA_HEADQUARTERS,
        ctenums.LocID.MANORIA_ROYAL_GUARD_HALL, # Battles?
        ctenums.LocID.ZENAN_BRIDGE_600, # Remove Zombor Objs
        ctenums.LocID.CURSED_WOODS,  # Frog interaction issue
        ctenums.LocID.DENADORO_SOUTH_FACE,
        ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR,
        ctenums.LocID.DENADORO_NORTH_FACE,
        ctenums.LocID.DENADORO_ENTRANCE,
        ctenums.LocID.DENADORO_LOWER_EAST_FACE,
        ctenums.LocID.DENADORO_UPPER_EAST_FACE,
        ctenums.LocID.DENADORO_MTN_VISTA,
        ctenums.LocID.DENADORO_GAUNTLET,
        ctenums.LocID.SUNKEN_DESERT_PARASITES,
        ctenums.LocID.MAGIC_CAVE_INTERIOR,
        ctenums.LocID.MAGUS_CASTLE_ENTRANCE,
        ctenums.LocID.MAGUS_CASTLE_SLASH,  # Slash
        ctenums.LocID.MAGUS_CASTLE_HALL_AGGRESSION,
        ctenums.LocID.MAGUS_CASTLE_HALL_DECEIT,
        ctenums.LocID.MAGUS_CASTLE_HALL_APPREHENSION,
        ctenums.LocID.MAGUS_CASTLE_LOWER_BATTLEMENTS,
        ctenums.LocID.OZZIES_FORT_HALL_DISREGARD,
        ctenums.LocID.OZZIES_FORT_GUILLOTINE,
        ctenums.LocID.GIANTS_CLAW_ENTRANCE,
        ctenums.LocID.GIANTS_CLAW_CAVERNS,
        ctenums.LocID.MANORIA_SHRINE_ANTECHAMBER,
        ctenums.LocID.MANORIA_STORAGE,
        ctenums.LocID.MANORIA_KITCHEN,
        ctenums.LocID.MANORIA_SHRINE,
        ctenums.LocID.LAB_16_WEST, ctenums.LocID.LAB_16_EAST,
        ctenums.LocID.ARRIS_DOME_INFESTATION,
        ctenums.LocID.ARRIS_DOME_LOWER_COMMONS,
        ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER,
        ctenums.LocID.REPTITE_LAIR_2F,
        ctenums.LocID.LAB_32_WEST,ctenums.LocID.LAB_32, ctenums.LocID.LAB_32_EAST,
        ctenums.LocID.PROTO_DOME,
        ctenums.LocID.FACTORY_RUINS_ENTRANCE,
        ctenums.LocID.FACTORY_RUINS_AUXILIARY_CONSOLE,
        ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER,
        ctenums.LocID.FACTORY_RUINS_INFESTATION,
        ctenums.LocID.FACTORY_RUINS_CRANE_CONTROL,
        ctenums.LocID.SEWERS_B1,
        ctenums.LocID.SEWERS_B2,
        ctenums.LocID.DEATH_PEAK_SOUTH_FACE,
        ctenums.LocID.DEATH_PEAK_SOUTHEAST_FACE,
        ctenums.LocID.DEATH_PEAK_NORTHEAST_FACE,
        ctenums.LocID.GENO_DOME_LABS,
        ctenums.LocID.GENO_DOME_STORAGE,
        ctenums.LocID.GENO_DOME_ROBOT_HUB,
        ctenums.LocID.FACTORY_RUINS_DATA_CORE,
        ctenums.LocID.DEATH_PEAK_NORTHWEST_FACE,
        ctenums.LocID.DEATH_PEAK_LOWER_NORTH_FACE,
        ctenums.LocID.DEATH_PEAK_CAVE,
        ctenums.LocID.GENO_DOME_ROBOT_ELEVATOR_ACCESS,
        ctenums.LocID.GENO_DOME_MAINFRAME,
        ctenums.LocID.GENO_DOME_WASTE_DISPOSAL,
        ctenums.LocID.MYSTIC_MTN_GULCH,
        ctenums.LocID.FOREST_MAZE,  # Gold/red eaglets
        ctenums.LocID.REPTITE_LAIR_1F,
        ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B1,
        ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B2,
        ctenums.LocID.REPTITE_LAIR_COMMONS,
        ctenums.LocID.REPTITE_LAIR_TUNNEL,
        ctenums.LocID.HUNTING_RANGE,
        ctenums.LocID.DACTYL_NEST_LOWER, ctenums.LocID.DACTYL_NEST_UPPER,
        ctenums.LocID.GIANTS_CLAW_ENTRANCE,
        ctenums.LocID.TYRANO_LAIR_EXTERIOR, ctenums.LocID.TYRANO_LAIR_ENTRANCE,
        ctenums.LocID.TYRANO_LAIR_ANTECHAMBERS, ctenums.LocID.TYRANO_LAIR_STORAGE,
        ctenums.LocID.TYRANO_LAIR_ROOM_OF_VERTIGO,
        ctenums.LocID.BLACK_OMEN_1F_ENTRANCE, ctenums.LocID.BLACK_OMEN_1F_WALKWAY,
        ctenums.LocID.BLACK_OMEN_1F_DEFENSE_CORRIDOR, # No?
        ctenums.LocID.BLACK_OMEN_1F_STAIRWAY, # No eyes?
        ctenums.LocID.BLACK_OMEN_3F_WALKWAY, ctenums.LocID.BLACK_OMEN_47F_AUX_COMMAND,
        ctenums.LocID.BLACK_OMEN_47F_GRAND_HALL, ctenums.LocID.BLACK_OMEN_47F_ROYAL_PATH,
        ctenums.LocID.BLACK_OMEN_47F_ROYAL_BALLROOM, ctenums.LocID.BLACK_OMEN_47F_ROYAL_ASSEMBLY,
        ctenums.LocID.BLACK_OMEN_47F_ROYAL_PROMENADE, ctenums.LocID.BLACK_OMEN_63F_DIVINE_ESPLENADE,
        ctenums.LocID.BLACK_OMEN_97F_ASTRAL_WALKWAY,
        ctenums.LocID.BLACKBIRD_SCAFFOLDING,
        ctenums.LocID.BLACKBIRD_LEFT_WING, ctenums.LocID.BLACKBIRD_HANGAR,
        ctenums.LocID.BLACKBIRD_REAR_HALLS, ctenums.LocID.BLACKBIRD_FORWARD_HALLS,
        ctenums.LocID.BLACKBIRD_TREASURY, ctenums.LocID.BLACKBIRD_CELL,
        ctenums.LocID.BLACKBIRD_BARRACKS, ctenums.LocID.BLACKBIRD_ARMORY_3,
        ctenums.LocID.BLACKBIRD_INVENTORY, ctenums.LocID.BLACKBIRD_LOUNGE,
        ctenums.LocID.BEAST_NEST,
        ctenums.LocID.MT_WOE_WESTERN_FACE, ctenums.LocID.MT_WOE_LOWER_EASTERN_FACE,
        ctenums.LocID.MT_WOE_MIDDLE_EASTERN_FACE,
        ctenums.LocID.OCEAN_PALACE_PIAZZA, ctenums.LocID.OCEAN_PALACE_SIDE_ROOMS,
        ctenums.LocID.OCEAN_PALACE_FORWARD_AREA, ctenums.LocID.OCEAN_PALACE_B3_LANDING,
        ctenums.LocID.OCEAN_PALACE_GRAND_STAIRWELL, # Remove masa
        ctenums.LocID.OCEAN_PALACE_B20_LANDING, ctenums.LocID.OCEAN_PALACE_SOUTHERN_ACCESS_LIFT,
        ctenums.LocID.LAST_VILLAGE_COMMONS,
        ctenums.LocID.TYRANO_LAIR_MAIN_CELL,
        ctenums.LocID.FACTORY_RUINS_ROBOT_STORAGE,
        ctenums.LocID.GUARDIA_REAR_STORAGE,
        ctenums.LocID.BLACKBIRD_ACCESS_SHAFT, ctenums.LocID.BLACKBIRD_ARMORY_2,
        ctenums.LocID.BLACKBIRD_ARMORY_1,
        ctenums.LocID.MAGUS_CASTLE_UPPER_BATTLEMENTS,
        ctenums.LocID.MAGUS_CASTLE_GRAND_STAIRWAY, ctenums.LocID.BLACK_OMEN_ENTRANCE,
        ctenums.LocID.BLACK_OMEN_98F_OMEGA_DEFENSE,
        ctenums.LocID.MAGUS_CASTLE_CORRIDOR_OF_COMBAT,
        ctenums.LocID.MAGUS_CASTLE_HALL_OF_AMBUSH, ctenums.LocID.MAGUS_CASTLE_DUNGEON,
        ctenums.LocID.LAST_VILLAGE_COMMONS, # Scout the BB enemies
    ]


def verify_assign_dict(
        assign_dict: dict[EID, EID],
        sprite_data_dict: dict[EID, enemystats.EnemySpriteData],
) -> bool:
    if not set(assign_dict.keys()).issubset(_good_enemies):
        return False

    if not set(assign_dict.values()).issubset(_good_enemies):
        return False

    for key, val in assign_dict.items():
        key_data = sprite_data_dict[key]
        val_data = sprite_data_dict[val]

        if key_data.sprite_size < val_data.sprite_size:
            return False

    return True

def apply_enemy_shuffle(
        assign_dict: dict[EID, EID],
        script_manager: scriptmanager.ScriptManager,
        sprite_data_dict: dict[EID, enemystats.EnemySpriteData]
):
    if not verify_assign_dict(assign_dict, sprite_data_dict):
        print("Invalid Assign Dict")
        return

    if list(assign_dict.keys()) == list(assign_dict.values()):
        return

    for loc_id in _relevant_loc_ids:
        script = script_manager[loc_id]

        pos: None | int = None
        while True:
            pos, cmd = script.find_command_opt([0x83], pos)
            if pos is None or cmd is None:
                break

            enemy_id = cmd.args[0]
            if enemy_id in assign_dict:
                script.data[pos+1] = assign_dict[enemy_id]
            pos += len(cmd)
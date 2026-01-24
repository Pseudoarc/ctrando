"""Keep a map of the whole game"""
import typing

from ctrando.common.ctenums import RecruitID, TreasureID as TID, ShopID, LocID
from ctrando.common import memory
from ctrando.bosses.bosstypes import BossSpotID as BSID
from ctrando.objectives.objectivetypes import QuestID

from ctrando.locations.locexitdata import LocOWExits as LocExit
from ctrando.logic import logictypes


class LocRegion:
    def __init__(
            self,
            name: str,
            loc_exits: set[LocExit] | None = None,
            reward_spots: set[typing.Any] | None = None,
            region_rewards: list[typing.Any] | None = None,
            region_loc_ids: set[LocID] | None = None,
            is_combat_region: bool = False
    ):
        self.name = name
        self.loc_exits = set() if loc_exits is None else set(loc_exits)
        self.reward_spots = set() if reward_spots is None else set(reward_spots)
        self.region_rewards = [] if region_rewards is None else list(region_rewards)
        self.region_loc_ids = set() if region_loc_ids is None else set(region_loc_ids)
        self.is_combat_region = is_combat_region


def get_all_loc_regions() -> list[LocRegion]:
    ret_list: list[LocRegion] = []

    game_start = LocRegion(
        "starting_rewards",
        reward_spots={RecruitID.STARTER},
        region_rewards=[],
        region_loc_ids={LocID.LOAD_SCREEN}
    )
    ret_list.append(game_start)

    cronos_house = LocRegion(
        "cronos_house",
        loc_exits={LocExit.CRONOS_HOUSE},
        region_loc_ids={LocID.CRONOS_KITCHEN}
    )
    ret_list.append(cronos_house)
    ret_list.append(
        LocRegion(
            "cronos_house_mom",
            reward_spots={TID.CRONOS_MOM},
        )
    )
    cronos_house_clone = LocRegion(
        "cronos_house_clone",
        reward_spots={TID.BEKKLER_KEY},
        region_loc_ids={LocID.CRONOS_ROOM}
    )
    ret_list.append(cronos_house_clone)

    truce_mayor_1000 = LocRegion(
        "truce_mayor_1000",
        loc_exits={LocExit.TRUCE_MAYOR},
        reward_spots={TID.TRUCE_MAYOR_1F, TID.TRUCE_MAYOR_2F, TID.TRUCE_MAYOR_2F_OLD_MAN},
        region_loc_ids={LocID.TRUCE_MAYOR_1F, LocID.TRUCE_MAYOR_2F}
    )
    ret_list.append(truce_mayor_1000)

    truce_market_1000 = LocRegion(
        "truce_market_1000",
        loc_exits={LocExit.TRUCE_MARKET_1000},
        reward_spots={ShopID.TRUCE_MARKET_1000},
        region_loc_ids={LocID.TRUCE_MARKET}
    )
    ret_list.append(truce_market_1000)

    truce_inn_1000 = LocRegion(
        "truce_inn_1000",
        loc_exits={LocExit.TRUCE_INN_1000},
    )
    ret_list.append(truce_inn_1000)

    truce_inn_1000_sealed = LocRegion(
        "truce_inn_1000_sealed",
        reward_spots={TID.TRUCE_INN_SEALED_1000},
        region_loc_ids={LocID.TRUCE_INN_1000}
    )
    ret_list.append(truce_inn_1000_sealed)

    ret_list.append(
        LocRegion("truce_ticket_office", {LocExit.TRUCE_TICKET_OFFICE},
                  region_loc_ids={LocID.TRUCE_TICKET_OFFICE})
    )
    ret_list.append(
        LocRegion("porre_ticket_office", {LocExit.PORRE_TICKET_OFFICE},
                  region_loc_ids={LocID.PORRE_TICKET_OFFICE})
    )
    ret_list.append(
        LocRegion("zenan_bridge_1000",
                  {LocExit.ZENAN_BRIDGE_1000_NORTH, LocExit.ZENAN_BRIDGE_1000_SOUTH},
                  region_loc_ids={LocID.ZENAN_BRIDGE_1000})
    )
    ret_list.append(LocRegion("porre_inn_1000", {LocExit.PORRE_INN_1000},
                              region_loc_ids={LocID.PORRE_INN}))

    guardia_castle_1000 = LocRegion(
        "guardia_castle_1000",
        loc_exits={LocExit.GUARDIA_CASTLE_1000},
        reward_spots={TID.QUEENS_TOWER_1000, TID.QUEENS_ROOM_1000, TID.KINGS_TOWER_1000,
                      TID.KINGS_ROOM_1000, TID.GUARDIA_COURT_TOWER},
        region_loc_ids={LocID.GUARDIA_THRONEROOM_1000,
                        LocID.GUARDIA_BARRACKS_1000,
                        LocID.GUARDIA_QUEENS_TOWER_1000}
    )
    ret_list.append(guardia_castle_1000)

    guardia_castle_1000_sealed = LocRegion(
        "guardia_castle_1000_sealed",
        reward_spots={TID.GUARDIA_CASTLE_SEALED_1000},
        region_loc_ids={LocID.GUARDIA_KINGS_TOWER_1000}
    )
    ret_list.append(guardia_castle_1000_sealed)

    porre_mayor_1000 = LocRegion(
        "porre_mayor_1000",
        loc_exits={LocExit.PORRE_MAYOR_1000},
        reward_spots={TID.PORRE_MAYOR_2F},
        region_loc_ids={LocID.PORRE_MAYOR_1F}
    )
    ret_list.append(porre_mayor_1000)

    ret_list.append(
        LocRegion(
            "porre_mayor_1000_sealed",
            reward_spots={TID.PORRE_MAYOR_SEALED_1, TID.PORRE_MAYOR_SEALED_2},
            region_loc_ids={LocID.PORRE_MAYOR_2F}
        )
    )
    ret_list.append(
        LocRegion(
            "porre_market_1000", {LocExit.PORRE_MARKET_1000},
            region_rewards=[ShopID.PORRE_1000],
            region_loc_ids={LocID.PORRE_MARKET_1000}
        )
    )

    snail_stop = LocRegion(
        "snail_stop",
        loc_exits={LocExit.SNAIL_STOP},
        reward_spots={TID.SNAIL_STOP_KEY},
        region_loc_ids={LocID.SNAIL_STOP}
    )
    ret_list.append(snail_stop)

    millennial_fair = LocRegion(
        "millennial_fair",
        loc_exits={LocExit.MILLENNIAL_FAIR},
        reward_spots={BSID.MILLENNIAL_FAIR_GATO, TID.FAIR_PENDANT},
        region_rewards=[memory.Flags.HAS_TRUCE_PORTAL],
        region_loc_ids={LocID.MILLENNIAL_FAIR, LocID.GATO_EXHIBIT,
                        LocID.LEENE_SQUARE, LocID.TELEPOD_EXHIBIT},
        is_combat_region=True
    )
    ret_list.append(millennial_fair)

    millennial_fair_recruit = LocRegion(
        "millennial_fair_recruit",
        reward_spots={RecruitID.MILLENNIAL_FAIR}
    )
    ret_list.append(millennial_fair_recruit)

    millennial_fair_bekkler = LocRegion(
        "millennial_fair_bekkler",
        region_rewards=[memory.Flags.WON_CRONO_CLONE],
        region_loc_ids={LocID.BEKKLERS_LAB}
    )
    ret_list.append(millennial_fair_bekkler)

    guardia_forest_1000 = LocRegion(
        "guardia_forest_1000",
        loc_exits={LocExit.GUARDIA_FOREST_NORTH_1000, LocExit.GUARDIA_FOREST_SOUTH_1000},
        reward_spots={TID.GUARDIA_FOREST_POWER_TAB_1000},
        region_rewards=[memory.Flags.HAS_BANGOR_PORTAL],
        region_loc_ids={LocID.GUARDIA_FOREST_1000, LocID.GUARDIA_FOREST_DEAD_END},
        is_combat_region=True
    )
    ret_list.append(guardia_forest_1000)

    guardia_forest_1000_sealed = LocRegion(
        "guardia_forest_1000_sealed",
        loc_exits=set(),
        reward_spots={TID.GUARDIA_FOREST_SEALED_1000}
    )
    ret_list.append(guardia_forest_1000_sealed)

    crono_trial = LocRegion(
        "crono_trial",
        loc_exits=set(),
        reward_spots={
                RecruitID.CRONO_TRIAL,
                TID.GUARDIA_PRISON_LUNCH_BAG, TID.GUARDIA_JAIL_CELL,
                TID.GUARDIA_JAIL_OMNICRONE_1, TID.GUARDIA_JAIL_OMNICRONE_2,
                TID.GUARDIA_JAIL_OMNICRONE_3, TID.GUARDIA_JAIL_OMNICRONE_4,
                TID.GUARDIA_JAIL_HOLE_1, TID.GUARDIA_JAIL_HOLE_2,
                TID.GUARDIA_JAIL_FRITZ, TID.GUARDIA_JAIL_FRITZ_STORAGE,
                TID.GUARDIA_JAIL_OUTER_WALL, TID.PRISON_TOWER_1000,
        },
        region_loc_ids={LocID.PRISON_CATWALKS, LocID.PRISON_CELLS,
                        LocID.PRISON_SUPERVISORS_OFFICE,
                        LocID.PRISON_TORTURE_STORAGE_ROOM,
                        LocID.PRISON_EXTERIOR, LocID.PRISON_STAIRWELLS},
        region_rewards=[QuestID.CRONO_TRIAL],
        is_combat_region=True
    )
    crono_trial_boss = LocRegion(
        "crono_trial_boss",
        loc_exits=set(),
        reward_spots={BSID.PRISON_CATWALKS},
        is_combat_region=True
    )
    ret_list.append(crono_trial)
    ret_list.append(crono_trial_boss)

    heckran_cave = LocRegion(
        "heckran_cave",
        loc_exits={LocExit.HECKRAN_CAVE, LocExit.HECKRAN_CAVE_WHIRLPOOL},
        reward_spots={
            TID.HECKRAN_CAVE_1, TID.HECKRAN_CAVE_2,
            TID.HECKRAN_CAVE_ENTRANCE, TID.HECKRAN_CAVE_SIDETRACK,
            BSID.HECKRAN_CAVE
        },
        region_rewards=[memory.Flags.HECKRAN_DEFEATED, QuestID.HECKRAN_CAVE],
        region_loc_ids={LocID.HECKRAN_CAVE_BOSS, LocID.HECKRAN_CAVE_PASSAGEWAYS,
                        LocID.HECKRAN_CAVE_UNDERGROUND_RIVER, LocID.HECKRAN_CAVE_ENTRANCE},
        is_combat_region=True
    )
    ret_list.append(heckran_cave)

    heckran_sealed = LocRegion(
        "heckran_sealed",
        reward_spots={TID.HECKRAN_SEALED_1, TID.HECKRAN_SEALED_2}
    )
    ret_list.append(heckran_sealed)
    ret_list.append(LocRegion("medina_portal", {LocExit.MEDINA_PORTAL}))
    ret_list.append(
        LocRegion(
            "medina_market", {LocExit.MEDINA_MARKET},
            region_rewards=[ShopID.MEDINA_MARKET],
            region_loc_ids={LocID.MEDINA_MARKET},
            is_combat_region=True
        )
    )
    ret_list.append(LocRegion("medina_inn", {LocExit.MEDINA_INN},
                              region_loc_ids={LocID.MEDINA_INN}))
    ret_list.append(LocRegion("medina_square", {LocExit.MEDINA_SQUARE},
                              region_loc_ids={LocID.MEDINA_SQUARE}))

    medina_elder = LocRegion(
        "medina_elder",
        loc_exits={LocExit.MEDINA_ELDER},
        reward_spots={TID.MEDINA_ELDER_MAGIC_TAB, TID.MEDINA_ELDER_SPEED_TAB},
        region_loc_ids={LocID.MEDINA_ELDER_1F, LocID.MEDINA_ELDER_2F}
    )
    ret_list.append(medina_elder)

    forest_ruins = LocRegion(
        "forest_ruins",
        loc_exits={LocExit.FOREST_RUINS},
        reward_spots={TID.FOREST_RUINS},
        region_loc_ids={LocID.FOREST_RUINS}
    )
    ret_list.append(forest_ruins)

    forest_ruins_pyramid = LocRegion(
        "forest_ruins_pyramid",
        reward_spots={TID.PYRAMID_LEFT, TID.PYRAMID_RIGHT}
    )
    ret_list.append(forest_ruins_pyramid)

    luccas_house_base = LocRegion(
        "luccas_house",
        loc_exits={LocExit.LUCCAS_HOUSE},
        reward_spots=set(),
        region_loc_ids={LocID.LUCCAS_WORKSHOP}
    )
    ret_list.append(luccas_house_base)

    luccas_house_heckran = LocRegion(
        "luccas_house_heckran",
        reward_spots={TID.TABAN_GIFT_VEST}
    )
    ret_list.append(luccas_house_heckran)

    luccas_house_forge = LocRegion(
        "luccas_house_forge",
        reward_spots={TID.TABAN_GIFT_HELM}
    )
    ret_list.append(luccas_house_forge)

    luccas_house_charged_pendant = LocRegion(
        "luccas_house_charged_pendant",
        reward_spots={TID.TABAN_GIFT_SUIT}
    )
    ret_list.append(luccas_house_charged_pendant)

    luccas_house_sunstone = LocRegion(
        "luccas_house_sunstone",
        loc_exits=set(),  # TODO: Should this have an exit?  Accessed from elsewhere.
        reward_spots={TID.TABAN_SUNSHADES, TID.LUCCA_WONDERSHOT}
    )
    ret_list.append(luccas_house_sunstone)

    truce_canyon = LocRegion(
        "truce_canyon",
        loc_exits={LocExit.TRUCE_CANYON},
        reward_spots={TID.TRUCE_CANYON_1, TID.TRUCE_CANYON_2},
        region_rewards=[memory.Flags.HAS_TRUCE_PORTAL],
        region_loc_ids={LocID.TRUCE_CANYON, LocID.TRUCE_CANYON_PORTAL},
        is_combat_region=True
    )
    ret_list.append(truce_canyon)

    guardia_castle_600 = LocRegion(
        "guardia_castle_600",
        loc_exits={LocExit.GUARDIA_CASTLE_600},
        reward_spots={TID.ROYAL_KITCHEN, TID.ZENAN_BRIDGE_CHEF, TID.ZENAN_BRIDGE_CHEF_TAB,
                      TID.QUEENS_ROOM_600, TID.QUEENS_TOWER_600, TID.KINGS_TOWER_600,
                      TID.KINGS_ROOM_600},
        region_loc_ids={LocID.GUARDIA_KITCHEN_600,
                        LocID.GUARDIA_THRONEROOM_600, LocID.GUARDIA_KINGS_TOWER_600,
                        LocID.GUARDIA_KINGS_TOWER_600, LocID.GUARDIA_BARRACKS_600}
    )
    ret_list.append(guardia_castle_600)

    ret_list.append(
        LocRegion(
            "guardia_castle_600_shell",
            region_rewards=[memory.Flags.GUARDIA_TREASURY_EXISTS]
        )
    )

    guardia_castle_600_recruit = LocRegion(
        "guardia_castle_600_recruit",
        reward_spots={RecruitID.CASTLE}
    )
    ret_list.append(guardia_castle_600_recruit)

    guardia_castle_600_sealed = LocRegion(
        "guardia_castle_600_sealed",
        reward_spots={TID.GUARDIA_CASTLE_SEALED_600}
    )
    ret_list.append(guardia_castle_600_sealed)

    guardia_forest_600 = LocRegion(
        "guardia_forest_600",
        loc_exits={LocExit.GUARDIA_FOREST_NORTH_600, LocExit.GUARDIA_FOREST_SOUTH_600},
        reward_spots={TID.GUARDIA_FOREST_POWER_TAB_600},
        region_loc_ids={LocID.GUARDIA_FOREST_600},
        is_combat_region=True
    )
    ret_list.append(guardia_forest_600)

    guardia_forest_600_sealed = LocRegion(
        "guardia_forest_600_sealed",
        loc_exits=set(),
        reward_spots={TID.GUARDIA_FOREST_SEALED_600}
    )
    ret_list.append(guardia_forest_600_sealed)

    # TODO: Decide whether cathedral always dumps you into castle or not.
    #       Easier to not do castle warp and worry about softlock?
    manoria_front = LocRegion(
        "manoria_sanctuary",
        loc_exits={LocExit.MANORIA_CATHEDRAL},
        reward_spots={RecruitID.CATHEDRAL}
    )
    manoria_cathedral = LocRegion(
        "manoria_cathedral",
        reward_spots={
            TID.MANORIA_CATHEDRAL_1, TID.MANORIA_CATHEDRAL_2, TID.MANORIA_CATHEDRAL_3,
            TID.MANORIA_BROMIDE_1, TID.MANORIA_BROMIDE_2, TID.MANORIA_BROMIDE_3,
            TID.MANORIA_INTERIOR_1, TID.MANORIA_INTERIOR_2, TID.MANORIA_INTERIOR_3,
            TID.MANORIA_INTERIOR_4, TID.MANORIA_SHRINE_MAGUS_1, TID.MANORIA_SHRINE_MAGUS_2,
            TID.MANORIA_INTERIOR_1, TID.MANORIA_INTERIOR_2, TID.MANORIA_INTERIOR_3,
            TID.MANORIA_INTERIOR_4, TID.MANORIA_SHRINE_SIDEROOM_1, TID.MANORIA_SHRINE_SIDEROOM_2,
            TID.YAKRAS_ROOM, TID.MANORIA_CONFINEMENT_POWER_TAB,
            BSID.MANORIA_CATHERDAL
        },
        region_rewards=[memory.Flags.MANORIA_BOSS_DEFEATED,
                        memory.Flags.OBTAINED_NAGAETTE_BROMIDE,
                        QuestID.MANORIA_CATHEDRAL],
        region_loc_ids={LocID.MANORIA_SANCTUARY, LocID.MANORIA_SHRINE,
                        LocID.MANORIA_SHRINE, LocID.MANORIA_SHRINE_ANTECHAMBER,
                        LocID.MANORIA_STORAGE, LocID.MANORIA_KITCHEN,
                        LocID.MANORIA_COMMAND, LocID.MANORIA_MAIN_HALL,
                        LocID.MANORIA_HEADQUARTERS, LocID.MANORIA_CONFINEMENT,
                        LocID.MANORIA_ROYAL_GUARD_HALL
                        },
        is_combat_region=True
    )
    ret_list.extend([manoria_front, manoria_cathedral])

    ret_list.append(
        LocRegion(
            "truce_market_600",
            loc_exits={LocExit.TRUCE_MARKET_600},
            reward_spots={ShopID.TRUCE_MARKET_600},
            region_loc_ids={LocID.TRUCE_MARKET_600}
        )
    )

    denadoro_mts = LocRegion(
        "denadoro_mts",
        loc_exits={LocExit.DENADORO_MTS},
        reward_spots={
            TID.DENADORO_MTS_SCREEN2_1, TID.DENADORO_MTS_SCREEN2_2, TID.DENADORO_MTS_SCREEN2_3,
            TID.DENADORO_MTS_FINAL_1, TID.DENADORO_MTS_FINAL_2, TID.DENADORO_MTS_FINAL_3,
            TID.DENADORO_MTS_WATERFALL_TOP_1, TID.DENADORO_MTS_WATERFALL_TOP_2,
            TID.DENADORO_MTS_WATERFALL_TOP_3, TID.DENADORO_MTS_WATERFALL_TOP_4,
            TID.DENADORO_MTS_WATERFALL_TOP_5, TID.DENADORO_MTS_ENTRANCE_1,
            TID.DENADORO_MTS_ENTRANCE_2, TID.DENADORO_MTS_SCREEN3_1,
            TID.DENADORO_MTS_SCREEN3_2, TID.DENADORO_MTS_SCREEN3_3, TID.DENADORO_MTS_SCREEN3_4,
            TID.DENADORO_MTS_AMBUSH, TID.DENADORO_MTS_SAVE_PT,
            TID.DENADORO_MTS_KEY, TID.MOUNTAINS_RE_NICE_MAGIC_TAB,
            TID.DENADORO_MTS_SPEED_TAB,
            BSID.DENADORO_MTS
        },
        region_rewards=[memory.Flags.TATA_SCENE_COMPLETE,
                        QuestID.DENADORO_MOUNTAINS],
        region_loc_ids={LocID.DENADORO_SOUTH_FACE, LocID.DENADORO_CAVE_OF_MASAMUNE_EXTERIOR,
                        LocID.DENADORO_CAVE_OF_MASAMUNE, LocID.DENADORO_NORTH_FACE,
                        LocID.DENADORO_ENTRANCE, LocID.DENADORO_LOWER_EAST_FACE,
                        LocID.DENADORO_UPPER_EAST_FACE, LocID.DENADORO_WEST_FACE},
        is_combat_region=True
    )
    ret_list.append(denadoro_mts)

    dorino_bromide = LocRegion(
        "dorino_bromide_base",
        loc_exits={LocExit.DORINO_BROMIDE_RESIDENCE},
    )
    ret_list.append(dorino_bromide)
    ret_list.append(
        LocRegion(
            "dorino_bromide_reward",
            reward_spots={TID.DORINO_BROMIDE_MAGIC_TAB}
        )
    )
    ret_list.append(
        LocRegion(
            "dorino_maket", {LocExit.DORINO_MARKET},
            region_rewards=[ShopID.DORINO],
            region_loc_ids={LocID.DORINO_MARKET}
        )
    )
    ret_list.append(LocRegion("dorino_inn", {LocExit.DORINO_INN},
                              region_loc_ids={LocID.DORINO_INN}))
    ret_list.append(LocRegion("dorino_inn_marle",
                              reward_spots={TID.DORINO_INN_POWERMEAL}))

    fionas_villa = LocRegion(
        "fionas_villa",
        loc_exits={LocExit.FIONAS_VILLA},
        reward_spots={TID.FIONAS_HOUSE_1, TID.FIONAS_HOUSE_2},
        region_loc_ids={LocID.FIONAS_VILLA}
    )
    ret_list.append(fionas_villa)
    ret_list.append(
        LocRegion(
            "fionas_villa_desert",
            region_rewards=[memory.Flags.ROBO_HELPS_FIONA]
        )
    )

    cursed_woods = LocRegion(
        "cursed_woods",
        loc_exits={LocExit.CURSED_WOODS},
        reward_spots={TID.CURSED_WOODS_1, TID.CURSED_WOODS_2,
                      TID.FROGS_BURROW_RIGHT},
        region_loc_ids={LocID.CURSED_WOODS, LocID.FROGS_BURROW},
        is_combat_region=True
    )
    ret_list.append(cursed_woods)

    burrow_medal = LocRegion(
        "burrow_medal",
        loc_exits=set(),
        reward_spots={TID.FROGS_BURROW_LEFT}
    )
    ret_list.append(burrow_medal)

    burrow_recruit = LocRegion(
        "burrow_recruit",
        loc_exits=set(),
        reward_spots={RecruitID.FROGS_BURROW}
    )
    ret_list.append(burrow_recruit)

    porre_market = LocRegion(
        "porre_market_600",
        loc_exits={LocExit.PORRE_MARKET_600},
        reward_spots={TID.PORRE_MARKET_600_POWER_TAB},
        region_loc_ids={LocID.PORRE_MARKET_600}
    )
    ret_list.append(porre_market)
    ret_list.append(LocRegion("porre_cafe_600", {LocExit.PORRE_CAFE_600},
                              region_loc_ids={LocID.PORRE_CAFE_600}))
    ret_list.append(LocRegion("porre_inn_600", {LocExit.PORRE_INN_600},
                              region_loc_ids={LocID.PORRE_INN_600}))

    lab_16 = LocRegion(
        "lab_16",
        loc_exits={LocExit.LAB_16_EAST, LocExit.LAB_16_WEST},
        reward_spots={TID.LAB_16_1, TID.LAB_16_2, TID.LAB_16_3, TID.LAB_16_4},
        region_loc_ids={LocID.LAB_16_WEST, LocID.LAB_16_EAST},
        is_combat_region=True
    )
    ret_list.append(lab_16)

    lab_32_west = LocRegion(
        "lab_32_west",
        loc_exits={LocExit.LAB_32_WEST},
        reward_spots={TID.LAB_32_1},
        region_loc_ids={LocID.LAB_32_WEST}
    )
    ret_list.append(lab_32_west)

    lab_32_east = LocRegion(
        "lab_32_east",
        loc_exits={LocExit.LAB_32_EAST},
        reward_spots=set(),
        region_loc_ids={LocID.LAB_32_EAST},
        is_combat_region=True
    )
    ret_list.append(lab_32_east)

    lab_32_middle = LocRegion(
        "lab_32_middle",
        loc_exits=set(),
        reward_spots={TID.LAB_32_RACE_LOG},
        region_loc_ids={LocID.LAB_32},
        is_combat_region=True
    )
    ret_list.append(lab_32_middle)

    johnny_race = LocRegion(
        "johnny_race",
        loc_exits=set(),
        region_rewards=[QuestID.DEFEAT_JOHNNY]
    )
    ret_list.append(johnny_race)

    sewers = LocRegion(
        "sewers",
        loc_exits={LocExit.SEWER_ACCESS_ARRIS, LocExit.SEWER_ACCESS_KEEPERS},
        reward_spots={TID.SEWERS_1, TID.SEWERS_2, TID.SEWERS_3, BSID.SEWERS_KRAWLIE},
        region_loc_ids={LocID.SEWERS_B1, LocID.SEWERS_B2},
        is_combat_region=True
    )
    ret_list.append(sewers)

    death_peak_entrance = LocRegion(
        "death_peak_entrance",
        loc_exits={LocExit.DEATH_PEAK, LocExit.DEATH_PEAK_FALL},
        reward_spots={TID.DEATH_PEAK_POWER_TAB},
        region_loc_ids={LocID.DEATH_PEAK_ENTRANCE}
    )
    ret_list.append(death_peak_entrance)

    death_peak = LocRegion(
        "death_peak",
        loc_exits=set(),
        reward_spots={
            RecruitID.DEATH_PEAK,
            TID.DEATH_PEAK_SOUTH_FACE_KRAKKER, TID.DEATH_PEAK_SOUTH_FACE_SPAWN_SAVE,
            TID.DEATH_PEAK_SOUTH_FACE_SUMMIT, TID.DEATH_PEAK_FIELD,
            TID.DEATH_PEAK_KRAKKER_PARADE, TID.DEATH_PEAK_CAVES_LEFT,
            TID.DEATH_PEAK_CAVES_CENTER, TID.DEATH_PEAK_CAVES_RIGHT,
            BSID.DEATH_PEAK
        },
        region_loc_ids={LocID.DEATH_PEAK_SUMMIT, LocID.DEATH_PEAK_SOUTH_FACE,
                        LocID.DEATH_PEAK_SOUTHEAST_FACE, LocID.DEATH_PEAK_NORTHEAST_FACE,
                        LocID.DEATH_PEAK_NORTHWEST_FACE, LocID.DEATH_PEAK_LOWER_NORTH_FACE,
                        LocID.DEATH_PEAK_CAVE, LocID.DEATH_PEAK_GUARDIAN_SPAWN,
                        LocID.DEATH_PEAK_SUMMIT_AFTER, LocID.DEATH_PEAK_SOUTH_FACE},
        region_rewards=[QuestID.DEATH_PEAK],
        is_combat_region=True
    )
    ret_list.append(death_peak)

    arris_dome = LocRegion(
        "arris_dome",
        loc_exits={LocExit.ARRIS_DOME},
        reward_spots={
            TID.ARRIS_DOME_FOOD_STORE, TID.ARRIS_DOME_RATS,
            TID.ARRIS_DOME_FOOD_LOCKER_KEY, BSID.ARRIS_DOME
        },
        region_loc_ids={LocID.ARRIS_DOME_COMMAND, LocID.ARRIS_DOME_RAFTERS,
                        LocID.ARRIS_DOME_INFESTATION,
                        LocID.ARRIS_DOME_AUXILIARY_CONSOLE, LocID.ARRIS_DOME,
                        LocID.ARRIS_DOME_GUARDIAN_CHAMBER, LocID.ARRIS_DOME_LOWER_COMMONS},
        is_combat_region=True
    )
    ret_list.append(arris_dome)

    arris_dome_sealed = LocRegion(
        "arris_dome_sealed",
        reward_spots={TID.ARRIS_DOME_SEAL_1, TID.ARRIS_DOME_SEAL_2,
                      TID.ARRIS_DOME_SEAL_3, TID.ARRIS_DOME_SEAL_4,
                      TID.ARRIS_DOME_SEALED_POWER_TAB},
        region_loc_ids={LocID.ARRIS_DOME_SEALED_ROOM}
    )
    ret_list.append(arris_dome_sealed)

    arris_dome_doan = LocRegion(
        "arris_dome_doan",
        reward_spots={TID.ARRIS_DOME_DOAN_KEY},
        region_rewards=[QuestID.ARRIS_DOME]
    )
    ret_list.append(arris_dome_doan)

    proto_dome = LocRegion(
        "proto_dome",
        loc_exits={LocExit.PROTO_DOME},
        reward_spots={RecruitID.PROTO_DOME},
        region_loc_ids={LocID.PROTO_DOME},
        is_combat_region=True
    )
    ret_list.append(proto_dome)
    ret_list.append(
        LocRegion("proto_dome_portal", reward_spots={TID.PROTO_DOME_PORTAL_TAB})
    )

    factory_ruins = LocRegion("factory_ruins", {LocExit.FACTORY_RUINS})
    factory_ruins_inside = LocRegion(
        "factory_ruins_inside",
        reward_spots={
            TID.FACTORY_LEFT_AUX_CONSOLE, TID.FACTORY_LEFT_SECURITY_LEFT,
            TID.FACTORY_LEFT_SECURITY_RIGHT, TID.FACTORY_RIGHT_FLOOR_TOP,
            TID.FACTORY_RIGHT_FLOOR_LEFT, TID.FACTORY_RIGHT_FLOOR_BOTTOM,
            TID.FACTORY_RIGHT_FLOOR_SECRET, TID.FACTORY_RIGHT_CRANE_UPPER,
            TID.FACTORY_RIGHT_CRANE_LOWER, TID.FACTORY_RIGHT_INFO_ARCHIVE,
            TID.FACTORY_RIGHT_DATA_CORE_1, TID.FACTORY_RIGHT_DATA_CORE_2,
            TID.FACTORY_RUINS_GENERATOR,
            BSID.FACTORY_RUINS
        },
        region_rewards=[memory.Flags.PROTO_DOME_DOOR_UNLOCKED,
                        QuestID.FACTORY_RUINS],
        region_loc_ids={LocID.FACTORY_RUINS_ENTRANCE, LocID.FACTORY_RUINS_AUXILIARY_CONSOLE,
                        LocID.FACTORY_RUINS_SECURITY_CENTER, LocID.FACTORY_RUINS_INFESTATION,
                        LocID.FACTORY_RUINS_CRANE_ROOM, LocID.FACTORY_RUINS_CRANE_CONTROL,
                        LocID.FACTORY_RUINS_DATA_CORE, LocID.FACTORY_RUINS_ROBOT_STORAGE},
        is_combat_region=True
    )
    ret_list.append(factory_ruins)
    ret_list.append(factory_ruins_inside)

    keepers_dome = LocRegion(
        "keepers_dome",
        loc_exits={LocExit.KEEPERS_DOME},
        region_loc_ids={LocID.KEEPERS_DOME}
    )
    ret_list.append(keepers_dome)

    keepers_dome_sealed = LocRegion(
        "keepers_dome_sealed",
        reward_spots={TID.KEEPERS_DOME_MAGIC_TAB},
        region_rewards=[memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS,
                        memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
                        logictypes.ScriptReward.EPOCH],
        region_loc_ids={LocID.KEEPERS_DOME_HANGAR, LocID.KEEPERS_DOME_CORRIDOR}
    )
    ret_list.append(keepers_dome_sealed)

    dactyl_nest = LocRegion(
        "dactyl_nest",
        loc_exits={LocExit.DACTYL_NEST},
        reward_spots={
            TID.DACTYL_NEST_1, TID.DACTYL_NEST_2, TID.DACTYL_NEST_3,
        },
        region_loc_ids={LocID.DACTYL_NEST_LOWER, LocID.DACTYL_NEST_UPPER},
        is_combat_region=True
    )
    ret_list.append(dactyl_nest)

    dactyl_nest_recruit = LocRegion(
        "dactyl_nest_recruit",
        reward_spots={RecruitID.DACTYL_NEST},
        region_rewards=[memory.Flags.OBTAINED_DACTYLS],
        region_loc_ids={LocID.DACTYL_NEST_SUMMIT}
    )
    ret_list.append(dactyl_nest_recruit)

    mystic_mts = LocRegion(
        "mystic_mts",
        loc_exits={LocExit.MYSTIC_MTS},
        reward_spots={TID.MYSTIC_MT_STREAM},
        region_loc_ids={LocID.MYSTIC_MTN_BASE, LocID.MYSTIC_MTN_PORTAL,
                        LocID.MYSTIC_MTN_GULCH},
        is_combat_region=True
    )
    ret_list.append(mystic_mts)

    hunting_range = LocRegion(
        "hunting_range",
        loc_exits={LocExit.HUNTING_RANGE},
        reward_spots={TID.HUNTING_RANGE_NU_REWARD},
        region_loc_ids={LocID.HUNTING_RANGE},
        region_rewards=[logictypes.StrangeReward.TRADING_MATERIALS],
        is_combat_region=True
    )
    ret_list.append(hunting_range)

    laruba_ruins = LocRegion(
        "laruba_ruins",
        loc_exits={LocExit.LARUBA_RUINS},
        reward_spots={TID.LARUBA_ROCK},
        region_loc_ids={LocID.LARUBA_RUINS}
    )
    laruba_ruins_chief = LocRegion(
        "laruba_ruins_chief",
        region_rewards=[memory.Flags.OBTAINED_DACTYLS]
    )
    ret_list.extend([laruba_ruins, laruba_ruins_chief])
    ret_list.append(
        LocRegion(
            "ioka_meeting_site", {LocExit.IOKA_MEETING_NORTH, LocExit.IOKA_MEETING_SOUTH},
            region_loc_ids={LocID.IOKA_MEETING_SITE}
        )
    )
    ret_list.append(LocRegion("ioka_chief_hut", {LocExit.CHIEFS_HUT}))
    ret_list.append(
        LocRegion(
            "ioka_trading_post", {LocExit.TRADING_POST},
            region_rewards=[ShopID.IOKA_VILLAGE],
            region_loc_ids={LocID.IOKA_TRADING_POST},
        )
    )
    ret_list.append(
        LocRegion(
            "ioka_trading_post_base",
            reward_spots={
                TID.TRADING_POST_PETAL_FANG_BASE, TID.TRADING_POST_PETAL_HORN_BASE,
                TID.TRADING_POST_PETAL_FEATHER_BASE, TID.TRADING_POST_FANG_FEATHER_BASE,
                TID.TRADING_POST_FANG_HORN_BASE, TID.TRADING_POST_HORN_FEATHER_BASE,
            },
        )
    )
    ret_list.append(
        LocRegion(
            "ioka_trading_post_upgrade",
            reward_spots={
                TID.TRADING_POST_PETAL_FANG_UPGRADE, TID.TRADING_POST_PETAL_HORN_UPGRADE,
                TID.TRADING_POST_PETAL_FEATHER_UPGRADE, TID.TRADING_POST_FANG_FEATHER_UPGRADE,
                TID.TRADING_POST_FANG_HORN_UPGRADE, TID.TRADING_POST_HORN_FEATHER_UPGRADE
            },
        )
    )
    ret_list.append(
        LocRegion(
            "ioka_trading_post_special",
            reward_spots={TID.TRADING_POST_SPECIAL},
        )
    )
    ret_list.append(LocRegion("ioka_sw_hut", {LocExit.IOKA_SW_HUT},
                              region_loc_ids={LocID.IOKA_SOUTHWEST_HUT}))
    ret_list.append(LocRegion("ioka_sweet_water_hut", {LocExit.IOKA_SWEET_WATER_HUT},
                              region_loc_ids={LocID.IOKA_SWEETWATER_HUT}))
    ret_list.append(LocRegion("ioka_sweet_water_hut_ayla",
                              reward_spots={TID.IOKA_SWEETWATER_TONIC}))
    ret_list.append(
        LocRegion(
        "lair_ruins_portal", {LocExit.LAIR_RUINS},
            region_rewards=[
                memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
                memory.Flags.HAS_LAIR_RUINS_PORTAL,
                memory.Flags.HAS_DARK_AGES_PORTAL,
            ],
            region_loc_ids={LocID.LAIR_RUINS_PORTAL}
        )
    )

    ret_list.append(LocRegion("choras_mayor", {LocExit.CHORAS_MAYOR_1000},
                              region_loc_ids={LocID.CHORAS_MAYOR_1F, LocID.CHORAS_MAYOR_2F}))
    ret_list.append(LocRegion("choras_inn_1000", {LocExit.CHORAS_INN_1000},
                              region_rewards=[memory.Flags.TALKED_TO_CHORAS_1000_CARPENTER],
                              region_loc_ids={LocID.CHORAS_INN_1000}))
    ret_list.append(
        LocRegion("choras_1000_carpenter_base", {LocExit.CHORAS_CARPTENTER_1000},
                  region_loc_ids={LocID.CHORAS_CARPENTER_1000})
    )
    choras_carpenter_wife = LocRegion(
        "choras_1000_carpenter_wife", reward_spots={TID.LAZY_CARPENTER},
    )
    ret_list.append(choras_carpenter_wife)

    choras_west_cape = LocRegion(
        "choras_west_cape",
        loc_exits={LocExit.WEST_CAPE},
        reward_spots={TID.TOMAS_GRAVE_SPEED_TAB},
        region_loc_ids={LocID.WEST_CAPE}
    )
    ret_list.append(choras_west_cape)

    choras_west_cape_grave = LocRegion(
        "choras_west_cape_grave",
        region_rewards=[memory.Flags.OW_GIANTS_CLAW_OPEN]
    )
    ret_list.append(choras_west_cape_grave)

    northern_ruins_1000 = LocRegion(
        "northern_ruins_1000",
        loc_exits={LocExit.NORTHERN_RUINS_1000},
    )
    ret_list.append(northern_ruins_1000)
    ret_list.append(
        LocRegion(
            "northern_ruins_1000_repaired",
            reward_spots={
                TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000,
                TID.NORTHERN_RUINS_LANDING_POWER_TAB,
                TID.NORTHERN_RUINS_HEROS_GRAVE_MAGIC_TAB,
            },
        )
    )

    northern_ruins_1000_sealed = LocRegion(
        "northern_ruins_1000_sealed",
        loc_exits=set(),
        reward_spots={
            TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_1000,
            TID.NORTHERN_RUINS_BACK_LEFT_SEALED_1000,
            TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_1000,
        }
    )
    ret_list.append(northern_ruins_1000_sealed)

    northern_ruins_1000_frog = LocRegion(
        "northern_ruins_1000_frog",
        reward_spots={TID.NORTHERN_RUINS_BASEMENT_1000}
    )
    ret_list.append(northern_ruins_1000_frog)

    # put NR LocIDs in 600
    cyrus_grave = LocRegion(
        "cyrus_grave_600",
        reward_spots={TID.CYRUS_GRAVE_KEY},
        region_rewards=[memory.Flags.MASAMUNE_UPGRADED,
                        QuestID.CYRUS_GRAVE],
        region_loc_ids={LocID.NORTHERN_RUINS_HEROS_GRAVE}
    )
    ret_list.append(cyrus_grave)

    guardia_castle_treasury = LocRegion(
        "guardia_castle_treasury",
        reward_spots={
            TID.GUARDIA_TREASURY_1, TID.GUARDIA_TREASURY_2, TID.GUARDIA_TREASURY_3,
            TID.GUARDIA_BASEMENT_1, TID.GUARDIA_BASEMENT_2, TID.GUARDIA_BASEMENT_3
        },
        region_loc_ids={LocID.GUARDIA_BASEMENT, LocID.GUARDIA_REAR_STORAGE},
        is_combat_region=True
    )
    ret_list.append(guardia_castle_treasury)

    guardia_castle_treasury_shell = LocRegion(
        "guardia_castle_rbow_shell",
        reward_spots={TID.KINGS_TRIAL_KEY}
    )
    ret_list.append(guardia_castle_treasury_shell)

    kings_trial_resolution = LocRegion(
        "kings_trial_resolution",
        reward_spots={BSID.KINGS_TRIAL, TID.MELCHIOR_RAINBOW_SHELL},
        region_loc_ids={LocID.COURTROOM},
        region_rewards=[QuestID.KINGS_TRIAL],
        is_combat_region=True
    )
    ret_list.append(kings_trial_resolution)

    melchior_forge_castle = LocRegion(
        "melchior_forge_castle",
        reward_spots={TID.MELCHIOR_SUNSTONE_RAINBOW, TID.MELCHIOR_SUNSTONE_SPECS}
    )
    ret_list.append(melchior_forge_castle)

    porre_elder_600_base = LocRegion(
        "porre_elder_600", {LocExit.PORRE_ELDER_600}
    )
    ret_list.append(porre_elder_600_base)

    porre_elder_600 = LocRegion(
        "porre_elder_600_jerky",
        region_rewards=[memory.Flags.GAVE_AWAY_JERKY_PORRE]
    )
    ret_list.append(porre_elder_600)

    porre_elder_600_sealed = LocRegion(
        "porre_elder_600_sealed",
        reward_spots={TID.PORRE_ELDER_SEALED_1, TID.PORRE_ELDER_SEALED_2}
    )
    ret_list.append(porre_elder_600_sealed)

    porre_mayor = LocRegion(
        "porre_mayor_moonstone",
        reward_spots={TID.JERKY_GIFT},
        region_rewards=[QuestID.JERKY_TRADE]
    )
    ret_list.append(porre_mayor)

    melchoirs_hut = LocRegion(
        "melchiors_hut",
        loc_exits={LocExit.MELCHIORS_HUT},
        reward_spots={ShopID.MELCHIORS_HUT}
    )
    ret_list.append(melchoirs_hut)
    forge_masa = LocRegion(
        "melchiors_hut_forge",
        reward_spots={TID.MELCHIOR_FORGE_MASA},
        region_rewards=[memory.Flags.HAS_FORGED_MASAMUNE,
                        QuestID.FORGE_MASAMUNE]
    )
    ret_list.append(forge_masa)

    ret_list.append(
        LocRegion("truce_inn_600", {LocExit.TRUCE_INN_600})
    )
    truce_inn_600_sealed = LocRegion(
        "truce_inn_600_sealed",
        reward_spots={TID.TRUCE_INN_SEALED_600}
    )
    ret_list.append(truce_inn_600_sealed)

    bangor_dome = LocRegion(
        "bangor_dome",
        loc_exits={LocExit.BANGOR_DOME},
        region_rewards=[memory.Flags.HAS_BANGOR_PORTAL]
    )
    ret_list.append(bangor_dome)

    bangor_dome_sealed = LocRegion(
        "bangor_dome_sealed",
        reward_spots={TID.BANGOR_DOME_SEAL_1, TID.BANGOR_DOME_SEAL_2, TID.BANGOR_DOME_SEAL_3}
    )
    ret_list.append(bangor_dome_sealed)

    trann_dome = LocRegion(
        "trann_dome",
        loc_exits={LocExit.TRANN_DOME},
        reward_spots={ShopID.TRANN_DOME}
    )
    ret_list.append(trann_dome)

    trann_dome_sealed = LocRegion(
        "trann_dome_sealed",
        reward_spots={TID.TRANN_DOME_SEAL_1, TID.TRANN_DOME_SEAL_2, TID.TRANN_DOME_SEALED_MAGIC_TAB}
    )
    ret_list.append(trann_dome_sealed)

    zenan_bridge_600 = LocRegion(
        "zenan_bridge_600",
        loc_exits={LocExit.ZENAN_BRIDGE_600_NORTH},  # Ignore South Exit
        reward_spots={BSID.ZENAN_BRIDGE, TID.ZENAN_BRIDGE_CAPTAIN},
        region_loc_ids={LocID.ZENAN_BRIDGE_600, LocID.ZENAN_BRIDGE_BOSS},
        region_rewards=[QuestID.ZENAN_BRIDGE],
        is_combat_region=True
    )
    ret_list.append(zenan_bridge_600)

    tatas_house = LocRegion(
        "tatas_house",
        loc_exits={LocExit.TATAS_HOUSE},
    )
    ret_list.append(tatas_house)
    ret_list.append(
        LocRegion("tata_reward", reward_spots={TID.TATA_REWARD})
    )

    denadoro_rock = LocRegion(
        "denadoro_gold_rock",
        reward_spots={TID.DENADORO_ROCK}
    )
    ret_list.append(denadoro_rock)

    sun_keep_600 = LocRegion(
        "sun_keep_600",
        loc_exits={LocExit.SUN_KEEP_600},
        reward_spots={TID.SUN_KEEP_600_POWER_TAB},
        region_loc_ids={LocID.SUN_KEEP_600}
    )
    ret_list.append(sun_keep_600)

    choras_cafe_600 = LocRegion(
        "choras_cafe_600",
        loc_exits={LocExit.CHORAS_CAFE_600},
        reward_spots={TID.TOMA_REWARD},
    )
    ret_list.append(choras_cafe_600)
    ret_list.append(
        LocRegion(
            "choras_cafe_600_tools",
            region_rewards=[memory.Flags.CHORAS_600_GAVE_CARPENTER_TOOLS]
        )
    )
    ret_list.append(
        LocRegion(
            "choras_market_600", {LocExit.CHORAS_MARKET_600},
            reward_spots={ShopID.CHORAS_MARKET_600}
        )
    )
    ret_list.append(LocRegion("choras_old_residence_600", {LocExit.CHORAS_OLD_RESIDENCE_600}))
    ret_list.append(LocRegion("choras_inn_600", {LocExit.CHORAS_INN_600}))

    ret_list.append(
        LocRegion(
            "choras_carpenter_600_base",
            loc_exits={LocExit.CHORAS_CARPTENTER_600}
        )
    )
    ret_list.append(
        LocRegion(
            "choras_carpenter_600",
            region_rewards=[memory.Flags.NORTHERN_RUINS_REPAIRS_COMPLETE]
        )
    )

    northern_ruins_600 = LocRegion(
        "northern_ruins_600",
        loc_exits={LocExit.NORTHERN_RUINS_600},
        reward_spots={TID.NORTHERN_RUINS_BASEMENT_600},
        region_loc_ids={LocID.NORTHERN_RUINS_BASEMENT, LocID.NORTHERN_RUINS_ENTRANCE},
        is_combat_region=True
    )
    ret_list.append(northern_ruins_600)
    ret_list.append(
        LocRegion(
            "northern_ruins_600_repaired",
            reward_spots={TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600},
            region_loc_ids={LocID.NORTHERN_RUINS_ANTECHAMBER, LocID.NORTHERN_RUINS_VESTIBULE,
                            LocID.NORTHERN_RUINS_BACK_ROOM, LocID.NORTHERN_RUINS_LANDING},
            is_combat_region=True
        )
    )

    northern_ruins_600_sealed = LocRegion(
        "northern_ruins_600_sealed",
        reward_spots={TID.NORTHERN_RUINS_BACK_LEFT_SEALED_600,
                      TID.NORTHERN_RUINS_BACK_RIGHT_SEALED_600,
                      TID.NORTHERN_RUINS_ANTECHAMBER_SEALED_600}
    )
    ret_list.append(northern_ruins_600_sealed)

    giants_claw = LocRegion(
        "giants_claw",
        loc_exits={LocExit.GIANTS_CLAW},
        reward_spots={
            TID.GIANTS_CLAW_TRAPS, TID.GIANTS_CLAW_CAVES_1, TID.GIANTS_CLAW_CAVES_2,
            TID.GIANTS_CLAW_CAVES_3, TID.GIANTS_CLAW_CAVES_4, TID.GIANTS_CLAW_CAVES_5,
            TID.GIANTS_CLAW_ROCK, TID.GIANTS_CLAW_KEY,
            TID.GIANTS_CLAW_TRAPS_POWER_TAB, TID.GIANTS_CLAW_ENTRANCE_POWER_TAB,
            TID.GIANTS_CLAW_CAVERNS_POWER_TAB,
            BSID.GIANTS_CLAW
        },
        region_loc_ids={LocID.GIANTS_CLAW_ENTRANCE, LocID.GIANTS_CLAW_CAVERNS,
                        LocID.GIANTS_CLAW_LAIR_ENTRANCE, LocID.GIANTS_CLAW_LAIR_THRONEROOM,
                        LocID.GIANTS_CLAW_TYRANO, LocID.ANCIENT_TYRANO_LAIR,
                        LocID.ANCIENT_TYRANO_LAIR_VERTIGO, LocID.ANCIENT_TYRANO_LAIR_VERTIGO,
                        LocID.ANCIENT_TYRANO_LAIR_NIZBELS_ROOM},
        region_rewards=[QuestID.GIANTS_CLAW],
        is_combat_region=True

    )
    ret_list.append(giants_claw)

    shared_tyrano_claw = LocRegion(
        "shared_tyrano_claw",
        reward_spots={TID.TYRANO_LAIR_KINO_CELL, TID.TYRANO_LAIR_TRAPDOOR,
                      TID.TYRANO_LAIR_THRONE_1, TID.TYRANO_LAIR_THRONE_2}
    )
    ret_list.append(shared_tyrano_claw)

    ozzies_fort = LocRegion(
        "ozzies_fort",
        loc_exits={LocExit.OZZIES_FORT},
        reward_spots={
            TID.OZZIES_FORT_GUILLOTINES_1, TID.OZZIES_FORT_GUILLOTINES_2,
            TID.OZZIES_FORT_GUILLOTINES_3, TID.OZZIES_FORT_GUILLOTINES_4,
            TID.OZZIES_FORT_FINAL_1, TID.OZZIES_FORT_FINAL_2,
            TID.OZZIES_FORT_GUILLOTINES_TAB,
            BSID.OZZIES_FORT_FLEA_PLUS, BSID.OZZIES_FORT_SUPER_SLASH,
            BSID.OZZIES_FORT_TRIO,
        },
        region_loc_ids={LocID.OZZIES_FORT_ENTRANCE, LocID.OZZIES_FORT_LAST_STAND,
                        LocID.OZZIES_FORT_GUILLOTINE, LocID.OZZIES_FORT_THRONE_INCOMPETENCE,
                        LocID.OZZIES_FORT_HALL_DISREGARD, LocID.OZZIES_FORT_FLEA_PLUS,
                        LocID.OZZIES_FORT_SUPER_SLASH},
        region_rewards=[QuestID.OZZIES_FORT],
        is_combat_region=True
    )
    ret_list.append(ozzies_fort)

    magus_castle = LocRegion(
        "magus_castle",
        loc_exits={LocExit.MAGUS_LAIR},
        reward_spots={
            TID.MAGUS_CASTLE_RIGHT_HALL,
            TID.MAGUS_CASTLE_GUILLOTINE_1, TID.MAGUS_CASTLE_GUILLOTINE_2,
            TID.MAGUS_CASTLE_SLASH_ROOM_1, TID.MAGUS_CASTLE_SLASH_ROOM_2,
            TID.MAGUS_CASTLE_SLASH_SWORD_FLOOR,
            TID.MAGUS_CASTLE_STATUE_HALL, TID.MAGUS_CASTLE_FOUR_KIDS,
            TID.MAGUS_CASTLE_OZZIE_1, TID.MAGUS_CASTLE_OZZIE_2,
            TID.MAGUS_CASTLE_ENEMY_ELEVATOR, TID.MAGUS_CASTLE_LEFT_HALL,
            TID.MAGUS_CASTLE_UNSKIPPABLES, TID.MAGUS_CASTLE_PIT_E,
            TID.MAGUS_CASTLE_PIT_NE, TID.MAGUS_CASTLE_PIT_NW,
            TID.MAGUS_CASTLE_PIT_W,
            TID.MAGUS_CASTLE_FLEA_MAGIC_TAB, TID.MAGUS_CASTLE_DUNGEONS_MAGIC_TAB,
            BSID.MAGUS_CASTLE_FLEA, BSID.MAGUS_CASTLE_SLASH
        },
        region_rewards=[memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
                        QuestID.MAGUS_CASTLE],
        region_loc_ids={LocID.MAGUS_CASTLE_OZZIE, LocID.MAGUS_CASTLE_PITS,
                        LocID.MAGUS_CASTLE_ENTRANCE,
                        LocID.MAGIC_CAVE_EXTERIOR, LocID.MAGIC_CAVE_EXTERIOR_OPEN,
                        LocID.MAGUS_CASTLE_GUILLOTINES, LocID.MAGUS_CASTLE_DUNGEON,
                        LocID.MAGUS_CASTLE_HALL_DECEIT, LocID.MAGUS_CASTLE_HALL_AGGRESSION,
                        LocID.MAGUS_CASTLE_INNER_SANCTUM, LocID.MAGUS_CASTLE_GRAND_STAIRWAY,
                        LocID.MAGUS_CASTLE_HALL_APPREHENSION, LocID.MAGUS_CASTLE_HALL_OF_AMBUSH,
                        LocID.MAGUS_CASTLE_LOWER_BATTLEMENTS, LocID.MAGUS_CASTLE_FLEA,
                        LocID.MAGUS_CASTLE_SLASH, LocID.MAGUS_CASTLE_CORRIDOR_OF_COMBAT,
                        LocID.MAGUS_CASTLE_PITS, LocID.MAGUS_CASTLE_OZZIE},
        is_combat_region=True
    )
    ret_list.append(magus_castle)

    magic_cave = LocRegion(
        "magic_cave",
        loc_exits={LocExit.MAGIC_CAVE_MAGUS},
        region_loc_ids={LocID.MAGIC_CAVE_INTERIOR},
        is_combat_region=True
    )
    ret_list.append(magic_cave)

    magic_cave = LocRegion(
        "magic_cave_sealed",
        reward_spots={TID.MAGIC_CAVE_SEALED}
    )
    ret_list.append(magic_cave)

    magic_cave_entrance = LocRegion(
        "magic_cave_entrance",
        loc_exits={LocExit.MAGIC_CAVE_OPEN}
    )
    ret_list.append(magic_cave_entrance)
    ret_list.append(
        LocRegion("magic_cave_closed", {LocExit.MAGIC_CAVE_CLOSED})
    )

    sunken_desert = LocRegion(
        "sunken_desert",
        loc_exits={LocExit.SUNKEN_DESERT_INTERIOR, LocExit.SUNKEN_DESERT_ENTRANCE},
        reward_spots={
            TID.SUNKEN_DESERT_B1_NE, TID.SUNKEN_DESERT_B1_SE,
            TID.SUNKEN_DESERT_B1_NW, TID.SUNKEN_DESERT_B1_SW,
            TID.SUNKEN_DESERT_B2_N, TID.SUNKEN_DESERT_B2_NW,
            TID.SUNKEN_DESERT_B2_W, TID.SUNKEN_DESERT_B2_SW,
            TID.SUNKEN_DESERT_B2_SE, TID.SUNKEN_DESERT_B2_E,
            TID.SUNKEN_DESERT_B2_CENTER, TID.SUNKEN_DESERT_POWER_TAB,
            BSID.SUNKEN_DESERT
        },
        region_rewards=[memory.Flags.SUNKEN_DESERT_BOSS_DEFEATED],
        region_loc_ids={LocID.SUNKEN_DESERT_DEVOURER, LocID.SUNKEN_DESERT_PARASITES,
                        LocID.SUNKEN_DESERT_ENTRANCE},
        is_combat_region=True
    )
    ret_list.append(sunken_desert)

    fiona_shrine = LocRegion(
        "fiona_shrine",
        loc_exits={LocExit.FIONAS_SHRINE},
        reward_spots={ShopID.FIONAS_SHRINE},
        region_loc_ids={LocID.FIONAS_SHRINE}
    )
    ret_list.append(fiona_shrine)

    fiona_campfire = LocRegion(
        "fiona_campfire",
        reward_spots={TID.FIONA_KEY},
        region_loc_ids={LocID.FIONA_FOREST, LocID.FIONA_FOREST_CAMPFIRE},
        region_rewards=[QuestID.SUNKEN_DESERT]
    )
    ret_list.append(fiona_campfire)

    ret_list.append(
        LocRegion(
            "sun_keep_2300",
            loc_exits={LocExit.SUN_KEEP_2300},
            region_loc_ids={LocID.SUN_KEEP_2300}
        )
    )
    ret_list.append(
        LocRegion(
            "sun_keep_1000",
            loc_exits={LocExit.SUN_KEEP_1000},
            region_loc_ids={LocID.SUN_KEEP_1000}
        )
    )

    ret_list.append(
        LocRegion(
            "sun_keep_prehistory",
            loc_exits={LocExit.SUN_KEEP_PREHISTORY},
            region_loc_ids={LocID.SUN_KEEP_65MBC}
        )
    )
    ret_list.append(
        LocRegion(
            "sun_keep_prehistory_charge",
            region_rewards=[memory.Flags.MOONSTONE_PLACED_PREHISTORY]
        )
    )

    moonstone_quest = LocRegion(
        "moonstone_quest",
        reward_spots={TID.SUN_KEEP_2300, TID.LUCCA_WONDERSHOT, TID.TABAN_SUNSHADES},
        region_rewards=[QuestID.CHARGE_MOONSTONE]
    )
    ret_list.append(moonstone_quest)

    sun_palace = LocRegion(
        "sun_palace",
        loc_exits={LocExit.SUN_PALACE},
        reward_spots={TID.SUN_PALACE_KEY, BSID.SUN_PALACE},
        region_loc_ids={LocID.SUN_PALACE},
        region_rewards=[QuestID.SUN_PALACE],
        is_combat_region=True
    )
    ret_list.append(sun_palace)

    end_of_time = LocRegion(
        "end_of_time",
        region_rewards=[memory.Flags.PROTO_DOME_DOOR_UNLOCKED,
                        memory.Flags.HAS_EOT_TIMEGAUGE_ACCESS,
                        QuestID.SPEKKIO],
        region_loc_ids={LocID.END_OF_TIME, LocID.SPEKKIO},
    )
    ret_list.append(end_of_time)

    end_of_time_gaspar = LocRegion(
        "end_of_time_gaspar",
        reward_spots={TID.EOT_GASPAR_REWARD}
    )
    ret_list.append(end_of_time_gaspar)

    geno_dome = LocRegion(
        "geno_dome",
        loc_exits={LocExit.GENO_DOME},
        region_loc_ids={LocID.GENO_DOME_ENTRANCE}
    )
    geno_dome_inside = LocRegion(
        "geno_dome_inside",
        reward_spots={
            TID.GENO_DOME_1F_1, TID.GENO_DOME_1F_2, TID.GENO_DOME_1F_3,
            TID.GENO_DOME_1F_4, TID.GENO_DOME_ROOM_1, TID.GENO_DOME_ROOM_2,
            TID.GENO_DOME_PROTO4_1, TID.GENO_DOME_PROTO4_2,
            TID.GENO_DOME_2F_1, TID.GENO_DOME_2F_2, TID.GENO_DOME_2F_3,
            TID.GENO_DOME_2F_4,
            TID.GENO_DOME_BOSS_1, TID.GENO_DOME_BOSS_2,
            TID.GENO_DOME_LABS_MAGIC_TAB, TID.GENO_DOME_LABS_SPEED_TAB,
            TID.GENO_DOME_CORRIDOR_POWER_TAB, TID.GENO_DOME_ATROPOS_MAGIC_TAB,
            BSID.GENO_DOME_FINAL,
            BSID.GENO_DOME_MID,
        },
        region_loc_ids={LocID.GENO_DOME_LABS, LocID.GENO_DOME_STORAGE,
                        LocID.GENO_DOME_ROBOT_HUB, LocID.GENO_DOME_ROBOT_ELEVATOR_ACCESS,
                        LocID.GENO_DOME_ROBOT_ELEVATOR_ACCESS, LocID.GENO_DOME_WASTE_DISPOSAL,
                        LocID.GENO_DOME_CONVEYOR, LocID.GENO_DOME_CONVEYOR_EXIT,
                        LocID.GENO_DOME_MAINFRAME, LocID.GENO_DOME_ENTRANCE,
                        LocID.GENO_DOME_CONVEYOR_ENTRANCE},
        region_rewards=[QuestID.GENO_DOME],
        is_combat_region=True
    )
    ret_list.append(geno_dome)
    ret_list.append(geno_dome_inside)

    ret_list.append(
        LocRegion(
            "forest_maze_north",
            {LocExit.FOREST_MAZE_NORTH},
        )
    )
    forest_maze = LocRegion(
        "forest_maze",
        loc_exits={LocExit.FOREST_MAZE_SOUTH},
        reward_spots={
            TID.FOREST_MAZE_1, TID.FOREST_MAZE_2, TID.FOREST_MAZE_3,
            TID.FOREST_MAZE_4, TID.FOREST_MAZE_5, TID.FOREST_MAZE_6,
            TID.FOREST_MAZE_7, TID.FOREST_MAZE_8, TID.FOREST_MAZE_9,
        },
        region_loc_ids={LocID.FOREST_MAZE},
        is_combat_region=True
    )
    ret_list.append(forest_maze)

    reptite_lair = LocRegion(
        "reptite_lair",
        loc_exits={LocExit.REPTITE_LAIR},
        reward_spots={
            TID.REPTITE_LAIR_REPTITES_1, TID.REPTITE_LAIR_REPTITES_2,
            TID.REPTITE_LAIR_SECRET_B1_NE, TID.REPTITE_LAIR_SECRET_B1_SE,
            TID.REPTITE_LAIR_SECRET_B1_SW, TID.REPTITE_LAIR_SECRET_B2_NE_OR_SE_LEFT,
            TID.REPTITE_LAIR_SECRET_B2_SW, TID.REPTITE_LAIR_SECRET_B2_NE_RIGHT,
            TID.REPTITE_LAIR_SECRET_B2_SE_RIGHT, TID.REPTITE_LAIR_KEY,
            BSID.REPTITE_LAIR
        },
        region_loc_ids={LocID.REPTITE_LAIR_ENTRANCE,
                        LocID.REPTITE_LAIR_TUNNEL, LocID.REPTITE_LAIR_COMMONS,
                        LocID.REPTITE_LAIR_2F, LocID.REPTITE_LAIR_1F,
                        LocID.REPTITE_LAIR_WEEVIL_BURROWS_B1, LocID.REPTITE_LAIR_WEEVIL_BURROWS_B2,
                        LocID.REPTITE_LAIR_AZALA_ROOM, LocID.REPTITE_LAIR_ACCESS_SHAFT,},
        region_rewards=[QuestID.REPTITE_LAIR],
        is_combat_region=True
    )
    ret_list.append(reptite_lair)

    tyrano_lair_entrance = LocRegion(
        "tyrano_lair_entrance",
        loc_exits={LocExit.TYRANO_LAIR},
        region_loc_ids={LocID.TYRANO_LAIR_ENTRANCE, LocID.TYRANO_LAIR_MAIN_CELL,
                        LocID.TYRANO_LAIR_ANTECHAMBERS},
        is_combat_region=True
    )
    ret_list.append(tyrano_lair_entrance)

    tyrano_lair = LocRegion(
        "tyrano_lair",
        reward_spots={
            TID.TYRANO_LAIR_MAZE_1, TID.TYRANO_LAIR_MAZE_2,
            TID.TYRANO_LAIR_MAZE_3, TID.TYRANO_LAIR_MAZE_4,
            BSID.TYRANO_LAIR_NIZBEL
        },
        region_rewards=[memory.Flags.OW_LAVOS_HAS_FALLEN,
                        QuestID.TYRANO_LAIR],
        region_loc_ids={LocID.TYRANO_LAIR_KEEP, LocID.TYRANO_LAIR_THRONEROOM,
                        LocID.TYRANO_LAIR_EXTERIOR, LocID.TYRANO_LAIR_ROOM_OF_VERTIGO,
                        LocID.TYRANO_LAIR_STORAGE, LocID.TYRANO_LAIR_NIZBEL},
        is_combat_region=True
    )
    ret_list.append(tyrano_lair)

    black_omen = LocRegion(
        "black_omen",
        # loc_exits={???},
        reward_spots={
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
            BSID.BLACK_OMEN_MEGA_MUTANT, BSID.BLACK_OMEN_GIGA_MUTANT,
            BSID.BLACK_OMEN_TERRA_MUTANT, BSID.BLACK_OMEN_ELDER_SPAWN
        },
        region_loc_ids={
            LocID.BLACK_OMEN_ENTRANCE,
            LocID.BLACK_OMEN_1F_ENTRANCE, LocID.BLACK_OMEN_1F_WALKWAY,
            LocID.BLACK_OMEN_1F_DEFENSE_CORRIDOR, LocID.BLACK_OMEN_1F_STAIRWAY,
            LocID.BLACK_OMEN_3F_WALKWAY, LocID.BLACK_OMEN_47F_AUX_COMMAND,
            LocID.BLACK_OMEN_47F_GRAND_HALL, LocID.BLACK_OMEN_47F_ROYAL_PATH,
            LocID.BLACK_OMEN_47F_ROYAL_BALLROOM, LocID.BLACK_OMEN_47F_ROYAL_ASSEMBLY,
            LocID.BLACK_OMEN_47F_ROYAL_PROMENADE, LocID.BLACK_OMEN_63F_DIVINE_ESPLENADE,
            LocID.BLACK_OMEN_97F_ASTRAL_WALKWAY, LocID.BLACK_OMEN_98F_OMEGA_DEFENSE,
            LocID.BLACK_OMEN_ELEVATOR_UP, LocID.BLACK_OMEN_ELEVATOR_DOWN,
            LocID.BLACK_OMEN_GIGA_MUTANT, LocID.BLACK_OMEN_TERRA_MUTANT,
            LocID.BLACK_OMEN_ELDER_SPAWN
        },
        region_rewards=[
            QuestID.OMEN_ELDER_SPAWN, QuestID.OMEN_TERRA_MUTANT, QuestID.OMEN_GIGA_MUTANT,
            QuestID.OMEN_MEGA_MUTANT
        ],
        is_combat_region=True
    )
    ret_list.append(black_omen)

    last_village_north_cape = LocRegion(
        "last_village_north_cape",
        loc_exits={LocExit.NORTH_CAPE},
        reward_spots={RecruitID.NORTH_CAPE},
        region_loc_ids={LocID.NORTH_CAPE},
        is_combat_region=True,
    )
    ret_list.append(last_village_north_cape)

    last_village_shop = LocRegion(
        "last_village_shop",
        loc_exits={LocExit.LAST_VILLAGE_SHOP},
        reward_spots={ShopID.LAST_VILLAGE_UPDATED, TID.LAST_VILLAGE_NU_SHOP_MAGIC_TAB}
    )
    ret_list.append(last_village_shop)

    last_village_commons = LocRegion(
        "last_village_commons",
        loc_exits={LocExit.LAST_VILLAGE_COMMNONS}
    )
    ret_list.append(last_village_commons)

    blackbird_scaffolding = LocRegion(
        "blackbird_scaffolding",
        loc_exits={LocExit.BLACKBIRD}
    )
    blackbird_scaffolding_epoch = LocRegion(
        "epoch_reborn",
        reward_spots={BSID.EPOCH_REBORN},
        region_rewards=[logictypes.ScriptReward.FLIGHT,
                        logictypes.ScriptReward.EPOCH,
                        memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS,
                        QuestID.EPOCH_REBORN_BATTLE],
        region_loc_ids={LocID.REBORN_EPOCH},
        is_combat_region=True
    )
    ret_list.extend([blackbird_scaffolding, blackbird_scaffolding_epoch])

    blackbird = LocRegion(
        "blackbird",
        reward_spots={TID.BLACKBIRD_DUCTS_MAGIC_TAB, BSID.BLACKBIRD_LEFT_WING},
        region_loc_ids={
            LocID.BLACKBIRD_LEFT_WING, LocID.BLACKBIRD_HANGAR,
            LocID.BLACKBIRD_REAR_HALLS, LocID.BLACKBIRD_FORWARD_HALLS,
            LocID.BLACKBIRD_TREASURY, LocID.BLACKBIRD_CELL,
            LocID.BLACKBIRD_BARRACKS, LocID.BLACKBIRD_ARMORY_3,
            LocID.BLACKBIRD_INVENTORY, LocID.BLACKBIRD_LOUNGE,
            LocID.BLACKBIRD_ACCESS_SHAFT, LocID.BLACKBIRD_ARMORY_2,
            LocID.BLACKBIRD_ARMORY_1,
        },
        region_rewards=[QuestID.BLACKBIRD],
        is_combat_region=True
    )
    ret_list.append(blackbird)

    zeal_palace = LocRegion(
        "zeal_palace",
        loc_exits={LocExit.ZEAL_PALACE},
        region_rewards=[memory.Flags.PLANT_LADY_SAVES_SEED,
                        memory.Flags.DISCOVERED_NU_SCRATCH_POINT]
    )
    ret_list.append(zeal_palace)

    zeal_mammon_m =  LocRegion(
        "zeal_mammon_m",
        reward_spots={TID.ZEAL_MAMMON_MACHINE}
    )
    ret_list.append(zeal_mammon_m)

    enhasa = LocRegion(
        "enhasa",
        loc_exits={LocExit.ENHASA},
        reward_spots={TID.ENHASA_NU_BATTLE_MAGIC_TAB, TID.ENHASA_NU_BATTLE_SPEED_TAB,
                      ShopID.ENHASA},
        region_loc_ids={LocID.ENHASA, LocID.ENHASA_NU_ROOM},
        is_combat_region=True
    )
    ret_list.append(enhasa)

    kajar = LocRegion(
        "kajar",
        loc_exits={LocExit.KAJAR},
        reward_spots={TID.KAJAR_ROCK, TID.KAJAR_SPEED_TAB, ShopID.NU_NORMAL_KAJAR},
    )
    ret_list.append(kajar)

    kajar_nu_scratch = LocRegion(
        "kajar_nu_scratch",
        reward_spots={TID.KAJAR_NU_SCRATCH_MAGIC_TAB}
    )
    ret_list.append(kajar_nu_scratch)

    ocean_palace = LocRegion(
        "ocean_palace",
        reward_spots={
            TID.OCEAN_PALACE_MAIN_S, TID.OCEAN_PALACE_MAIN_N,
            TID.OCEAN_PALACE_E_ROOM, TID.OCEAN_PALACE_W_ROOM,
            TID.OCEAN_PALACE_SWITCH_NW, TID.OCEAN_PALACE_SWITCH_SW,
            TID.OCEAN_PALACE_SWITCH_NE, TID.OCEAN_PALACE_SWITCH_SECRET,
            TID.OCEAN_PALACE_ELEVATOR_MAGIC_TAB,
            TID.OCEAN_PALACE_FINAL,
            BSID.ZEAL_PALACE,
            BSID.OCEAN_PALACE_TWIN_GOLEM, BSID.OCEAN_PALACE_TWIN_GOLEM_ALT
        },
        region_loc_ids={
            LocID.ZEAL_PALACE_THRONE, LocID.ZEAL_PALACE_THRONE_NIGHT,
            LocID.OCEAN_PALACE_PIAZZA, LocID.OCEAN_PALACE_SIDE_ROOMS,
            LocID.OCEAN_PALACE_FORWARD_AREA, LocID.OCEAN_PALACE_B3_LANDING,
            LocID.OCEAN_PALACE_GRAND_STAIRWELL,  # Remove masa
            LocID.OCEAN_PALACE_ELEVATOR_BATTLES,
            LocID.OCEAN_PALACE_B20_LANDING, LocID.OCEAN_PALACE_SOUTHERN_ACCESS_LIFT,
            LocID.OCEAN_PALACE_REGAL_ANTECHAMBER,
        },
        region_rewards=[QuestID.ZEAL_PALACE_THRONE],
        is_combat_region=True
    )
    ret_list.append(ocean_palace)

    ocean_palace_mammon_m = LocRegion(
        "ocean_palace_mammon_m",
        region_rewards=[memory.Flags.HAS_ALGETTY_PORTAL, QuestID.OCEAN_PALACE]
    )
    ret_list.append(ocean_palace_mammon_m)

    algetty = LocRegion(
        "algetty",
        loc_exits={LocExit.TERRA_CAVE},
        reward_spots={ShopID.EARTHBOUND_VILLAGE}
    )
    ret_list.append(algetty)

    mt_woe = LocRegion(
        "mt_woe",
        reward_spots={
            TID.BEAST_NEST_POWER_TAB,
            TID.MT_WOE_2ND_SCREEN_1, TID.MT_WOE_2ND_SCREEN_2,
            TID.MT_WOE_2ND_SCREEN_3, TID.MT_WOE_2ND_SCREEN_4,
            TID.MT_WOE_2ND_SCREEN_5, TID.MT_WOE_3RD_SCREEN_1,
            TID.MT_WOE_3RD_SCREEN_2, TID.MT_WOE_3RD_SCREEN_3,
            TID.MT_WOE_3RD_SCREEN_4, TID.MT_WOE_3RD_SCREEN_5,
            TID.MT_WOE_1ST_SCREEN, TID.MT_WOE_FINAL_1,
            TID.MT_WOE_FINAL_2,
            TID.MT_WOE_MAGIC_TAB,
            TID.MT_WOE_KEY,
            BSID.BEAST_CAVE, BSID.MT_WOE
        },
        region_loc_ids={
            LocID.BEAST_NEST,
            LocID.MT_WOE_SUMMIT, LocID.MT_WOE_WESTERN_FACE,
            LocID.MT_WOE_LOWER_EASTERN_FACE, LocID.MT_WOE_UPPER_EASTERN_FACE,
            LocID.MT_WOE_WESTERN_FACE, LocID.MT_WOE_MIDDLE_EASTERN_FACE,
        },
        region_rewards=[QuestID.MT_WOE, QuestID.BEAST_CAVE],
        is_combat_region=True
    )
    ret_list.append(mt_woe)
    ret_list.append(LocRegion("truce_single_residence", {LocExit.TRUCE_SINGLE_RESIDENCE}))
    ret_list.append(LocRegion("truce_screaming_residence", {LocExit.TRUCE_SCREAMING_RESIDENCE}))
    ret_list.append(LocRegion("porre_residence_1000", {LocExit.PORRE_RESIDENCE_1000}))
    ret_list.append(LocRegion("truce_smith_residence_600", {LocExit.TRUCE_SMITH_RESIDENCE}))
    ret_list.append(LocRegion("truce_couple_residence_600", {LocExit.TRUCE_COUPLE_RESIDENCE_600}))
    ret_list.append(LocRegion("dark_ages_portal", {LocExit.DARK_AGES_PORTAL_DEFAULT}))
    ret_list.append(LocRegion("skyway_enhasa_south", {LocExit.SKYWAY_ENHASA_SOUTH}))
    ret_list.append(LocRegion("land_bridge_enhasa_south", {LocExit.LAND_BRIDGE_ENHASA_SOUTH}))
    ret_list.append(LocRegion("skyway_enhasa_north", {LocExit.SKYWAY_ENHASA_NORTH}))
    ret_list.append(LocRegion("land_bridge_enhasa_north", {LocExit.LAND_BRIDGE_ENHASA_NORTH}))
    ret_list.append(LocRegion("skyway_kajar", {LocExit.SKYWAY_KAJAR}))
    ret_list.append(LocRegion("land_bridge_kajar", {LocExit.LAND_BRIDGE_KAJAR}))
    ret_list.append(LocRegion("zeal_teleporter_bottom", {LocExit.ZEAL_TELEPORTER_BOTTOM}))
    ret_list.append(LocRegion("zeal_teleporter_top", {LocExit.ZEAL_TELEPORTER_TOP}))
    ret_list.append(LocRegion("last_village_residence", {LocExit.LAST_VILLAGE_RESIDENCE}))
    ret_list.append(LocRegion("last_village_empty_hut", {LocExit.LAST_VILLAGE_EMPTY_HUT}))
    ret_list.append(LocRegion("sun_keep_last_village", {LocExit.SUN_KEEP_LAST_VILLAGE}))

    return ret_list

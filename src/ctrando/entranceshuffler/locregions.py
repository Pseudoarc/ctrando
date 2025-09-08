"""Keep a map of the whole game"""
import typing

from ctrando.common.ctenums import RecruitID, TreasureID as TID, ShopID, LocID
from ctrando.common import memory
from ctrando.bosses.bosstypes import BossSpotID as BSID

from ctrando.locations.locexitdata import LocOWExits as LocExit
from ctrando.logic import logictypes


class LocRegion:
    def __init__(
            self,
            name: str,
            loc_exits: set[LocExit] | None = None,
            reward_spots: set[typing.Any] | None = None,
            region_rewards: list[typing.Any] | None = None,
            region_loc_ids: set[LocID] | None = None
    ):
        self.name = name
        self.loc_exits = set() if loc_exits is None else set(loc_exits)
        self.reward_spots = set() if reward_spots is None else set(reward_spots)
        self.region_rewards = [] if region_rewards is None else list(region_rewards)
        self.region_loc_ids = set() if region_loc_ids is None else set(region_loc_ids)


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
        region_loc_ids={LocID.CRONOS_KITCHEN, LocID.CRONOS_ROOM}
    )
    ret_list.append(cronos_house)
    ret_list.append(
        LocRegion(
            "cronos_house_mom",
            reward_spots={TID.CRONOS_MOM}
        )
    )
    cronos_house_clone = LocRegion(
        "cronos_house_clone",
        reward_spots={TID.BEKKLER_KEY}
    )
    ret_list.append(cronos_house_clone)

    truce_mayor_1000 = LocRegion(
        "truce_mayor_1000",
        loc_exits={LocExit.TRUCE_MAYOR},
        reward_spots={TID.TRUCE_MAYOR_1F, TID.TRUCE_MAYOR_2F, TID.TRUCE_MAYOR_2F_OLD_MAN},
    )
    ret_list.append(truce_mayor_1000)

    truce_market_1000 = LocRegion(
        "truce_market_1000",
        loc_exits={LocExit.TRUCE_MARKET_1000},
        reward_spots={ShopID.TRUCE_MARKET_1000}
    )
    ret_list.append(truce_market_1000)

    truce_inn_1000 = LocRegion(
        "truce_inn_1000",
        loc_exits={LocExit.TRUCE_INN_1000},
        region_loc_ids={LocID.TRUCE_INN_1000}
    )
    ret_list.append(truce_inn_1000)

    truce_inn_1000_sealed = LocRegion(
        "truce_inn_1000_sealed",
        reward_spots={TID.TRUCE_INN_SEALED_1000}
    )
    ret_list.append(truce_inn_1000_sealed)

    ret_list.append(
        LocRegion("truce_ticket_office", {LocExit.TRUCE_TICKET_OFFICE})
    )
    ret_list.append(
        LocRegion("porre_ticket_office", {LocExit.PORRE_TICKET_OFFICE})
    )
    ret_list.append(
        LocRegion("zenan_bridge_1000",
                  {LocExit.ZENAN_BRIDGE_1000_NORTH, LocExit.ZENAN_BRIDGE_1000_SOUTH})
    )
    ret_list.append(LocRegion("porre_inn_1000", {LocExit.PORRE_INN_1000}))

    guardia_castle_1000 = LocRegion(
        "guardia_castle_1000",
        loc_exits={LocExit.GUARDIA_CASTLE_1000},
        reward_spots={TID.QUEENS_TOWER_1000, TID.QUEENS_ROOM_1000, TID.KINGS_TOWER_1000,
                      TID.KINGS_ROOM_1000, TID.GUARDIA_COURT_TOWER},
    )
    ret_list.append(guardia_castle_1000)

    guardia_castle_1000_sealed = LocRegion(
        "guardia_castle_1000_sealed",
        reward_spots={TID.GUARDIA_CASTLE_SEALED_1000},
    )
    ret_list.append(guardia_castle_1000_sealed)

    porre_mayor_1000 = LocRegion(
        "porre_mayor_1000",
        loc_exits={LocExit.PORRE_MAYOR_1000},
        reward_spots={TID.PORRE_MAYOR_2F}
    )
    ret_list.append(porre_mayor_1000)

    ret_list.append(
        LocRegion(
            "porre_mayor_1000_sealed",
            reward_spots={TID.PORRE_MAYOR_SEALED_1, TID.PORRE_MAYOR_SEALED_2}
        )
    )
    ret_list.append(
        LocRegion(
            "porre_market_1000", {LocExit.PORRE_MARKET_1000},
            region_rewards=[ShopID.PORRE_1000]
        )
    )

    snail_stop = LocRegion(
        "snail_stop",
        loc_exits={LocExit.SNAIL_STOP},
        reward_spots={TID.SNAIL_STOP_KEY}
    )
    ret_list.append(snail_stop)

    millennial_fair = LocRegion(
        "millennial_fair",
        loc_exits={LocExit.MILLENNIAL_FAIR},
        reward_spots={BSID.MILLENNIAL_FAIR_GATO, TID.FAIR_PENDANT},
        region_rewards=[memory.Flags.HAS_TRUCE_PORTAL]
    )
    ret_list.append(millennial_fair)

    millennial_fair_recruit = LocRegion(
        "millennial_fair_recruit",
        reward_spots={RecruitID.MILLENNIAL_FAIR}
    )
    ret_list.append(millennial_fair_recruit)

    millennial_fair_bekkler = LocRegion(
        "millennial_fair_bekkler",
        region_rewards=[memory.Flags.WON_CRONO_CLONE]
    )
    ret_list.append(millennial_fair_bekkler)

    guardia_forest_1000 = LocRegion(
        "guardia_forest_1000",
        loc_exits={LocExit.GUARDIA_FOREST_NORTH_1000, LocExit.GUARDIA_FOREST_SOUTH_1000},
        reward_spots={TID.GUARDIA_FOREST_POWER_TAB_1000},
        region_rewards=[memory.Flags.HAS_BANGOR_PORTAL],
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
        }
    )
    crono_trial_boss = LocRegion(
        "crono_trial_boss",
        loc_exits=set(),
        reward_spots={BSID.PRISON_CATWALKS}
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
        region_rewards=[memory.Flags.HECKRAN_DEFEATED]
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
            region_rewards=[ShopID.MEDINA_MARKET]
        )
    )
    ret_list.append(LocRegion("medina_inn", {LocExit.MEDINA_INN}))
    ret_list.append(LocRegion("medina_square", {LocExit.MEDINA_SQUARE}))

    medina_elder = LocRegion(
        "medina_elder",
        loc_exits={LocExit.MEDINA_ELDER},
        reward_spots={TID.MEDINA_ELDER_MAGIC_TAB, TID.MEDINA_ELDER_SPEED_TAB}
    )
    ret_list.append(medina_elder)

    forest_ruins = LocRegion(
        "forest_ruins",
        loc_exits={LocExit.FOREST_RUINS},
        reward_spots={TID.FOREST_RUINS},
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
        reward_spots=set()
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
        region_rewards=[memory.Flags.HAS_TRUCE_PORTAL]
    )
    ret_list.append(truce_canyon)

    guardia_castle_600 = LocRegion(
        "guardia_castle_600",
        loc_exits={LocExit.GUARDIA_CASTLE_600},
        reward_spots={TID.ROYAL_KITCHEN, TID.ZENAN_BRIDGE_CHEF, TID.ZENAN_BRIDGE_CHEF_TAB,
                      TID.QUEENS_ROOM_600, TID.QUEENS_TOWER_600, TID.KINGS_TOWER_600,
                      TID.KINGS_ROOM_600}
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
        reward_spots={TID.GUARDIA_FOREST_POWER_TAB_600}
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
                        memory.Flags.OBTAINED_NAGAETTE_BROMIDE]
    )
    ret_list.extend([manoria_front, manoria_cathedral])

    ret_list.append(
        LocRegion(
            "truce_market_600",
            loc_exits={LocExit.TRUCE_MARKET_600},
            reward_spots={ShopID.TRUCE_MARKET_600}
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
        region_rewards=[memory.Flags.TATA_SCENE_COMPLETE]
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
            region_rewards=[ShopID.DORINO]
        )
    )
    ret_list.append(LocRegion("dorino_inn", {LocExit.DORINO_INN}))

    fionas_villa = LocRegion(
        "fionas_villa",
        loc_exits={LocExit.FIONAS_VILLA},
        reward_spots={TID.FIONAS_HOUSE_1, TID.FIONAS_HOUSE_2}
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
                      TID.FROGS_BURROW_RIGHT}
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
        reward_spots={TID.PORRE_MARKET_600_POWER_TAB}
    )
    ret_list.append(porre_market)
    ret_list.append(LocRegion("porre_cafe_600", {LocExit.PORRE_CAFE_600}))
    ret_list.append(LocRegion("porre_inn_600", {LocExit.PORRE_INN_600}))

    lab_16 = LocRegion(
        "lab_16",
        loc_exits={LocExit.LAB_16_EAST, LocExit.LAB_16_WEST},
        reward_spots={TID.LAB_16_1, TID.LAB_16_2, TID.LAB_16_3, TID.LAB_16_4}
    )
    ret_list.append(lab_16)

    lab_32_west = LocRegion(
        "lab_32_west",
        loc_exits={LocExit.LAB_32_WEST},
        reward_spots={TID.LAB_32_1}
    )
    ret_list.append(lab_32_west)

    lab_32_east = LocRegion(
        "lab_32_east",
        loc_exits={LocExit.LAB_32_EAST},
        reward_spots=set()
    )
    ret_list.append(lab_32_east)

    lab_32_middle = LocRegion(
        "lab_32_middle",
        loc_exits=set(),
        reward_spots={TID.LAB_32_RACE_LOG}
    )
    ret_list.append(lab_32_middle)

    sewers = LocRegion(
        "sewers",
        loc_exits={LocExit.SEWER_ACCESS_ARRIS, LocExit.SEWER_ACCESS_KEEPERS},
        reward_spots={TID.SEWERS_1, TID.SEWERS_2, TID.SEWERS_3, BSID.SEWERS_KRAWLIE}
    )
    ret_list.append(sewers)

    death_peak_entrance = LocRegion(
        "death_peak_entrance",
        loc_exits={LocExit.DEATH_PEAK, LocExit.DEATH_PEAK_FALL},
        reward_spots={TID.DEATH_PEAK_POWER_TAB}
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
        }
    )
    ret_list.append(death_peak)

    arris_dome = LocRegion(
        "arris_dome",
        loc_exits={LocExit.ARRIS_DOME},
        reward_spots={
            TID.ARRIS_DOME_FOOD_STORE, TID.ARRIS_DOME_RATS,
            TID.ARRIS_DOME_FOOD_LOCKER_KEY, BSID.ARRIS_DOME
        }
    )
    ret_list.append(arris_dome)

    arris_dome_sealed = LocRegion(
        "arris_dome_sealed",
        reward_spots={TID.ARRIS_DOME_SEAL_1, TID.ARRIS_DOME_SEAL_2,
                      TID.ARRIS_DOME_SEAL_3, TID.ARRIS_DOME_SEAL_4,
                      TID.ARRIS_DOME_SEALED_POWER_TAB}
    )
    ret_list.append(arris_dome_sealed)

    arris_dome_doan = LocRegion(
        "arris_dome_doan",
        reward_spots={TID.ARRIS_DOME_DOAN_KEY}
    )
    ret_list.append(arris_dome_doan)

    proto_dome = LocRegion(
        "proto_dome",
        loc_exits={LocExit.PROTO_DOME},
        reward_spots={RecruitID.PROTO_DOME}
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
        region_rewards=[memory.Flags.FACTORY_POWER_ACTIVATED]
    )
    ret_list.append(factory_ruins)
    ret_list.append(factory_ruins_inside)

    keepers_dome = LocRegion(
        "keepers_dome",
        loc_exits={LocExit.KEEPERS_DOME}
    )
    ret_list.append(keepers_dome)

    keepers_dome_sealed = LocRegion(
        "keepers_dome_sealed",
        reward_spots={TID.KEEPERS_DOME_MAGIC_TAB},
        region_rewards=[memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS,
                        memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
                        logictypes.ScriptReward.EPOCH]
    )
    ret_list.append(keepers_dome_sealed)

    # TODO: Decide how to handle Dactyl warp to prehistory.
    #       Consider putting dactyls on the map but returning to the front's exit
    dactyl_nest = LocRegion(
        "dactyl_nest",
        loc_exits={LocExit.DACTYL_NEST},
        reward_spots={
            TID.DACTYL_NEST_1, TID.DACTYL_NEST_2, TID.DACTYL_NEST_3,
        }
    )
    ret_list.append(dactyl_nest)

    dactyl_nest_recruit = LocRegion(
        "dactyl_nest_recruit",
        reward_spots={RecruitID.DACTYL_NEST},
        region_rewards=[memory.Flags.OBTAINED_DACTYLS]
    )
    ret_list.append(dactyl_nest_recruit)

    mystic_mts = LocRegion(
        "mystic_mts",
        loc_exits={LocExit.MYSTIC_MTS},
        reward_spots={TID.MYSTIC_MT_STREAM}
    )
    ret_list.append(mystic_mts)

    hunting_range = LocRegion(
        "hunting_range",
        loc_exits={LocExit.HUNTING_RANGE},
        reward_spots={TID.HUNTING_RANGE_NU_REWARD}
    )
    ret_list.append(hunting_range)

    laruba_ruins = LocRegion(
        "laruba_ruins",
        loc_exits={LocExit.LARUBA_RUINS},
        reward_spots={TID.LARUBA_ROCK}
    )
    laruba_ruins_chief = LocRegion(
        "laruba_ruins_chief",
        region_rewards=[memory.Flags.OBTAINED_DACTYLS]
    )
    ret_list.extend([laruba_ruins, laruba_ruins_chief])
    ret_list.append(
        LocRegion(
            "ioka_meeting_site", {LocExit.IOKA_MEETING_NORTH, LocExit.IOKA_MEETING_SOUTH}
        )
    )
    ret_list.append(LocRegion("ioka_chief_hut", {LocExit.CHIEFS_HUT}))
    ret_list.append(
        LocRegion(
            "ioka_trading_post", {LocExit.TRADING_POST},
            region_rewards=[ShopID.IOKA_VILLAGE]
        )
    )
    ret_list.append(LocRegion("ioka_sw_hut", {LocExit.IOKA_SW_HUT}))
    ret_list.append(LocRegion("ioka_sweet_water_hut", {LocExit.IOKA_SWEET_WATER_HUT}))
    ret_list.append(
        LocRegion(
        "lair_ruins_portal", {LocExit.LAIR_RUINS},
            region_rewards=[
                memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS,
                memory.Flags.HAS_LAIR_RUINS_PORTAL,
                memory.Flags.HAS_DARK_AGES_PORTAL,
            ]
        )
    )

    ret_list.append(LocRegion("choras_mayor", {LocExit.CHORAS_MAYOR_1000}))
    ret_list.append(LocRegion("choras_inn_1000", {LocExit.CHORAS_INN_1000},
                              region_rewards=[memory.Flags.TALKED_TO_CHORAS_1000_CARPENTER]))
    ret_list.append(
        LocRegion("choras_1000_carpenter_base", {LocExit.CHORAS_CARPTENTER_1000})
    )
    choras_carpenter_wife = LocRegion(
        "choras_1000_carpenter_wife", reward_spots={TID.LAZY_CARPENTER}
    )
    ret_list.append(choras_carpenter_wife)

    choras_west_cape = LocRegion(
        "choras_west_cape",
        loc_exits={LocExit.WEST_CAPE},
        reward_spots={TID.TOMAS_GRAVE_SPEED_TAB},
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
            reward_spots={TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_1000}
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

    cyrus_grave = LocRegion(
        "cyrus_grave_600",
        reward_spots={TID.CYRUS_GRAVE_KEY},
        region_rewards=[memory.Flags.MASAMUNE_UPGRADED]
    )
    ret_list.append(cyrus_grave)

    guardia_castle_treasury = LocRegion(
        "guardia_castle_treasury",
        reward_spots={
            TID.GUARDIA_TREASURY_1, TID.GUARDIA_TREASURY_2, TID.GUARDIA_TREASURY_3,
            TID.GUARDIA_BASEMENT_1, TID.GUARDIA_BASEMENT_2, TID.GUARDIA_BASEMENT_3
        }
    )
    ret_list.append(guardia_castle_treasury)

    guardia_castle_treasury_shell = LocRegion(
        "guardia_castle_rbow_shell",
        reward_spots={TID.KINGS_TRIAL_KEY}
    )
    ret_list.append(guardia_castle_treasury_shell)

    kings_trial_resolution = LocRegion(
        "kings_trial_resolution",
        reward_spots={BSID.KINGS_TRIAL, TID.MELCHIOR_RAINBOW_SHELL}
    )
    ret_list.append(kings_trial_resolution)

    melchior_forge_castle = LocRegion(
        "melchior_forge_castle",
        reward_spots={TID.MELCHIOR_RAINBOW_SHELL, TID.MELCHIOR_SUNSTONE_SPECS}
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
        reward_spots={TID.JERKY_GIFT}
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
        region_rewards=[memory.Flags.HAS_FORGED_MASAMUNE]
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
        reward_spots={BSID.ZENAN_BRIDGE, TID.ZENAN_BRIDGE_CAPTAIN}
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
        reward_spots={TID.SUN_KEEP_600_POWER_TAB}
    )
    ret_list.append(sun_keep_600)

    choras_cafe_600 = LocRegion(
        "choras_cafe_600",
        loc_exits={LocExit.CHORAS_CAFE_600},
        reward_spots={TID.TOMA_REWARD}
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
        reward_spots={TID.NORTHERN_RUINS_BASEMENT_600}
    )
    ret_list.append(northern_ruins_600)
    ret_list.append(
        LocRegion(
            "northern_ruins_600_repaired",
            reward_spots={TID.NORTHERN_RUINS_ANTECHAMBER_LEFT_600}
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
        }
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
        }
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
        region_rewards=[memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS]
    )
    ret_list.append(magus_castle)

    magic_cave = LocRegion(
        "magic_cave",
        loc_exits={LocExit.MAGIC_CAVE_MAGUS},
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
        region_rewards=[memory.Flags.SUNKEN_DESERT_BOSS_DEFEATED]
    )
    ret_list.append(sunken_desert)

    fiona_shrine = LocRegion(
        "fiona_shrine",
        loc_exits={LocExit.FIONAS_SHRINE},
        reward_spots={ShopID.FIONAS_SHRINE}
    )
    ret_list.append(fiona_shrine)

    fiona_campfire = LocRegion(
        "fiona_campfire",
        reward_spots={TID.FIONA_KEY}
    )
    ret_list.append(fiona_campfire)

    ret_list.append(
        LocRegion(
            "sun_keep_2300",
            loc_exits={LocExit.SUN_KEEP_2300}
        )
    )
    ret_list.append(
        LocRegion(
            "sun_keep_1000",
            loc_exits={LocExit.SUN_KEEP_1000}
        )
    )

    ret_list.append(
        LocRegion(
            "sun_keep_prehistory",
            loc_exits={LocExit.SUN_KEEP_PREHISTORY}
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
        reward_spots={TID.SUN_KEEP_2300, TID.LUCCA_WONDERSHOT, TID.TABAN_SUNSHADES}
    )
    ret_list.append(moonstone_quest)

    sun_palace = LocRegion(
        "sun_palace",
        loc_exits={LocExit.SUN_PALACE},
        reward_spots={TID.SUN_PALACE_KEY, BSID.SUN_PALACE}
    )
    ret_list.append(sun_palace)

    end_of_time = LocRegion(
        "end_of_time"
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
        }
    )
    ret_list.append(geno_dome)
    ret_list.append(geno_dome_inside)

    ret_list.append(
        LocRegion(
            "forest_maze_north",
            {LocExit.FOREST_MAZE_NORTH}
        )
    )
    forest_maze = LocRegion(
        "forest_maze",
        loc_exits={LocExit.FOREST_MAZE_SOUTH},
        reward_spots={
            TID.FOREST_MAZE_1, TID.FOREST_MAZE_2, TID.FOREST_MAZE_3,
            TID.FOREST_MAZE_4, TID.FOREST_MAZE_5, TID.FOREST_MAZE_6,
            TID.FOREST_MAZE_7, TID.FOREST_MAZE_8, TID.FOREST_MAZE_9,
        }
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
        }
    )
    ret_list.append(reptite_lair)

    tyrano_lair = LocRegion(
        "tyrano_lair",
        loc_exits={LocExit.TYRANO_LAIR},
        reward_spots={
            TID.TYRANO_LAIR_MAZE_1, TID.TYRANO_LAIR_MAZE_2,
            TID.TYRANO_LAIR_MAZE_3, TID.TYRANO_LAIR_MAZE_4,
            BSID.TYRANO_LAIR_NIZBEL
        },
        region_rewards=[memory.Flags.OW_LAVOS_HAS_FALLEN]
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
        }
    )
    ret_list.append(black_omen)

    last_village_north_cape = LocRegion(
        "last_village_north_cape",
        loc_exits={LocExit.NORTH_CAPE},
        reward_spots={RecruitID.NORTH_CAPE}
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
        "blackbird_scaffolding_epoch",
        region_rewards=[logictypes.ScriptReward.FLIGHT,
                        logictypes.ScriptReward.EPOCH]
    )
    ret_list.extend([blackbird_scaffolding, blackbird_scaffolding_epoch])

    blackbird = LocRegion(
        "blackbird",
        reward_spots={TID.BLACKBIRD_DUCTS_MAGIC_TAB,
                      BSID.EPOCH_REBORN, BSID.BLACKBIRD_LEFT_WING},
        region_rewards=[logictypes.ScriptReward.FLIGHT,
                        logictypes.ScriptReward.EPOCH]
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
                      ShopID.ENHASA}
    )
    ret_list.append(enhasa)

    kajar = LocRegion(
        "kajar",
        loc_exits={LocExit.KAJAR},
        reward_spots={TID.KAJAR_ROCK, TID.KAJAR_SPEED_TAB, ShopID.NU_NORMAL_KAJAR}
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
            BSID.ZEAL_PALACE
        }
    )
    ret_list.append(ocean_palace)

    ocean_palace_mammon_m = LocRegion(
        "ocean_palace_mammon_m",
        region_rewards=[memory.Flags.HAS_ALGETTY_PORTAL]
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
        }
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

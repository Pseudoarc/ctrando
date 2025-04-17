"""Keep a map of the whole game"""
from ctrando.overworlds.owexitdata import OWExitClass as OWExit


class OWRegion:
    def __init__(
            self,
            name: str,
            ow_exits: set[OWExit]
    ):
        self.name = name
        self.ow_exits = set(ow_exits)


def get_ow_regions() -> list[OWRegion]:
    # 1000AD Regions
    truce_1000_ow = OWRegion(
        "truce_1000_overworld",
        {
            OWExit.VORTEX_PT, OWExit.CRONOS_HOUSE, OWExit.TRUCE_SINGLE_RESIDENCE,
            OWExit.TRUCE_INN_1000, OWExit.TRUCE_TICKET_OFFICE, OWExit.TRUCE_SCREAMING_RESIDENCE,
            OWExit.MILLENNIAL_FAIR, OWExit.TRUCE_MARKET_1000, OWExit.TRUCE_MAYOR,
            OWExit.LUCCAS_HOUSE, OWExit.GUARDIA_FOREST_SOUTH_1000,
            OWExit.ZENAN_BRIDGE_1000_NORTH
        }
    )

    guardia_castle_1000_ow = OWRegion(
        "guardia_castle_1000_overworld",
        {OWExit.GUARDIA_CASTLE_1000, OWExit.GUARDIA_FOREST_NORTH_1000}
    )

    porre_1000_ow = OWRegion(
        "porre_1000_overworld",
        {
            OWExit.ZENAN_BRIDGE_1000_SOUTH, OWExit.PORRE_INN_1000, OWExit.PORRE_MARKET_1000,
            OWExit.SNAIL_STOP, OWExit.PORRE_MAYOR_1000, OWExit.PORRE_RESIDENCE_1000,
            OWExit.PORRE_TICKET_OFFICE,
        }
    )
    fiona_shrine_1000_ow = OWRegion(
        "fionas_shrine_overworld",
        {OWExit.FIONAS_SHRINE}
    )
    medina_1000_ow = OWRegion(
        "medina_1000_overworld",
        {
            OWExit.MEDINA_ELDER_HOUSE, OWExit.MEDINA_INN, OWExit.MEDINA_PORTAL,
            OWExit.MELCHIORS_HUT, OWExit.MEDINA_MARKET, OWExit.MEDINA_SQUARE,
            OWExit.FOREST_RUINS, OWExit.HECKRAN_CAVE,
        }
    )
    choras_1000_ow = OWRegion(
        "choras_1000_overworld",
        {
            OWExit.CHORAS_MAYOR_1000, OWExit.CHORAS_INN_1000, OWExit.CHORAS_CARPENTER_1000,
            OWExit.NORTHERN_RUINS_1000, OWExit.WEST_CAPE
        }
    )
    sun_keep_1000_ow = OWRegion("sun_keep_1000_overworld",
                                {OWExit.SUN_KEEP_1000})

    # 600AD regions
    truce_600_ow = OWRegion(
        "truce_600_overworld",
        {
            OWExit.ZENAN_BRIDGE_600_NORTH, OWExit.TRUCE_CANYON, OWExit.TRUCE_COUPLE_RESIDENCE_600,
            OWExit.TRUCE_SMITH_RESIDENCE, OWExit.TRUCE_INN_600, OWExit.TRUCE_MARKET_600,
            OWExit.GUARDIA_FOREST_SOUTH_600, OWExit.MANORIA_CATHEDRAL
        }
    )
    guardia_castle_600_ow = OWRegion(
        "guardia_castle_600_overworld",
        {OWExit.GUARDIA_CASTLE_600, OWExit.GUARDIA_FOREST_NORTH_600}
    )
    porre_600_ow = OWRegion(
        "porre_600_overworld",
        {
            OWExit.ZENAN_BRIDGE_600_SOUTH, OWExit.MAGIC_CAVE_OPEN, OWExit.MAGIC_CAVE_CLOSED,
            OWExit.DORINO_BROMIDE_RESIDENCE, OWExit.DORINO_INN, OWExit.DORINO_MARKET,
            OWExit.TATAS_HOUSE, OWExit.PORRE_ELDER_600, OWExit.PORRE_CAFE_600,
            OWExit.PORRE_INN_600, OWExit.PORRE_MARKET_600, OWExit.CURSED_WOODS,
            OWExit.DENADORO_MTS, OWExit.FIONAS_VILLA
        }
    )
    sunken_desert_600_ow = OWRegion(
        "sunken_desert_overworld",
        {OWExit.SUNKEN_DESERT}
    )
    choras_600_ow = OWRegion(
        "choras_600_overworld",
        {
            OWExit.CHORAS_OLD_RESIDENCE_600, OWExit.CHORAS_INN_600,
            OWExit.CHORAS_CAFE_600, OWExit.CHORAS_CARPENTER_600, OWExit.CHORAS_MARKET_600,
            OWExit.NORTHERN_RUINS_600,
        }
    )
    # Problem: Magus's lair OW exit disappears after magus is defeated.
    # - Just don't ever disable that exit?  No harm re-exploring the castle.
    magus_lair_600_ow = OWRegion(
        "magus_lair_overworld",
        {OWExit.MAGUS_LAIR, OWExit.MAGIC_CAVE_MAGUS}
    )
    ozzies_fort_600_ow = OWRegion("ozzies_fort_overworld", {OWExit.OZZIES_FORT})
    sun_keep_600_ow = OWRegion("sun_keep_600_overworld", {OWExit.SUN_KEEP_600})
    giants_claw_600_ow = OWRegion("giants_claw_overworld", {OWExit.GIANTS_CLAW})
    # Future
    trann_bangor_ow = OWRegion(
        "trann_bangor_overworld",
        {OWExit.TRANN_DOME, OWExit.BANGOR_DOME, OWExit.LAB_16_WEST}
    )
    arris_ow = OWRegion(
        "arris_overworld",
        {OWExit.ARRIS_DOME, OWExit.LAB_16_EAST, OWExit.SEWER_ACCESS_ARRIS,
         OWExit.LAB_32_WEST}
    )
    proto_ow = OWRegion(
        "proto_overworld",
        {OWExit.PROTO_DOME, OWExit.FACTORY_RUINS, OWExit.LAB_32_EAST}
    )
    keepers_ow = OWRegion(
        "keepers_overworld",
        {OWExit.KEEPERS_DOME, OWExit.SEWER_ACCESS_KEEPERS, OWExit.DEATH_PEAK}
    )
    sun_keep_2300 = OWRegion("sun_keep_2300_overworld", {OWExit.SUN_KEEP_2300})
    geno_dome = OWRegion("geno_overworld", {OWExit.GENO_DOME})
    sun_palace = OWRegion("sun_palace_overworld", {OWExit.SUN_PALACE})
    # Prehistory
    # Problem: Finding Dactyls puts you in Prehistory.
    # - May need to move Epoch to prehistory to allow escape
    # - May want to consider
    ioka_area_ow = OWRegion(
        "ioka_overworld",
        {OWExit.MYSTIC_MTS, OWExit.FOREST_MAZE_NORTH, OWExit.DACTYL_NEST,
         OWExit.IOKA_MEETING_SOUTH, OWExit.IOKA_MEETING_NORTH, OWExit.IOKA_MEETING_SOUTH,
         OWExit.CHIEFS_HUT, OWExit.TRADING_POST, OWExit.LARUBA_RUINS,
         OWExit.IOKA_SW_HUT, OWExit.IOKA_SWEET_WATER_HUT, OWExit.HUNTING_RANGE}
    )
    reptite_lair_ow = OWRegion(
        "reptite_lair_overworld",
        {OWExit.REPTITE_LAIR, OWExit.FOREST_MAZE_SOUTH}
    )
    sun_keep_prehistory_ow = OWRegion(
        "sun_keep_prehistory_overworld",
        {OWExit.SUN_KEEP_PREHISTORY}
    )
    tyrano_lair_ow = OWRegion("tyrano_lair_overworld", {OWExit.TYRANO_LAIR})
    # Problem: finishing Tyrano Lair will make Lavos fall and remove the lair exit.
    # May have to leave Tyrano lair vanilla?
    lair_ruins_ow = OWRegion("lair_ruins_overworld", {OWExit.LAIR_RUINS})
    # Dark Ages
    dark_ages_portal_ow = OWRegion(
        "dark_ages_portal_overworld",
        {OWExit.DARK_AGES_PORTAL, OWExit.TERRA_CAVE, OWExit.SKYWAY_ENHASA_SOUTH}
    )
    dark_ages_skyways_ow = OWRegion(
        "dark_ages_skyway_island_overworld",
        {OWExit.SKYWAY_ENHASA_NORTH, OWExit.SKYWAY_KAJAR}
    )
    # Zeal
    enhasa_ow = OWRegion(
        "enhasa_overworld",
        {OWExit.ENHASA, OWExit.LAND_BRIDGE_ENHASA_NORTH, OWExit.LAND_BRIDGE_ENHASA_SOUTH}
    )
    zeal_main_ow = OWRegion(
        "kajar_overworld",
        {OWExit.KAJAR, OWExit.BLACKBIRD, OWExit.ZEAL_TELEPORTER_BOTTOM, OWExit.LAND_BRIDGE_KAJAR}
    )
    zeal_palace_ow = OWRegion(
        "zeal_palace_overworld",
        {OWExit.ZEAL_PALACE, OWExit.ZEAL_TELEPORTER_TOP}
    )
    # Last Village
    last_village_ow = OWRegion(
        "last_village_overworld",
        {OWExit.LAST_VILLAGE_SHOP, OWExit.LAST_VILLAGE_COMMONS,
         OWExit.NORTH_CAPE, OWExit.LAST_VILLAGE_RESIDENCE, OWExit.LAST_VILLAGE_EMPTY_HUT}
    )
    last_village_portal_ow = OWRegion(
        "last_village_portal_overworld",
        {OWExit.LAST_VILLAGE_PORTAL}
    )
    last_village_sun_keep_ow = OWRegion(
        "last_village_sun_keep_overworld",
        {OWExit.SUN_KEEP_LAST_VILLAGE}
    )

    return [
        truce_1000_ow, guardia_castle_1000_ow, porre_1000_ow,
        fiona_shrine_1000_ow, medina_1000_ow, choras_1000_ow, sun_keep_1000_ow,
        truce_600_ow, guardia_castle_600_ow, sunken_desert_600_ow,
        porre_600_ow, choras_600_ow, magus_lair_600_ow, ozzies_fort_600_ow,
        sun_keep_600_ow, giants_claw_600_ow, trann_bangor_ow, arris_ow,
        proto_ow, keepers_ow, sun_keep_2300, geno_dome, sun_palace,
        ioka_area_ow, reptite_lair_ow, sun_keep_prehistory_ow, tyrano_lair_ow,
        lair_ruins_ow, dark_ages_portal_ow, dark_ages_skyways_ow, enhasa_ow,
        zeal_main_ow, zeal_palace_ow, last_village_ow, last_village_portal_ow,
        last_village_sun_keep_ow
    ]
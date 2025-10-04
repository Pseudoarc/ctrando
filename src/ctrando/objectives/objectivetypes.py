"""Module containing types for creating objectives"""
from enum import Enum, auto
import copy
from dataclasses import dataclass
import typing

from ctrando.bosses import bosstypes as bty
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent, scriptmanager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


HookFinder = typing.Callable[[locationevent.LocationEvent], int]

_objective_string = (
    "{line break}"
    "   Objective Complete: {item}{null}"
)


@dataclass
class ObjectiveSettings:
    num_algetty_portal_objectives: int
    num_omen_objectives: int
    num_bucket_objectives: int
    num_timegauge_objectives: int


def get_objective_count_checks(
        script: locationevent.LocationEvent,
        obj_settings: ObjectiveSettings,
):
    ret_ef = (
        EF()
        .add_if(
            EC.if_not_flag(memory.Flags.HAS_ALGETTY_PORTAL),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_algetty_portal_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("Algetty Portal Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.HAS_ALGETTY_PORTAL))
            )
        )
        .add_if(
            EC.if_not_flag(memory.Flags.BUCKET_AVAILABLE),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_bucket_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("Bucket Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.BUCKET_AVAILABLE))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_omen_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("Omen Boss Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS),
            EF().add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_timegauge_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("1999 Added to Epoch!{null}")
                )).add(EC.set_flag(memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS))
            )
        )
    )

    print(ret_ef)
    input()

    return ret_ef


class QuestID(Enum):
    """An enumeration of quests which are valid objectives."""
    # Going mostly in plot order to not forget things.
    MANORIA_CATHEDRAL = auto()
    CRONO_TRIAL = auto()
    # ARRIS_DOME_GUARDIAN = auto()
    # ARRIS_DOME_FOOD = auto()
    ARRIS_DOME = auto()  # Guardian + Seed turn-in
    FACTORY_RUINS = auto()
    HECKRAN_CAVE = auto()
    ZENAN_BRIDGE = auto()
    DENADORO_MOUNTAINS = auto()
    REPTITE_LAIR = auto()
    FORGE_MASAMUNE = auto()
    # Perhaps a separate entry for front of Castle boss fight
    MAGUS_CASTLE = auto()
    TYRANO_LAIR = auto()
    MT_WOE = auto()
    ZEAL_PALACE_THRONE = auto()
    OCEAN_PALACE = auto()
    BLACKBIRD = auto()
    EPOCH_REBORN_BATTLE = auto()
    # Now endgame quests
    JERKY_TRADE = auto()  # Maybe don't include this since it's just a turn-in
    SUN_PALACE = auto()
    CHARGE_MOONSTONE = auto()  # KI turn-in + Lucca
    GIANTS_CLAW = auto()
    KINGS_TRIAL = auto()  # All the way to Yarka XIII battle
    CYRUS_GRAVE = auto()
    OZZIES_FORT = auto()
    SUNKEN_DESERT = auto()  # All the way to Lucca's mission.
    GENO_DOME = auto()
    DEATH_PEAK = auto()
    SPEKKIO = auto()


@dataclass
class HookData:
    script: locationevent.LocationEvent
    pos: int


class HookLocator(typing.Protocol):
    """Protocol defining how hook lookups will be performed."""
    def __call__(
            self,
            script_manager: scriptmanager.ScriptManager
    ) -> HookData:
        ...

_special_tokens: tuple[str, ...] = (
    "any_quest",
    "open_quest",
    "gated_quest",
    "flight_gated_quest",
    "very_gated_quest",
    "any_boss",
    "any_miniboss",
    "none"
)

def get_special_tokens() -> tuple[str, ...]:
    return _special_tokens


class CommandSequenceLocator:
    """
    Class which specifies how to find a position in a script by following
    a sequence of commands.  Implements HookLocator
    """
    def __init__(self,
                 loc_id: ctenums.LocID,
                 obj_id: int,
                 func_id: FID,
                 cmd_sequence: list[typing.Union[EC, int]],
                 place_after_last: bool
    ):
        self.loc_id = loc_id
        self.obj_id = obj_id
        self.func_id = func_id
        self.cmd_sequence = list(cmd_sequence)
        self.place_after_last = place_after_last

    def __call__(self, script_manager: scriptmanager.ScriptManager):
        """
        Open loc_id's script, navigate to the object/function, and then
        find the sequence of commands in order.  The QuestLocator will
        find the position of the final command.  If place_after_last
        is True, then the position after the final command will be found.
        """
        script = script_manager[self.loc_id]

        pos = script.get_function_start(self.obj_id, self.func_id)
        for ind, cmd in enumerate(self.cmd_sequence):
            if isinstance(cmd, int):
                pos, found_cmd = script.find_command([cmd], pos)
            else:
                found_cmd = cmd
                pos = script.find_exact_command(cmd, pos)

            if ind != len(self.cmd_sequence)-1:
                pos += len(found_cmd)
            elif self.place_after_last:
                pos += len(found_cmd)

        return HookData(script, pos)

    def __str__(self):
        ret = f"{self.__class__.__name__}: loc_id={self.loc_id}, obj_id={self.obj_id}, func_id={self.func_id}, cmds={self.cmd_sequence}"
        if self.place_after_last:
            ret += " (after last)"

        return ret


@dataclass
class QuestData:
    name: str
    desc: str


_quest_data_dict: dict[QuestID, QuestData] = {
    QuestID.MANORIA_CATHEDRAL: QuestData("*Cathedral", "Defeat Manoria Boss"),
    QuestID.CRONO_TRIAL: QuestData("*CronoTrial", "Escape Guardia Prison"),
    QuestID.ARRIS_DOME: QuestData("*ArrisDome", "Guardian + Doan Seed"),
    QuestID.FACTORY_RUINS: QuestData("*Factory", "Defeat Factory Boss"),
    QuestID.HECKRAN_CAVE: QuestData("*HeckranCave", "Defeat Heckran Cave Boss"),
    QuestID.ZENAN_BRIDGE: QuestData("*ZenanBrdge", "Defeat Zenan Bridge Boss"),
    QuestID.DENADORO_MOUNTAINS: QuestData("*Denadoro", "Defeat Denadoro Boss"),
    QuestID.REPTITE_LAIR: QuestData("*ReptiteLr", "Defeat Reptite Lair Boss"),
    QuestID.FORGE_MASAMUNE: QuestData("*ForgeMasa", "Forge the Masamune"),
    QuestID.MAGUS_CASTLE: QuestData("*MagusCstle", "Clear Magus's Castle"),
    QuestID.TYRANO_LAIR: QuestData("*TyranoLair", "Defeat Black Tyrano"),
    QuestID.MT_WOE: QuestData("*Mt. Woe", "Defeat Boss of Mt. Woe"),
    QuestID.ZEAL_PALACE_THRONE: QuestData("*ZealThrone", "Defeat Zeal Palace Boss"),
    QuestID.OCEAN_PALACE: QuestData("*OceanPalce", "Use Ruby Knife on Mammon M"),
    QuestID.BLACKBIRD: QuestData("*BlackBird", "Escape from the Blackbird"),
    QuestID.EPOCH_REBORN_BATTLE: QuestData("*EpochBoss", "Defeat the boss on Epoch"),
    QuestID.JERKY_TRADE: QuestData("*JerkyTrade", "Trade The Jerky Away (Porre)"),
    QuestID.SUN_PALACE: QuestData("*SunPalace", "Obtain the Sun Palace Treasure"),
    QuestID.CHARGE_MOONSTONE: QuestData("*ChargeMoon", "Charge the Moonstone"),
    QuestID.GIANTS_CLAW: QuestData("*GiantsClaw", "Obtain the Giant's Claw Treasure"),
    QuestID.KINGS_TRIAL: QuestData("*KingTrial", "Clear King Guardia's Name"),
    QuestID.CYRUS_GRAVE: QuestData("*CyrusGrave", "Have Frog Bring Masa to Cyrus"),
    QuestID.OZZIES_FORT: QuestData("*OzzieFort", "Defeat Ozzie (Cat Switch)"),
    QuestID.SUNKEN_DESERT: QuestData("*SunkenDsrt", "Have Lucca Face Her Past"),
    QuestID.GENO_DOME: QuestData("*Geno Dome", "Defeat Geno Dome Boss"),
    QuestID.DEATH_PEAK: QuestData("*DeathPeak", "Clear Death Peak"),
    QuestID.SPEKKIO: QuestData("*Spekkio", "Defeat Spekkio")
}

_boss_abbrev: dict[bty.BossID, str] = {
    bty.BossID.ATROPOS_XR: 'AtroposXR',
    bty.BossID.DALTON: 'Dalton',
    bty.BossID.DALTON_PLUS: 'DaltonPlus',
    bty.BossID.ELDER_SPAWN: 'ElderSpawn',
    bty.BossID.FLEA: 'Flea',
    bty.BossID.FLEA_PLUS: 'Flea Plus',
    bty.BossID.GATO: 'Gato',
    bty.BossID.GIGA_MUTANT: 'GigaMutant',
    bty.BossID.GOLEM: 'Golem',
    bty.BossID.GOLEM_BOSS: 'Golem Boss',
    bty.BossID.HECKRAN: 'Heckran',
    bty.BossID.KRAWLIE: 'Krawlie',
    bty.BossID.LAVOS_SPAWN: 'LavosSpawn',
    bty.BossID.MAMMON_M: 'Mammon M',
    bty.BossID.MAGUS_NORTH_CAPE: 'Magus (NC)',
    bty.BossID.MASA_MUNE: 'Masa&Mune',
    bty.BossID.MEGA_MUTANT: 'MegaMutant',
    bty.BossID.MUD_IMP: 'Mud Imp',
    bty.BossID.NIZBEL: 'Nizbel',
    bty.BossID.NIZBEL_2: 'Nizbel II',
    bty.BossID.RETINITE: 'Retinite',
    bty.BossID.R_SERIES: 'R Series',
    bty.BossID.RUST_TYRANO: 'RustTyrano',
    bty.BossID.SLASH_SWORD: 'Slash',
    bty.BossID.SUPER_SLASH: 'SuperSlash',
    bty.BossID.SON_OF_SUN: 'Son of Sun',
    bty.BossID.TERRA_MUTANT: 'TerraMutnt',
    bty.BossID.YAKRA: 'Yakra',
    bty.BossID.YAKRA_XIII: 'Yakra XIII',
    bty.BossID.ZOMBOR: 'Zombor',
    bty.BossID.MOTHER_BRAIN: 'MotherBrn',
    bty.BossID.DRAGON_TANK: 'DragonTank',
    bty.BossID.GIGA_GAIA: 'Giga Gaia',
    bty.BossID.GUARDIAN: 'Guardian',
    bty.BossID.OZZIE_TRIO: 'Ozzie Trio',
    #
    # bty.BossID.MAGUS: 'Magus',
    # bty.BossID.BLACK_TYRANO: 'Black Tyrano'
}

def get_boss_item_name(boss_id: bty.BossID) -> str:
    return _boss_abbrev[boss_id]


def get_quest_data(quest_id: QuestID) -> QuestData:
    """Returns a given quest's name and desc"""
    data = _quest_data_dict[quest_id]
    return QuestData(data.name, data.desc)


_quest_locator_dict: dict[QuestID, HookLocator] = {
    QuestID.MANORIA_CATHEDRAL: CommandSequenceLocator(
        ctenums.LocID.MANORIA_COMMAND, 8, FID.STARTUP,
        [EC.break_cmd()], False
    ),
    QuestID.CRONO_TRIAL: CommandSequenceLocator(
        ctenums.LocID.PRISON_CATWALKS,0, FID.ARBITRARY_0,
        [EC.party_follow()], False
    ),
    QuestID.ARRIS_DOME: CommandSequenceLocator(
        ctenums.LocID.ARRIS_DOME,0xF, FID.TOUCH,
        [EC.party_follow()], False
    ),
    QuestID.FACTORY_RUINS: CommandSequenceLocator(
        ctenums.LocID.FACTORY_RUINS_SECURITY_CENTER, 0, FID.STARTUP,
        [EC.reset_byte(0x7F0212)],
        True,
    ),
    QuestID.HECKRAN_CAVE: CommandSequenceLocator(
        ctenums.LocID.HECKRAN_CAVE_BOSS, 0, FID.STARTUP,
        [0xD8], True
    ),
    QuestID.ZENAN_BRIDGE: CommandSequenceLocator(
        ctenums.LocID.ZENAN_BRIDGE_BOSS, 1, FID.STARTUP,
        [EC.set_flag(memory.Flags.OW_ZENAN_COMPLETE)],
        True
    ),
    QuestID.DENADORO_MOUNTAINS: CommandSequenceLocator(
        ctenums.LocID.DENADORO_CAVE_OF_MASAMUNE, 0xA, FID.TOUCH,
        [0xBB], True
    ),
    QuestID.REPTITE_LAIR: CommandSequenceLocator(
        ctenums.LocID.REPTITE_LAIR_AZALA_ROOM,0, FID.STARTUP,
        [EC.set_flag(memory.Flags.NIZBEL_DEFEATED)],
        True,
    ),
    QuestID.FORGE_MASAMUNE: CommandSequenceLocator(
        ctenums.LocID.MELCHIORS_KITCHEN, 8, FID.ACTIVATE,
        [
            EC.call_obj_function(4, FID.ARBITRARY_1, 6, FS.HALT),
            0xF1
         ], False
    ),
    QuestID.MAGUS_CASTLE: CommandSequenceLocator(
        ctenums.LocID.MAGUS_CASTLE_INNER_SANCTUM, 9, FID.ACTIVATE,
        [0xD8, EC.static_animation(0x5D), EC.static_animation(0x5D)], False
    ),
    QuestID.TYRANO_LAIR: CommandSequenceLocator(
        ctenums.LocID.TYRANO_LAIR_KEEP, 0x15, FID.ARBITRARY_0,
        [0xD8], True
    ),
    QuestID.MT_WOE: CommandSequenceLocator(
        ctenums.LocID.MT_WOE_SUMMIT, 0, FID.ARBITRARY_0,
        [0xD8], True
    ),
    QuestID.ZEAL_PALACE_THRONE: CommandSequenceLocator(
        ctenums.LocID.ZEAL_PALACE_THRONE_NIGHT, 9, FID.ARBITRARY_0,
        [0xD8], True
    ),
    QuestID.OCEAN_PALACE: CommandSequenceLocator(
        ctenums.LocID.OCEAN_PALACE_THRONE, 0xB, FID.STARTUP,
        [EC.set_flag(memory.Flags.ZEAL_HAS_FALLEN)], True
    ),
    QuestID.BLACKBIRD: CommandSequenceLocator(
        ctenums.LocID.BLACKBIRD_LEFT_WING, 0x18, FID.STARTUP,
        [0xD8], True
    ),
    QuestID.EPOCH_REBORN_BATTLE: CommandSequenceLocator(
        ctenums.LocID.REBORN_EPOCH, 9, FID.STARTUP,
        [0xD8], True
    ),
    QuestID.JERKY_TRADE: CommandSequenceLocator(
        ctenums.LocID.PORRE_MAYOR_1F, 0x8, FID.ACTIVATE,
        [EC.play_sound(4)], True
    ),
    QuestID.SUN_PALACE: CommandSequenceLocator(
        ctenums.LocID.SUN_PALACE, 0x11, FID.ACTIVATE,
        [EC.set_explore_mode(True)], False
    ),
    QuestID.CHARGE_MOONSTONE: CommandSequenceLocator(
        ctenums.LocID.SUN_KEEP_2300, 0x8, FID.ACTIVATE,
        [0xBB], True
    ),
    QuestID.GIANTS_CLAW: CommandSequenceLocator(
        ctenums.LocID.GIANTS_CLAW_TYRANO, 1, FID.STARTUP,
        [0xBB], True
    ),
    QuestID.KINGS_TRIAL: CommandSequenceLocator(
        ctenums.LocID.KINGS_TRIAL, 0xA, FID.ARBITRARY_3,
        [0xD8], True
    ),
    QuestID.CYRUS_GRAVE: CommandSequenceLocator(
        ctenums.LocID.NORTHERN_RUINS_HEROS_GRAVE, 5, FID.ARBITRARY_5,
        [EC.set_flag(memory.Flags.MASAMUNE_UPGRADED)], True
    ),
    QuestID.OZZIES_FORT: CommandSequenceLocator(
        ctenums.LocID.OZZIES_FORT_THRONE_INCOMPETENCE, 8, FID.TOUCH,
        [EC.party_follow()], False
    ),
    QuestID.SUNKEN_DESERT: CommandSequenceLocator(
        ctenums.LocID.FIONA_FOREST, 1, FID.ARBITRARY_4,
        [EC.return_cmd()], False
    ),
    QuestID.GENO_DOME: CommandSequenceLocator(
        ctenums.LocID.GENO_DOME_MAINFRAME, 0, FID.ARBITRARY_3,
        [EC.return_cmd()], False
    ),
    QuestID.DEATH_PEAK: CommandSequenceLocator(
        ctenums.LocID.DEATH_PEAK_GUARDIAN_SPAWN, 8, FID.ACTIVATE,
        [EC.return_cmd()], False
    ),
    QuestID.SPEKKIO: CommandSequenceLocator(
        ctenums.LocID.SPEKKIO, 0, FID.ARBITRARY_0,
        cmd_sequence=[EC.set_byte(0x7F0232)], place_after_last=True
    )
}

ObjectiveType = QuestID | bty.BossID | None

_associated_objs: list[tuple[ObjectiveType, ...]] = [
    (QuestID.MANORIA_CATHEDRAL, bty.BossSpotID.MANORIA_CATHERDAL),
    (QuestID.CRONO_TRIAL, bty.BossSpotID.PRISON_CATWALKS),
    (QuestID.FACTORY_RUINS, bty.BossSpotID.FACTORY_RUINS),
    (QuestID.HECKRAN_CAVE, bty.BossSpotID.HECKRAN_CAVE),
    (QuestID.ZENAN_BRIDGE, bty.BossSpotID.ZENAN_BRIDGE),
    (QuestID.DENADORO_MOUNTAINS, bty.BossSpotID.DENADORO_MTS),
    (QuestID.REPTITE_LAIR, bty.BossSpotID.REPTITE_LAIR),
    (QuestID.MT_WOE, bty.BossSpotID.MT_WOE),
    (QuestID.ZEAL_PALACE_THRONE, bty.BossSpotID.ZEAL_PALACE),
    (QuestID.BLACKBIRD, bty.BossSpotID.BLACKBIRD_LEFT_WING),
    (QuestID.EPOCH_REBORN_BATTLE, bty.BossSpotID.EPOCH_REBORN),
    (QuestID.SUN_PALACE, bty.BossSpotID.SUN_PALACE),
    (QuestID.GIANTS_CLAW, bty.BossSpotID.GIANTS_CLAW),
    (QuestID.KINGS_TRIAL, bty.BossSpotID.KINGS_TRIAL),
    (QuestID.OZZIES_FORT, bty.BossSpotID.OZZIES_FORT_TRIO),
    (QuestID.GENO_DOME, bty.BossSpotID.GENO_DOME_FINAL),
    # Not death peak
]

_boss_spot_locator_dict: dict[bty.BossSpotID, HookLocator] = {
    bty.BossSpotID.MAGUS_CASTLE_FLEA: CommandSequenceLocator(
        ctenums.LocID.MAGUS_CASTLE_FLEA, 0xC, FID.STARTUP,
        [0xD8, 0xD8], True
    ),
    bty.BossSpotID.MAGUS_CASTLE_SLASH: CommandSequenceLocator(
        ctenums.LocID.MAGUS_CASTLE_SLASH, 0xB, FID.STARTUP,
        [0xD8], True
    ),
    bty.BossSpotID.TYRANO_LAIR_NIZBEL: CommandSequenceLocator(
        ctenums.LocID.TYRANO_LAIR_NIZBEL, 0xA, FID.ACTIVATE,
        [0xD8], True
    ),
    bty.BossSpotID.DEATH_PEAK: CommandSequenceLocator(
        ctenums.LocID.DEATH_PEAK_CAVE, 0x0, FID.STARTUP,
        [EC.set_flag(memory.Flags.DEATH_PEAK_CAVE_LAVOS_SPAWN)], False
    ),
    bty.BossSpotID.BLACK_OMEN_MEGA_MUTANT: CommandSequenceLocator(
        ctenums.LocID.BLACK_OMEN_1F_ENTRANCE, 0x00, FID.STARTUP,
        [EC.set_flag(memory.Flags.BLACK_OMEN_MEGA_MUTANT_BATTLE)], False
    ),
    bty.BossSpotID.BLACK_OMEN_GIGA_MUTANT: CommandSequenceLocator(
        ctenums.LocID.BLACK_OMEN_GIGA_MUTANT, 0xA, FID.ACTIVATE,
        [EC.return_cmd()], False
    ),
    bty.BossSpotID.BLACK_OMEN_TERRA_MUTANT: CommandSequenceLocator(
        ctenums.LocID.BLACK_OMEN_TERRA_MUTANT, 0x8, FID.TOUCH,
        [EC.reset_byte(0x7F0212)], False
    ),
    bty.BossSpotID.BLACK_OMEN_ELDER_SPAWN: CommandSequenceLocator(
        ctenums.LocID.BLACK_OMEN_ELDER_SPAWN, 0x00, FID.STARTUP,
        [EC.set_flag(memory.Flags.BLACK_OMEN_ELDER_SPAWN)], False
    ),
    bty.BossSpotID.OZZIES_FORT_FLEA_PLUS: CommandSequenceLocator(
        ctenums.LocID.OZZIES_FORT_FLEA_PLUS, 0x09, FID.ACTIVATE,
        [EC.set_explore_mode(True)], False
    ),
    bty.BossSpotID.OZZIES_FORT_SUPER_SLASH: CommandSequenceLocator(
        ctenums.LocID.OZZIES_FORT_SUPER_SLASH, 0x09, FID.ACTIVATE,
        [EC.set_explore_mode(True)], False
    ),
    bty.BossSpotID.OCEAN_PALACE_TWIN_GOLEM: CommandSequenceLocator(
        ctenums.LocID.OCEAN_PALACE_REGAL_ANTECHAMBER, 0xD, FID.STARTUP,
        [0xD8], True
    ),
    bty.BossSpotID.GENO_DOME_MID: CommandSequenceLocator(
        ctenums.LocID.GENO_DOME_MAINFRAME, 0x00, FID.ARBITRARY_2,
        [EC.call_obj_function(0x1D, FID.ARBITRARY_0, 1, FS.HALT)],
        False
    ),
    bty.BossSpotID.BEAST_CAVE: CommandSequenceLocator(
        ctenums.LocID.BEAST_NEST, 0x00, FID.STARTUP,
        [EC.set_explore_mode(True)], False
    ),
    bty.BossSpotID.ARRIS_DOME: CommandSequenceLocator(
        ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER, 0x09, FID.ACTIVATE,
        [0xD8, EC.set_explore_mode(True)], False
    ),
    bty.BossSpotID.MILLENNIAL_FAIR_GATO: CommandSequenceLocator(
        ctenums.LocID.GATO_EXHIBIT, 0x00, FID.STARTUP,
        [0xD8, EC.party_follow()], False
    ),
    bty.BossSpotID.SEWERS_KRAWLIE: CommandSequenceLocator(
        ctenums.LocID.SEWERS_B1, 0x22, FID.ACTIVATE,
        [0xD8], True
    ),
    bty.BossSpotID.SUNKEN_DESERT: CommandSequenceLocator(
        ctenums.LocID.SUNKEN_DESERT_DEVOURER, 0, FID.ARBITRARY_0,
        [EC.return_cmd()], False
    ),
    bty.BossSpotID.BLACK_OMEN_ZEAL: CommandSequenceLocator(
        ctenums.LocID.BLACK_OMEN_ZEAL, 8, FID.STARTUP,
        [0xD8], True
    )
}

for eq_class in _associated_objs:
    try:
        quest_id = next(x for x in eq_class if isinstance(x, QuestID))
        spot_id = next(x for x in eq_class if isinstance(x, bty.BossSpotID))

        _boss_spot_locator_dict[spot_id] = _quest_locator_dict[quest_id]
    except StopIteration:
        pass


def get_boss_locator_dict() -> dict[bty.BossSpotID, HookLocator]:
    return _boss_spot_locator_dict


def get_boss_spot_locator(boss_spot_id: bty.BossSpotID) -> HookLocator:
    return _boss_spot_locator_dict[boss_spot_id]


def get_boss_locator(boss_id: bty.BossID,
                     boss_assign_dict: dict[bty.BossSpotID, bty.BossID]) -> HookLocator:
    locators: list[HookLocator] = []

    for spot, boss in boss_assign_dict.items():
        if boss == boss_id:
            locators.append(copy.deepcopy(_boss_spot_locator_dict[spot]))

    if not locators:
        raise KeyError(f"Unable to find {boss_id}.")

    # If multi-assign... return them all?
    return locators[0]


def get_associated_objectives() -> list[tuple[ObjectiveType, ...]]:
    return list(_associated_objs)


def get_quest_locator(quest_id: QuestID) -> HookLocator:
    """Get a quest's hook locator"""
    locator = _quest_locator_dict[quest_id]
    return copy.deepcopy(locator)


def get_obj_keys(obj_str: str) -> list[ObjectiveType]:

    for boss_id in bty.BossID:
        if boss_id == obj_str:
            return [bty.BossID(boss_id)]

    for quest_id in QuestID:
        if quest_id.name.lower() == obj_str:
            return [quest_id]

    if obj_str not in _special_tokens:
        raise ValueError("Invalid objective specifier.")

    if obj_str == "any_quest":
        return list(QuestID)
    elif obj_str == "open_quest":
        return [
            QuestID.MANORIA_CATHEDRAL, QuestID.HECKRAN_CAVE,
            QuestID.CRONO_TRIAL, QuestID.DENADORO_MOUNTAINS,
        ]
    elif obj_str == "gated_quest":
        return [
            QuestID.MT_WOE, QuestID.FACTORY_RUINS, QuestID.ARRIS_DOME,
            QuestID.TYRANO_LAIR, QuestID.JERKY_TRADE, QuestID.ZENAN_BRIDGE,
            QuestID.REPTITE_LAIR, QuestID.EPOCH_REBORN_BATTLE, QuestID.ZEAL_PALACE_THRONE,
            QuestID.KINGS_TRIAL,
        ]
    elif obj_str == "flight_gated_quest":
        return [
            QuestID.SUN_PALACE, QuestID.CYRUS_GRAVE, QuestID.OZZIES_FORT,
            QuestID.CHARGE_MOONSTONE, QuestID.GENO_DOME, QuestID.GIANTS_CLAW,
            QuestID.CYRUS_GRAVE,
        ]
    elif obj_str == "very_gated_quest":
        return [
            QuestID.BLACKBIRD, QuestID.SUNKEN_DESERT, QuestID.FORGE_MASAMUNE,
            QuestID.DEATH_PEAK, QuestID.MAGUS_CASTLE, QuestID.OCEAN_PALACE,
            QuestID.SUNKEN_DESERT
        ]
    elif obj_str == "any_boss":
        return bty.get_assignable_bosses()
    elif obj_str == "any_miniboss":
        return bty.get_minibosses()
    elif obj_str == "none":
        return [None]
    else:
        raise ValueError(f"Unknown objective: \"{obj_str}\".")

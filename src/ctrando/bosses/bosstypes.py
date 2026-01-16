"""
This module contains enumerations for bosses and boss spots and some functions
describing the default relationship between them.
"""

from __future__ import annotations

import copy
import enum
import typing

from ctrando.common import ctenums


class BossSpotID(enum.StrEnum):
    """Enum for Boss Spots."""
    MANORIA_CATHERDAL = enum.auto()
    HECKRAN_CAVE = enum.auto()
    DENADORO_MTS = enum.auto()
    ZENAN_BRIDGE = enum.auto()
    REPTITE_LAIR = enum.auto()
    MAGUS_CASTLE_FLEA = enum.auto()
    MAGUS_CASTLE_SLASH = enum.auto()
    # MAGUS_CASTLE_MAGUS = enum.auto()  # Removing until actually needed
    GIANTS_CLAW = enum.auto()
    TYRANO_LAIR_NIZBEL = enum.auto()
    ZEAL_PALACE = enum.auto()
    DEATH_PEAK = enum.auto()
    BLACK_OMEN_MEGA_MUTANT = enum.auto()
    BLACK_OMEN_GIGA_MUTANT = enum.auto()
    BLACK_OMEN_TERRA_MUTANT = enum.auto()
    BLACK_OMEN_ELDER_SPAWN = enum.auto()
    KINGS_TRIAL = enum.auto()

    SUN_PALACE = enum.auto()
    SUNKEN_DESERT = enum.auto()
    OCEAN_PALACE_TWIN_GOLEM = enum.auto()
    OCEAN_PALACE_TWIN_GOLEM_ALT =  enum.auto()

    GENO_DOME_FINAL = enum.auto()
    BEAST_CAVE = enum.auto()
    MT_WOE = enum.auto()
    ARRIS_DOME = enum.auto()
    FACTORY_RUINS = enum.auto()
    PRISON_CATWALKS = enum.auto()
    BLACKBIRD_LEFT_WING = enum.auto()
    OZZIES_FORT_TRIO = enum.auto()
    NORTH_CAPE = enum.auto()

    # minibosses
    EPOCH_REBORN = enum.auto()
    OZZIES_FORT_FLEA_PLUS = enum.auto()
    OZZIES_FORT_SUPER_SLASH = enum.auto()
    GENO_DOME_MID = enum.auto()
    MILLENNIAL_FAIR_GATO = enum.auto()
    SEWERS_KRAWLIE = enum.auto()
    BLACK_OMEN_ZEAL = enum.auto()

    def __str__(self):
        return _boss_spot_names[self]


_boss_spot_names: dict[BossSpotID, str] = {
    BossSpotID.MANORIA_CATHERDAL: 'Cathedral',
    BossSpotID.HECKRAN_CAVE: 'Heckran\'s Cave',
    BossSpotID.DENADORO_MTS: 'Denadoro Mountains',
    BossSpotID.ZENAN_BRIDGE: 'Zenan Bridge',
    BossSpotID.REPTITE_LAIR: 'Reptite Lair',
    BossSpotID.MAGUS_CASTLE_FLEA: 'Magus Castle Flea',
    BossSpotID.MAGUS_CASTLE_SLASH: 'Magus Castle Slash',
    BossSpotID.GIANTS_CLAW: 'Giant\'s Claw',
    BossSpotID.TYRANO_LAIR_NIZBEL: 'Tyrano Lair Midboss',
    BossSpotID.ZEAL_PALACE: 'Zeal Palace Throneroom',
    BossSpotID.DEATH_PEAK: 'Death Peak',
    BossSpotID.BLACK_OMEN_MEGA_MUTANT: 'Black Omen Mega Mutant',
    BossSpotID.BLACK_OMEN_GIGA_MUTANT: 'Black Omen Giga Mutant',
    BossSpotID.BLACK_OMEN_TERRA_MUTANT: 'Black Omen Terra Mutant',
    BossSpotID.BLACK_OMEN_ELDER_SPAWN: 'Black Omen Elder Spawn',
    BossSpotID.KINGS_TRIAL: 'King\'s Trial',
    BossSpotID.OZZIES_FORT_FLEA_PLUS: 'Ozzie\'s Fort Flea Plus',
    BossSpotID.OZZIES_FORT_SUPER_SLASH: 'Ozzie\'s Fort Super Slash',
    BossSpotID.SUN_PALACE: 'Sun Palace',
    BossSpotID.SUNKEN_DESERT: 'Sunken Desert',
    BossSpotID.OCEAN_PALACE_TWIN_GOLEM: 'Ocean Palace Twin Boss',
    BossSpotID.OCEAN_PALACE_TWIN_GOLEM_ALT: 'Ocean Palace Twin Boss (Twin)',
    BossSpotID.GENO_DOME_MID: 'Geno Dome (Mid)',
    BossSpotID.GENO_DOME_FINAL: 'Geno Dome (Final)',
    BossSpotID.BEAST_CAVE: 'Beast Cave',
    BossSpotID.MT_WOE: 'Mt. Woe',
    BossSpotID.ARRIS_DOME: 'Arris Dome',
    BossSpotID.FACTORY_RUINS: 'Factory',
    BossSpotID.PRISON_CATWALKS: 'Prison Catwalks',
    BossSpotID.BLACKBIRD_LEFT_WING: 'Blackbird Left Wing',
    BossSpotID.EPOCH_REBORN: 'Epoch Reborn',
    BossSpotID.MILLENNIAL_FAIR_GATO: 'Millennial Fair Gato',
    BossSpotID.SEWERS_KRAWLIE: 'Future Sewers',
    BossSpotID.OZZIES_FORT_TRIO: 'Ozzie\'s Fort Trio',
    BossSpotID.BLACK_OMEN_ZEAL: 'Black Omen Zeal',
    BossSpotID.NORTH_CAPE: "North Cape"
}


class BossID(enum.StrEnum):
    """Enum for bosses."""
    DALTON = "dalton"
    DALTON_PLUS = "dalton_plus"
    ELDER_SPAWN = "elder_spawn"
    FLEA = "flea"
    GIGA_MUTANT = "giga_mutant"
    GOLEM = "golem"
    GOLEM_BOSS = "golem_boss"
    HECKRAN = "heckran"
    LAVOS_SPAWN = "lavos_spawn"
    MAMMON_M = "mammon_machine"
    MAGUS_NORTH_CAPE = "magus_nc"
    MASA_MUNE = "masa_mune"
    MEGA_MUTANT = "mega_mutant"
    MUD_IMP = "mud_imp"
    NIZBEL = "nizbel"
    NIZBEL_2 = "nizbel_2"
    RETINITE = "retinite"
    R_SERIES = "r_series"
    RUST_TYRANO = "rust_tyrano"
    SLASH_SWORD = "slash"
    SON_OF_SUN = "son_of_sun"
    TERRA_MUTANT = "terra_mutant"
    YAKRA = "yakra"
    YAKRA_XIII = "yakra_xiii"
    ZOMBOR = "zombor"

    MOTHER_BRAIN = "mother_brain"
    DRAGON_TANK = "dragon_tank"
    GIGA_GAIA = "giga_gaia"
    GUARDIAN = "guardian"

    MAGUS = "magus"
    BLACK_TYRANO = "black_tyrano"
    OZZIE_TRIO = "ozzie_trio"

    # Midbosses
    ATROPOS_XR = "atropos"
    FLEA_PLUS = "flea_plus"
    SUPER_SLASH = "super_slash"
    KRAWLIE = "krawlie"
    GATO = "gato"

    # End Bosses
    LAVOS_SHELL = "lavos1"
    INNER_LAVOS = "lavos2"
    LAVOS_CORE = "lavos3"
    ZEAL = "zeal"
    ZEAL_2 = "zeal2"

    def __str__(self):
        if self == BossID.MAGUS_NORTH_CAPE:
            return 'Magus (North Cape)'
        if self == BossID.YAKRA_XIII:
            return 'Yakra XIII'
        if self == BossID.NIZBEL_2:
            return 'Nizbel II'

        out = self.__repr__().split('.')[1].split(':')[0].lower().title()
        out = out.replace('_', ' ')
        return out

_split_name_dict: dict[BossID, tuple[str,str]] = {
    BossID.DALTON: ("dal", "ton"),
    BossID.DALTON_PLUS: ("dalton", "plus"),
    BossID.ELDER_SPAWN: ("elder", "spawn"),
    BossID.FLEA: ("fl", "ea"),
    BossID.GIGA_MUTANT: ("giga", "mutant"),
    BossID.GOLEM: ("go", "lem"),
    BossID.GOLEM_BOSS: ("golem", "boss"),
    BossID.HECKRAN: ("heck", "ran"),
    BossID.LAVOS_SPAWN: ("lavos", "spawn"),
    # BossID.MAMMON_M: "mammon_machine",
    BossID.MAGUS_NORTH_CAPE: ("mag", "us"),
    BossID.MASA_MUNE: ("masa", "mune"),
    BossID.MEGA_MUTANT: ("mega", "mutant"),
    BossID.MUD_IMP: ("mud", "imp"),
    BossID.NIZBEL: ("niz", "bel"),
    BossID.NIZBEL_2: ("niz", "bel_2"),
    BossID.RETINITE: ("retin", "ite"),
    BossID.R_SERIES: ("r", "series"),
    BossID.RUST_TYRANO: ("rust", "tyrano"),
    BossID.SLASH_SWORD: ("sl", "ash"),
    BossID.SON_OF_SUN: ("son of", "sun"),
    BossID.TERRA_MUTANT: ("terra", "mutant"),
    BossID.YAKRA: ("yak", "ra"),
    BossID.YAKRA_XIII: ("yakra", "XIII"),
    BossID.ZOMBOR: ("zom", "bor"),

    BossID.MOTHER_BRAIN: ("mother", "brain"),
    BossID.DRAGON_TANK: ("dragon", "tank"),
    BossID.GIGA_GAIA: ("giga", "gaia"),
    BossID.GUARDIAN: ("guard", "ian"),
    BossID.OZZIE_TRIO: ("ozzie", "trio"),
    BossID.ZEAL: ("ze", "al"),
}
def get_split_name(boss_id: BossID) -> tuple[str, str]:
    return _split_name_dict.get(boss_id, ("masa", "mune"))


_abbrev_name_dict: dict[BossID, str] = {
    BossID.DALTON: "Dalton",
    BossID.DALTON_PLUS: "Dalton",
    BossID.ELDER_SPAWN: "Spawn",
    BossID.FLEA: "Flea",
    BossID.GIGA_MUTANT: "Mutant",
    BossID.GOLEM: "Golem",
    BossID.GOLEM_BOSS: "Golem",
    BossID.HECKRAN: "Heckran",
    BossID.LAVOS_SPAWN: "Spawn",
    # BossID.MAMMON_M: "mammon_machine",
    BossID.MAGUS_NORTH_CAPE: "Magus",
    BossID.MASA_MUNE: "Masamune",
    BossID.MEGA_MUTANT: "Mutant",
    BossID.MUD_IMP: "Mud Imp",
    BossID.NIZBEL: "Nizbel",
    BossID.NIZBEL_2: "Nizbel",
    BossID.RETINITE: "Retinite",
    BossID.R_SERIES: "R-Series",
    BossID.RUST_TYRANO: ("Tyrano"),
    BossID.SLASH_SWORD: ("Slash"),
    BossID.SON_OF_SUN: ("Son of Sun"),
    BossID.TERRA_MUTANT: ("Mutant"),
    BossID.YAKRA: ("Yakra"),
    BossID.YAKRA_XIII: ("Yakra"),
    BossID.ZOMBOR: ("Zombor"),

    BossID.MOTHER_BRAIN: ("Mother"),
    BossID.DRAGON_TANK: ("dragon"),
    BossID.GIGA_GAIA: ("GigaGaia"),
    BossID.GUARDIAN: ("Guardian"),
    BossID.OZZIE_TRIO: ("Ozzie"),
    BossID.ZEAL: ("Zeal"),
}
def get_abbrev_name(boss_id: BossID) -> tuple[str, str]:
    return _abbrev_name_dict.get(boss_id)


_arris_categories: dict[str: list[BossID]] = {
    "freaky mutants": [BossID.MEGA_MUTANT, BossID.GIGA_MUTANT, BossID.TERRA_MUTANT],
    "robot guards": [BossID.R_SERIES, BossID.MOTHER_BRAIN, BossID.GUARDIAN, BossID.DRAGON_TANK],
    "fancy folks": [BossID.ZEAL, BossID.DALTON, BossID.MAGUS_NORTH_CAPE, BossID.FLEA,
                    BossID.SLASH_SWORD, BossID.OZZIE_TRIO],
    # "crafty wizards": [BossID.ZEAL, BossID.DALTON, BossID.MAGUS_NORTH_CAPE, BossID.FLEA],
    "muscleheads": [BossID.MASA_MUNE, BossID.HECKRAN, BossID.NIZBEL, BossID.NIZBEL_2],
    "eyeball monsters": [BossID.RETINITE, BossID.SON_OF_SUN],
    "magical beasts": [BossID.GOLEM, BossID.GOLEM_BOSS, BossID.GIGA_GAIA, BossID.HECKRAN],
    "spiny beasts": [BossID.LAVOS_SPAWN, BossID.ELDER_SPAWN, BossID.YAKRA, BossID.YAKRA_XIII],
    "giant brutes": [BossID.GIGA_GAIA, BossID.RUST_TYRANO, BossID.ZOMBOR, BossID.RETINITE],
    "giant lizards": [BossID.NIZBEL, BossID.NIZBEL_2, BossID.RUST_TYRANO],
    "goofy goons": [BossID.OZZIE_TRIO, BossID.DALTON_PLUS],
    "boneheads": [BossID.ZOMBOR, BossID.RETINITE, BossID.OZZIE_TRIO],
}
def get_arris_categories() -> dict[str, list[BossID]]:
    return dict(_arris_categories)


_arris_name_dict: dict[BossID, str] = {
    BossID.DALTON: "Dalton",
    BossID.DALTON_PLUS: "crazy wizard",
    BossID.ELDER_SPAWN: "Spawn",
    BossID.FLEA: "Flea",
    BossID.GIGA_MUTANT: "freaky mutants",
    BossID.GOLEM: "Golem",
    BossID.GOLEM_BOSS: "Golem",
    BossID.HECKRAN: "Heckran",
    BossID.LAVOS_SPAWN: "Spawn",
    # BossID.MAMMON_M: "mammon_machine",
    BossID.MAGUS_NORTH_CAPE: "Magus",
    BossID.MASA_MUNE: "Masamune",
    BossID.MEGA_MUTANT: "freaky mutants",
    BossID.MUD_IMP: "Mud Imp",
    BossID.NIZBEL: "giant lizards",
    BossID.NIZBEL_2: "giant lizards",
    BossID.RETINITE: "eyeball monster",
    BossID.R_SERIES: "robot guards",
    BossID.RUST_TYRANO: ("giant lizards"),
    BossID.SLASH_SWORD: ("Slash"),
    BossID.SON_OF_SUN: ("eyeball monster"),
    BossID.TERRA_MUTANT: ("freaky mutants"),
    BossID.YAKRA: ("Yakra"),
    BossID.YAKRA_XIII: ("Yakra"),
    BossID.ZOMBOR: ("Zombor"),

    BossID.MOTHER_BRAIN: ("robot guards"),
    BossID.DRAGON_TANK: ("dragon"),
    BossID.GIGA_GAIA: ("GigaGaia"),
    BossID.GUARDIAN: ("robot guards"),
    BossID.OZZIE_TRIO: ("Ozzie"),
    BossID.ZEAL: ("Zeal"),
}
def get_abbrev_name(boss_id: BossID) -> tuple[str, str]:
    return _abbrev_name_dict.get(boss_id)


_alt_name_dict: dict[BossID, str] = {
    BossID.YAKRA_XIII: "Yakra XIII",
    BossID.MAGUS_NORTH_CAPE: "Magus",
}
def get_boss_dialogue_name(boss_id: BossID):
    name = boss_id.value.replace("_", " ")
    name = " ".join(x.capitalize() for x in name.split())
    return _alt_name_dict.get(boss_id, name)


def get_midboss_ids() -> list[BossID]:
    return [
        BossID.KRAWLIE, BossID.ATROPOS_XR, BossID.SUPER_SLASH,
        BossID.FLEA_PLUS, BossID.GATO, BossID.DALTON
    ]


def get_boss_ids() -> list[BossID]:
    midbosses = set(get_midboss_ids())

    return [boss_id for boss_id in BossID
            if boss_id not in midbosses]


class BossPart:
    """
    Data class for a single part of a boss: enemy id, slot, and displacement
    from primary part.
    """
    def __init__(self, enemy_id: ctenums.EnemyID = ctenums.EnemyID.NU,
                 slot: int = 3,
                 displacement: typing.Tuple[int, int] = (0, 0)):
        self.enemy_id = enemy_id
        self.slot = slot
        self.displacement = displacement

    def __str__(self):
        return f'BossPart: enemy_id={self.enemy_id}, slot={self.slot}, ' \
            f'disp={self.displacement}'


class BossScheme:
    """
    Essentially a list of BossParts with some methods for manipulating
    displacements.
    """
    def __init__(self, *parts: BossPart):
        self.parts = list(parts)

    def __str__(self):
        out_str = 'Boss Scheme:\n'
        for part in self.parts:
            out_str += '\t' + str(part) + '\n'

        return out_str

    def make_part_first(self, new_first_ind):
        """
        Makes the part with the given index first.  Relative order of other
        parts is unchanged.
        """
        self.parts[0], self.parts[new_first_ind] = \
            self.parts[new_first_ind], self.parts[0]

        disp_0 = self.parts[0].displacement
        for part in self.parts:
            cur_disp = part.displacement
            part.displacement = (cur_disp[0] - disp_0[0],
                                 cur_disp[1] - disp_0[1])

    def reorder_horiz(self, left: bool = True):
        """
        Move the leftmost (if left is True) or rightmost (otherwise) to the
        first spot
        """

        # expecting a value from enumerate(self.parts)
        def key_fn(val: tuple[int, BossPart]):
            return val[1].displacement[0]

        if left:
            x_extr = min(enumerate(self.parts), key=key_fn)
        else:
            x_extr = max(enumerate(self.parts), key=key_fn)

        extr_ind = x_extr[0]
        self.make_part_first(extr_ind)

    def flip_disps(self):
        """
        Flip a boss's orientation so that bosses like guardian can fit when
        they are located on the left/right edges of the screen.
        """

        for part in self.parts:
            part.displacement = (part.displacement[1], part.displacement[0])


_BS = BossScheme
_BP = BossPart
_EID = ctenums.EnemyID
_default_schemes: dict[BossID, BossScheme] = {
    BossID.ATROPOS_XR: _BS(_BP(_EID.ATROPOS_XR, 5)),
    BossID.BLACK_TYRANO: _BS(
        _BP(_EID.AZALA, 7),
        _BP(_EID.BLACKTYRANO, 3)  # Not real disp b/c not randomizing
    ),
    BossID.DALTON: _BS(_BP(_EID.DALTON, 3)),
    BossID.DALTON_PLUS: _BS(_BP(_EID.DALTON_PLUS, 3)),
    BossID.DRAGON_TANK: _BS(
        _BP(_EID.DRAGON_TANK, 3),
        _BP(_EID.TANK_HEAD, 9),
        _BP(_EID.GRINDER, 0xA)
    ),
    BossID.ELDER_SPAWN: _BS(
        _BP(_EID.ELDER_SPAWN_SHELL, 3),
        _BP(_EID.ELDER_SPAWN_HEAD, 9, (-8, 1))
    ),
    BossID.FLEA: _BS(_BP(_EID.FLEA, 7)),
    BossID.FLEA_PLUS: _BS(_BP(_EID.FLEA_PLUS, 7)),
    BossID.GATO: _BS(_BP(_EID.GATO, 6)),
    BossID.GIGA_GAIA: _BS(
        _BP(_EID.GIGA_GAIA_HEAD, 6),
        _BP(_EID.GIGA_GAIA_LEFT, 7, (0x30, 0x20)),
        _BP(_EID.GIGA_GAIA_RIGHT, 9, (-0x30, 0x20))
    ),
    BossID.GIGA_MUTANT: BossScheme(
        BossPart(_EID.GIGA_MUTANT_HEAD, 3),
        BossPart(_EID.GIGA_MUTANT_BOTTOM, 9)
    ),
    BossID.GOLEM: BossScheme(BossPart(_EID.GOLEM, 3)),
    BossID.GOLEM_BOSS: BossScheme(BossPart(_EID.GOLEM_BOSS, 3)),
    BossID.GUARDIAN: BossScheme(
        BossPart(_EID.GUARDIAN, 3),
        BossPart(_EID.GUARDIAN_BIT, 7, (-0x3A, -0x08)),
        BossPart(_EID.GUARDIAN_BIT, 8, (0x40, -0x08))
    ),
    BossID.HECKRAN: BossScheme(BossPart(_EID.HECKRAN, 3),),
    BossID.INNER_LAVOS: BossScheme(
        BossPart(_EID.LAVOS_2_HEAD, 0xA),
        BossPart(_EID.LAVOS_2_LEFT, 6, (-0x32, 0xE)),
        BossPart(_EID.LAVOS_2_RIGHT, 3, (0x32, 0xE))
    ),
    BossID.KRAWLIE: BossScheme(BossPart(_EID.KRAWLIE, 7)),
    BossID.LAVOS_CORE: BossScheme(  # Fake coords
        BossPart(_EID.LAVOS_3_CORE, 3),
        BossPart(_EID.LAVOS_3_LEFT, 7),
        BossPart(_EID.LAVOS_3_RIGHT, 9)
    ),
    BossID.LAVOS_SHELL: BossScheme(BossPart(_EID.LAVOS_OCEAN_PALACE, 5)),
    BossID.LAVOS_SPAWN: BossScheme(
        BossPart(_EID.LAVOS_SPAWN_SHELL, 3),
        BossPart(_EID.LAVOS_SPAWN_HEAD, 9, (-8, 0))
    ),
    BossID.MAMMON_M: BossScheme(BossPart(_EID.MAMMON_M, 3)),
    BossID.MASA_MUNE: BossScheme(BossPart(_EID.MASA_MUNE, 6)),
    BossID.MEGA_MUTANT: BossScheme(
        BossPart(_EID.MEGA_MUTANT_HEAD, 3),
        BossPart(_EID.MEGA_MUTANT_BOTTOM, 7)
    ),
    BossID.MAGUS: BossScheme(BossPart(_EID.MAGUS, 3)),
    BossID.MAGUS_NORTH_CAPE: BossScheme(BossPart(_EID.MAGUS_NORTH_CAPE, 3)),
    BossID.MOTHER_BRAIN: BossScheme(
        BossPart(_EID.MOTHERBRAIN, 3),
        BossPart(_EID.DISPLAY, 6, (-0x40, -0x0F)),  # (-0x50, -0x1F) Orig
        BossPart(_EID.DISPLAY, 7, (-0x08, -0x1F)),  # (-0x20, -0x2F) Orig
        BossPart(_EID.DISPLAY, 8, (0x38, -0x0F)),  # (-0x40, -0x1F) Orig
    ),
    BossID.MUD_IMP: BossScheme(
        BossPart(_EID.MUD_IMP, 9),
        BossPart(_EID.BLUE_BEAST, 3, (0x30, 0x10)),
        BossPart(_EID.RED_BEAST, 7, (0, 0x20))
    ),
    BossID.NIZBEL: BossScheme(BossPart(_EID.NIZBEL, 3)),
    BossID.NIZBEL_2: BossScheme(BossPart(_EID.NIZBEL_II, 3)),
    BossID.OZZIE_TRIO: BossScheme(
        BossPart(_EID.GREAT_OZZIE, 3),
        BossPart(_EID.SUPER_SLASH_TRIO, 7, displacement=(-0x20, 0x30)),
        BossPart(_EID.FLEA_PLUS_TRIO, 9, displacement=(0x20, 0x30))
    ),
    BossID.RETINITE: BossScheme(
        BossPart(_EID.RETINITE_EYE, 3),
        BossPart(_EID.RETINITE_TOP, 9, (0, -0x8)),
        BossPart(_EID.RETINITE_BOTTOM, 6, (0, 0x28))
    ),
    BossID.R_SERIES: BossScheme(
        BossPart(_EID.R_SERIES, 3),
        BossPart(_EID.R_SERIES, 4, (0, 0x40)),
        BossPart(_EID.R_SERIES, 7, (0x20, 0)),
        BossPart(_EID.R_SERIES, 8, (0x20, 0x40)),
        BossPart(_EID.R_SERIES, 9, (-0x20, 0)),
        BossPart(_EID.R_SERIES, 0xA, (-0x20, 0x40))
    ),
    BossID.RUST_TYRANO: BossScheme(BossPart(_EID.RUST_TYRANO,  3)),
    BossID.SLASH_SWORD: BossScheme(BossPart(_EID.SLASH_SWORD, 3)),
    BossID.SON_OF_SUN: BossScheme(
        BossPart(_EID.SON_OF_SUN_EYE, 3, (0, 0)),
        BossPart(_EID.SON_OF_SUN_FLAME, 4, (0x18, -0x7)),
        BossPart(_EID.SON_OF_SUN_FLAME, 5, (0xC, 0x17)),
        BossPart(_EID.SON_OF_SUN_FLAME, 6, (-0xC, 0x17)),
        BossPart(_EID.SON_OF_SUN_FLAME, 7, (-0x18, -0x7)),
        BossPart(_EID.SON_OF_SUN_FLAME, 8, (0, -0x17)),
    ),
    BossID.SUPER_SLASH: BossScheme(BossPart(_EID.SUPER_SLASH, 7)),
    BossID.TERRA_MUTANT: BossScheme(
        BossPart(_EID.TERRA_MUTANT_HEAD, 3),
        BossPart(_EID.TERRA_MUTANT_BOTTOM, 9)
    ),
    BossID.YAKRA: BossScheme(BossPart(_EID.YAKRA, 3)),
    BossID.YAKRA_XIII: BossScheme(BossPart(_EID.YAKRA_XIII, 3)),
    BossID.ZEAL: BossScheme(BossPart(_EID.ZEAL, 9)),
    BossID.ZEAL_2: BossScheme(
        BossPart(_EID.ZEAL_2_CENTER, 3),
        BossPart(_EID.ZEAL_2_LEFT, 6),  # Fake Coords
        BossPart(_EID.ZEAL_2_RIGHT, 9),  # Fake Coords
    ),
    BossID.ZOMBOR: BossScheme(
        BossPart(_EID.ZOMBOR_TOP, 9),
        BossPart(_EID.ZOMBOR_BOTTOM, 3, (0, 0x20))
    )
}


def get_default_scheme(boss_id: BossID) -> BossScheme:
    """
    Associate BossID with a scheme consistent with default JoT.
    """
    return copy.deepcopy(_default_schemes[boss_id])


def get_boss_data_dict() -> dict[BossID, BossScheme]:
    """
    Return the default BossScheme for each BossID
    """
    return copy.deepcopy(_default_schemes)


def get_default_boss_assignment() -> dict[BossSpotID, BossID]:
    """
    Provides the default assignment of BossSpotID -> BossID.
    """
    BSID = BossSpotID
    return {
        BSID.ARRIS_DOME: BossID.GUARDIAN,
        BSID.BLACK_OMEN_ELDER_SPAWN: BossID.ELDER_SPAWN,
        BSID.BLACK_OMEN_GIGA_MUTANT: BossID.GIGA_MUTANT,
        BSID.BLACK_OMEN_TERRA_MUTANT: BossID.TERRA_MUTANT,
        BSID.DEATH_PEAK: BossID.LAVOS_SPAWN,
        BSID.DENADORO_MTS: BossID.MASA_MUNE,
        BSID.EPOCH_REBORN: BossID.DALTON_PLUS,
        BSID.FACTORY_RUINS: BossID.R_SERIES,
        BSID.GENO_DOME_MID: BossID.ATROPOS_XR,
        BSID.GENO_DOME_FINAL: BossID.MOTHER_BRAIN,
        BSID.GIANTS_CLAW: BossID.RUST_TYRANO,
        BSID.HECKRAN_CAVE: BossID.HECKRAN,
        BSID.KINGS_TRIAL: BossID.YAKRA_XIII,
        BSID.MAGUS_CASTLE_FLEA: BossID.FLEA,
        BSID.MAGUS_CASTLE_SLASH: BossID.SLASH_SWORD,
        BSID.MANORIA_CATHERDAL: BossID.YAKRA,
        BSID.MT_WOE: BossID.GIGA_GAIA,
        BSID.OCEAN_PALACE_TWIN_GOLEM: BossID.GOLEM,
        BSID.OZZIES_FORT_FLEA_PLUS: BossID.FLEA_PLUS,
        BSID.OZZIES_FORT_SUPER_SLASH: BossID.SUPER_SLASH,
        BSID.PRISON_CATWALKS: BossID.DRAGON_TANK,
        BSID.REPTITE_LAIR: BossID.NIZBEL,
        BSID.SUN_PALACE: BossID.SON_OF_SUN,
        BSID.SUNKEN_DESERT: BossID.RETINITE,
        BSID.TYRANO_LAIR_NIZBEL: BossID.NIZBEL_2,
        BSID.ZEAL_PALACE: BossID.GOLEM,
        BSID.ZENAN_BRIDGE: BossID.ZOMBOR,
        BSID.BLACK_OMEN_ZEAL: BossID.ZEAL,
        BSID.OZZIES_FORT_TRIO: BossID.OZZIE_TRIO,
        BSID.NORTH_CAPE: BossID.MAGUS_NORTH_CAPE
    }


def get_minibosses() -> list[BossID]:
    return [BossID.ATROPOS_XR, BossID.GATO, BossID.SUPER_SLASH, BossID.FLEA_PLUS,
            BossID.DALTON, BossID.KRAWLIE]


def get_end_bosses() -> list[BossID]:
    return [
        BossID.MAMMON_M, BossID.ZEAL_2,
        BossID.LAVOS_CORE, BossID.LAVOS_SHELL, BossID.INNER_LAVOS,   # Hard Lavos?
    ]


def get_assignable_bosses() -> list[BossID]:
    minibosses = get_minibosses()
    endbosses = get_end_bosses()
    exclusions = minibosses + endbosses + [BossID.MAGUS_NORTH_CAPE, BossID.MAGUS, BossID.BLACK_TYRANO]
    return [
        BossID(x) for x in BossID if x not in exclusions
    ]
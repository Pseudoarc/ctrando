"""
Module for PCTech class and functions related to manipulating PCTechs.
"""
from __future__ import annotations
import copy
import functools
import io
import typing
from typing import Generator, Optional

from ctrando.asm import assemble
from ctrando.asm import instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.common import byteops, ctenums, ctrom, cttypes as cty, asmpatcher
from ctrando.strings import ctstrings
from ctrando.attacks import cttechtypes as ctt, pctechrefs


class TechNotFoundException(Exception):
    """Raise when trying to get a nonexistent tech"""


def get_menu_usable_list(ct_rom: ctrom.CTRom) -> list[int]:
    """
    Get a list of techs marked as usable in the menu.
    """
    hook_pos = 0x3FF82E

    rom_buf = ct_rom.getbuffer()
    hook_byte = rom_buf[hook_pos]

    if hook_byte == 0xA9:
        # Not expanded
        tech_list_start = 0x3FF830
    elif hook_byte == 0x22:
        # Expanded, starts with JSL
        rt_addr = byteops.file_ptr_from_rom(rom_buf, hook_pos+1)
        tech_list_start = rt_addr + 2
    else:
        raise ValueError("Could not read menu usable list from ct_rom.")

    # tech_list_start points to code that's just a list of instructions
    # TSB XX 77 which sets some bits in 0x7E77XX to mark tech XX as usable
    # in the menu.  TSB has opcode 0x0C.
    ret_list: list[int] = []
    cur_pos = tech_list_start
    while rom_buf[cur_pos] == 0x0C:
        ret_list.append(rom_buf[cur_pos+1])
        cur_pos += 3

    return ret_list


def get_menu_usable(ct_rom: ctrom.CTRom, tech_id: int) -> bool:
    """Determine if tech tech_id is usable in the menu."""
    return tech_id in get_menu_usable_list(ct_rom)


RockType = typing.Literal[
    ctenums.ItemID.BLUE_ROCK, ctenums.ItemID.BLACK_ROCK,
    ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
    ctenums.ItemID.GOLD_ROCK
]


def determine_rock_used(
        ct_rom: ctrom.CTRom, tech_id: int) -> typing.Optional[RockType]:
    """
    Determine which rock a tech needs.  Returns None if no rock is needed.
    """

    hook_pos = 0x0282F3
    hook_value = ct_rom.getbuffer()[hook_pos]

    rock_list: list[RockType] = [
        ctenums.ItemID.BLACK_ROCK, ctenums.ItemID.BLUE_ROCK,
        ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
        ctenums.ItemID.GOLD_ROCK
    ]

    if hook_value == 0x5C:
        # Is modified
        routine_addr = byteops.file_ptr_from_rom(ct_rom.getbuffer(), hook_pos+1)

        num_rock_techs = ctt.get_rock_tech_count(ct_rom)
        num_techs = ctt.get_total_tech_count(ct_rom)

        rock_tech_number = tech_id - (num_techs - num_rock_techs)
        if rock_tech_number < 0:
            return None

        # Otherwise, find rock_tech_number in the rock assignment table.

        # We use raw offsets into the routine to find the location of their
        # rock pointer table and the actual rock data.
        rock_table_ptr = routine_addr + 0x30
        rock_table_addr = byteops.file_ptr_from_rom(ct_rom.getbuffer(),
                                                    rock_table_ptr)

        # The rock table data is lexicographic order on (pc_id, rock_id)
        # Each entry is a 0xFF-terminated list of rock_tech_numbers.  So
        # We loop until we find the desired rock_tech_number and can % 5
        # to find which rock is used for that tech.
        ff_count = 0
        ct_rom.seek(rock_table_addr)
        while ff_count < 35:

            # This could be more efficient by reading chunks, but it's unlikely
            # to matter with how infrequently we call this.
            cur_byte = ct_rom.read(1)[0]

            if cur_byte == 0xFF:
                ff_count += 1
            elif cur_byte == rock_tech_number:
                rock_num = ff_count % 5
                return rock_list[rock_num]

        raise ValueError("No rock found for tech.")

    if hook_value == 0xA2:
        # Is vanilla
        num_techs = ctt.get_total_tech_count(ct_rom)
        first_rock_tech = num_techs - 5
        rock_num = tech_id - first_rock_tech

        if rock_num < 0:
            return None
        return rock_list[rock_num]

    raise ValueError("Unable to read rock data from rom.")


def get_pc_target_data(
        ct_rom: ctrom.CTRom, tech_id: int,
        tech_target_data: typing.Optional[ctt.PCTechTargetData] = None
) -> typing.Optional[ctenums.CharID]:
    """
    Determine whether a tech needs to target based on a particular PC index.
    When charrando is used, this needs to be updated.

    Notable Examples:
    - Doublevbomb targets around PC with index 3.
    - Black hole targets around PC with index 6.
    """

    hook_pos = 0x0122A9
    rom_buf = ct_rom.getbuffer()

    hook_byte = rom_buf[hook_pos]

    if hook_byte == 0xBD:
        # Unmodified
        # Determine pc target data from normal tech target data.
        if tech_target_data is None:
            tech_target_data = ctt.PCTechTargetData.read_from_ctrom(ct_rom, tech_id)

        target_type = tech_target_data.select_target
        if target_type == ctt.TargetType.AREA_MAGUS:
            return ctenums.CharID.MAGUS
        if target_type in (ctt.TargetType.LINE_ROBO,
                           ctt.TargetType.AREA_ROBO_13,
                           ctt.TargetType.AREA_ROBO_14):
            return ctenums.CharID.ROBO
        return None
    if hook_byte == 0x5C:
        # Modified
        # Determine pc targt data from special range on rom
        rt_start = byteops.file_ptr_from_rom(rom_buf, hook_pos+1)
        rt_offset = 5
        target_table_start = byteops.file_ptr_from_rom(rom_buf,
                                                       rt_start + rt_offset)
        target_byte = rom_buf[target_table_start + tech_id]

        if target_byte == 0xFF:
            return None
        return ctenums.CharID(target_byte)

    raise ValueError("Could not parse rom target routine.")


class PCAttack:
    """
    Class to store data of a PC's basic attack.
    Presently, only stores data that gets lumped with tech data
    """

    def __init__(
            self,
            control_header: Optional[ctt.PCTechControlHeader] = None,
            effect_header: Optional[ctt.PCTechEffectHeader] = None
    ):
        if control_header is None:
            control_header = ctt.PCTechControlHeader()
        self.control_header = control_header.get_copy()

        if effect_header is None:
            effect_header = ctt.PCTechEffectHeader()
        self.effect_header = effect_header.get_copy()

    @classmethod
    def read_from_ct_rom(cls, ct_rom: ctrom.CTRom, pc_id: ctenums.CharID):
        """
        Read attack data for a given character from the ct_rom
        """

        control_index = ctt.get_total_tech_count(ct_rom) + pc_id
        control = ctt.PCTechControlHeader.read_from_ctrom(ct_rom, control_index)

        effect_index = control.get_effect_index(0)
        effect = ctt.PCTechEffectHeader.read_from_ctrom(ct_rom, effect_index)

        return PCAttack(control, effect)


class PCTech:
    """
    Class to store all data needed by a tech.

    Most of this is straightforward, but there are three dc-flag specific
    fields that are included.
    - rock_used: With dc the rock -> tech association can not be determined
        from the tech_id.  This needs to be given explicitly.
    - menu_usable:  With dc, there can be many (or no) techs which are usable
        in the menu.
    - pc_target: Some techs target a particular CharID (e.g. Doublevbomb).
        The target needs to be tracked explicitly for dc flag when there may
        be multiple of the same character in a fight.
    """

    def __init__(
            self,
            battle_group: ctt.PCTechBattleGroup,
            control_header: ctt.PCTechControlHeader,
            effect_headers: list[ctt.PCTechEffectHeader],
            effect_mps: list[int],
            menu_mp_reqs: typing.Optional[ctt.PCTechMenuMPReq],
            graphics_header: ctt.PCTechGfxHeader,
            target_data: ctt.PCTechTargetData,
            learn_reqs: typing.Optional[ctt.PCTechLearnRequirements],
            name: ctstrings.CTNameString,
            desc: ctstrings.CTString,
            atb_penalty: ctt.PCTechATBPenalty,
            rock_used: typing.Optional[RockType],
            menu_usable: bool,
            pc_target: typing.Optional[ctenums.CharID]
    ):
        self.battle_group = battle_group.get_copy()
        self.control_header = control_header.get_copy()
        self.graphics_header = graphics_header.get_copy()
        self.target_data = target_data.get_copy()
        self.learn_reqs: typing.Optional[ctt.PCTechLearnRequirements] = ctt.PCTechLearnRequirements()
        self.atb_penalty = atb_penalty.get_copy()
        self.rock_used = rock_used
        self.menu_usable = menu_usable
        self.pc_target = pc_target

        if learn_reqs is not None:
            self.learn_reqs = learn_reqs.get_copy()
        else:
            self.learn_reqs = None

        self.menu_mp_reqs: typing.Optional[ctt.PCTechMenuMPReq] = None
        if menu_mp_reqs is not None:
            self.menu_mp_reqs = menu_mp_reqs.get_copy()

        self._name = ctstrings.CTNameString(name)
        self._desc = ctstrings.CTString(desc)

        self.effect_headers: list[ctt.PCTechEffectHeader] = []
        self.effect_mps: list[int] = []

        # Make sure that everything is sized correctly.
        num_pcs = battle_group.number_of_pcs
        if len(effect_headers) != num_pcs:
            raise ValueError('Number of PCs and effect headers differs')

        if len(effect_mps) != num_pcs:
            raise ValueError('Number of PCs and mps differs')

        if len(atb_penalty) == 1 and num_pcs not in (1, 2):
            raise ValueError("Number of PCs and atb penalties differs.")
        if len(atb_penalty) == 2 and num_pcs != 3:
            raise ValueError("Number of PCs and atb penalties differs.")

        if menu_mp_reqs is None and num_pcs != 1:
            raise ValueError('Number of PCs and menu mp requirements differs')
        if menu_mp_reqs is not None and len(menu_mp_reqs) != num_pcs:
            raise ValueError('Number of PCs and menu mp requirements differs')

        for effect_header, mp in zip(effect_headers, effect_mps):
            self.effect_headers.append(effect_header)
            self.effect_mps.append(mp)

    @property
    def name(self) -> str:
        """This tech's name as a string."""
        return str(self._name)

    @name.setter
    def name(self, val: str):
        new_name = ctstrings.CTNameString.from_string(val, length=0xB)
        self._name = new_name

    @property
    def desc(self) -> str:
        """This tech's description as a string."""
        return str(self._desc)

    @desc.setter
    def desc(self, val: str):
        new_desc = ctstrings.CTString.from_str(val, compress=True)
        self._desc = new_desc

    @property
    def num_pcs(self) -> int:
        """The number of PCs who perform this tech."""
        return self.battle_group.number_of_pcs

    @property
    def needs_magic_to_learn(self):
        """Does this tech need magic to learn (single only)"""
        if self.num_pcs != 1:
            raise TypeError("Combo techs don't need magic to learn")

        return self.control_header[0] & 0x80

    @needs_magic_to_learn.setter
    def needs_magic_to_learn(self, val: bool):
        if self.num_pcs != 1:
            raise TypeError("Combo techs don't need magic to learn")

        self.control_header[0] &= 0x7F
        self.control_header[0] |= 0x80*(val is True)

    @property
    def is_unlearnable(self):
        """Can this tech be learned (combo tech only)."""
        if self.num_pcs == 1:
            raise TypeError("Single techs cannot be marked unlearnable.")

        return self.control_header[0] & 0x80

    @is_unlearnable.setter
    def is_unlearnable(self, val: bool):
        if not self.num_pcs == 1:
            raise TypeError("Single techs cannot be marked unlearnable.")

        self.control_header[0] &= 0x7F
        self.control_header[0] |= 0x80*(val is True)

    def get_menu_mp_requirement(self, pc_id: ctenums.CharID):
        """
        Get the Menu MP requirement for a given PC.
        """

        if pc_id not in self.battle_group:
            raise ValueError

        return next(req for req in self.menu_mp_reqs if (req - 1) // 8 == pc_id)

    def set_menu_mp_requirement(self, pc_id: ctenums.CharID, tech_id: ctenums.TechID):
        """
        Sets Menu MP.  Must be a tech in the single tech range.
        """

        if not (1+pc_id*8 <= tech_id < 1+(pc_id+1)*8):
            raise ValueError("Menu MP must be one of the character's single techs.")

        if self.menu_mp_reqs is None:
            raise TypeError("Tech has no Menu MP Requirements")

        pc_mmp_ind = next(
            ind for ind, val in enumerate(self.menu_mp_reqs) if (val-1) // 8 == pc_id
        )
        self.menu_mp_reqs[pc_mmp_ind] = tech_id

    def get_learn_requirement(self, pc_id: ctenums.CharID):
        """
        Get the required tech level for pc_id for the combo tech to be learned.
        """

        if self.num_pcs == 1 or self.rock_used is not None:
            raise TypeError("Only non-rock combo techs have learn requirements")

        learn_ind = sorted(self.battle_group).index(pc_id)
        return self.learn_reqs[learn_ind]

    def set_learn_requirement(self, pc_id: ctenums.CharID, learn_req: int | ctenums.TechID):
        """
        Set the required tech level for pc_id for the combo tech to be learned.
        """

        if self.num_pcs == 1 or self.rock_used is not None:
            raise TypeError("Only non-rock combo techs have learn requirements")

        if isinstance(learn_req, ctenums.TechID):
            learn_req = ((learn_req - 1) % 8) + 1

        if not (1 <= learn_req <= 8):
            raise ValueError("The learn requirement must be in [1, 8]")

        learn_ind = sorted(self.battle_group).index(pc_id)
        self.learn_reqs[learn_ind] = learn_req

    @classmethod
    def read_from_ctrom(
            cls, ct_rom: ctrom.CTRom, tech_id: int,
            lrn_req_rw: typing.Optional[cty.RomRW] = None,
            atb_pen_rw: typing.Optional[cty.RomRW] = None
            ) -> PCTech:
        """
        Read the PCTech with a given tech id from a ctrom.CTRom.

        If reading many techs, it may be more efficient to compute the
        cttypes.RomRW objects for learning requirements and atb penalties
        since these involve some computations.  These can be provided with
        optional arguments lrn_req_rw and atb_pen_rw.
        """
        control_header = ctt.PCTechControlHeader.read_from_ctrom(ct_rom, tech_id)

        battle_group_index = control_header.battle_group_id
        battle_group = ctt.PCTechBattleGroup.read_from_ctrom(ct_rom, battle_group_index)

        eff_inds = [control_header.get_effect_index(eff_num)
                    for eff_num in range(battle_group.number_of_pcs)]
        effect_headers = [
            ctt.PCTechEffectHeader.read_from_ctrom(ct_rom, eff_ind)
            for eff_ind in eff_inds
        ]

        effect_mps = [
            int(ctt.PCEffectMP.read_from_ctrom(ct_rom, eff_ind)[0])
            for eff_ind in eff_inds
        ]

        graphics_header = ctt.PCTechGfxHeader.read_from_ctrom(ct_rom, tech_id)

        target_data = ctt.PCTechTargetData.read_from_ctrom(ct_rom, tech_id)

        if battle_group.number_of_pcs > 1:
            if lrn_req_rw is None:
                lrn_req_rw = ctt.PCTechLearnRequirements.ROM_RW

            # There are always 0x39 single tech entries: 1 fake +
            # 7*8 singles.
            lrn_req_index = tech_id - 0x39
            learn_reqs = ctt.PCTechLearnRequirements.read_from_ctrom(ct_rom, lrn_req_index, lrn_req_rw)
        else:
            learn_reqs = None

        if battle_group.number_of_pcs > 1:
            menu_mps = ctt.PCTechMenuMPReq.read_from_ctrom(ct_rom, tech_id)
        else:
            menu_mps = None

        name = ctt.read_tech_name_from_ctrom(ct_rom, tech_id)
        desc = ctt.read_tech_desc_from_ctrom(ct_rom, tech_id)

        if atb_pen_rw is None:
            num_dual_techs = ctt.get_dual_tech_count(ct_rom)
            num_triple_techs = ctt.get_triple_tech_count(ct_rom)
            atb_pen_rw = ctt.PCTechATBPenaltyRW(num_dual_techs, num_triple_techs)

        if battle_group.number_of_pcs == 3:
            num_atb_bytes = 2
        else:
            num_atb_bytes = 1

        atb_penalty = ctt.PCTechATBPenalty.read_from_ctrom(ct_rom, tech_id, atb_pen_rw)

        rock_used = determine_rock_used(ct_rom, tech_id)
        menu_usable = get_menu_usable(ct_rom, tech_id)
        pc_target = get_pc_target_data(ct_rom, tech_id, target_data)

        return PCTech(battle_group, control_header, effect_headers,
                      effect_mps, menu_mps, graphics_header, target_data,
                      learn_reqs, name, desc, atb_penalty, rock_used,
                      menu_usable, pc_target)


TechList = typing.List[typing.Optional[PCTech]]


class PCTechManagerGroup:
    """
    Class used internally by PCTechManager to store groups of techs.

    PCTechManagerGroup has no public-facing members.  The only changes to
    instances of the class should be made to self._techs through the
    add_tech and set_tech methods.
    """
    _pc_bitmask: typing.ClassVar[dict[ctenums.CharID, int]] = {
        ctenums.CharID.CRONO: 0x80,
        ctenums.CharID.MARLE: 0x40,
        ctenums.CharID.LUCCA: 0x20,
        ctenums.CharID.ROBO: 0x10,
        ctenums.CharID.FROG: 0x08,
        ctenums.CharID.AYLA: 0x04,
        ctenums.CharID.MAGUS: 0x02,
    }

    def __init__(self, bitmask: int,
                 rock_used: typing.Optional[RockType] = None,
                 techs: typing.Optional[TechList] = None):

        self._rock_used = rock_used

        if bitmask not in range(1, 0x100):
            raise ValueError("Bitmask must be i range(1x100)")

        if bool(bitmask & 0x01):
            raise ValueError("Bit 0x01 does not correspond to a PC.")

        self._bitmask = bitmask
        self._num_pcs = bin(self.bitmask).count('1')

        if self.num_pcs not in range(1, 4):
            raise ValueError(
                f"Bitmask 0x{self.bitmask:02X} must only have 1, 2 or 3 "
                "bytes set."
            )

        self._num_techs = (
            8 if self.num_pcs == 1 else (
                3 if self.num_pcs == 2 else 1
            )
        )

        self._techs: TechList = []
        if techs is None:
            self._techs = [None for _ in range(self.num_techs)]
        else:
            if len(techs) != self.num_techs:
                raise ValueError(
                    "Size of parameter techs inconsistent with number of PCs."
                )
            for tech in techs:
                self._validate_tech(tech)

            self._techs = techs

    def get_all_techs(self) -> TechList:
        """Get the internal list of techs (not a copy)."""
        return self._techs

    def has_tech(self, index: int) -> bool:
        """Is there a tech at the given index."""
        return self._techs[index] is not None

    def get_tech(self, index: int) -> PCTech:
        """
        Get the tech at the given index.

        Raises TechNotFoundException if there is none."""
        tech = self._techs[index]
        if tech is None:
            raise TechNotFoundException

        return tech

    def has_free_space(self) -> bool:
        """Does this group have any free space."""
        return None in self._techs

    def add_tech(self, tech: PCTech) -> int:
        """Add a tech to this group.  Returns the insertion index."""
        if None not in self._techs:
            raise IndexError(f"No room in group {self._bitmask:02X}.")

        insertion_index = self._techs.index(None)
        self.set_tech(insertion_index, tech)
        return insertion_index

    def set_tech(self, index: int, tech: typing.Optional[PCTech]):
        """Add a tech to this group at a particular index."""
        self._validate_tech(tech)
        self._techs[index] = tech

    def _validate_tech(self, tech: typing.Optional[PCTech]) -> None:
        """
        Verify that a tech belongs in this group.  Raises ValueError on
        failure.
        """
        if tech is not None:
            if tech.battle_group.to_bitmask() != self._bitmask:
                raise ValueError(
                    "Tech bitmask does not match group bitmask"
                )
            if tech.rock_used != self._rock_used:
                raise ValueError(
                    "Tech rock usage does not match group rock usage."
                )

    @classmethod
    def bitmask_from_pcs(
            cls, *pcs: ctenums.CharID
    ) -> int:
        """Create a bitmask from ctenums.CharIDs."""
        if isinstance(pcs, ctenums.CharID):
            pcs = [pcs]

        bitmask = functools.reduce(
            lambda x, y: x | y, (cls._pc_bitmask[char] for char in pcs), 0
        )
        return bitmask

    @classmethod
    def from_pcs(cls, *pcs: ctenums.CharID,
                 rock_used: typing.Optional[RockType] = None,
                 techs: typing.Optional[list[typing.Optional[PCTech]]] = None
                 ) -> PCTechManagerGroup:
        """Create a PCTechManagerGroup from ctenums.CharIDs."""
        return cls(cls.bitmask_from_pcs(*pcs), rock_used=rock_used,
                   techs=techs)

    @property
    def bitmask(self) -> int:
        """Get the bitmask associated with this group."""
        return self._bitmask

    @property
    def pcs(self) -> list[ctenums.CharID]:
        """Get a list of CharIDs in this group."""
        return [
            char_id for char_id in ctenums.CharID
            if bool(self._pc_bitmask[char_id] & self.bitmask)
        ]

    @property
    def rock_used(self) -> typing.Optional[RockType]:
        """Get the rock used by this group."""
        return self._rock_used

    @property
    def num_pcs(self) -> int:
        """Get how many pcs are in this group's bitmask."""
        return self._num_pcs

    @property
    def num_techs(self) -> int:
        """Get how many techs this group can hold."""
        return self._num_techs


class PCTechManager:
    """Handle all PC tech data."""

    def __init__(self, techs: typing.Optional[typing.Iterable[PCTech]] = None):
        """
        Construct a PCTechManager from a collection of PCTechs.

        Note that the iteration order of the techs parameter matters.
        The first Crono tech encountered while iterating will be Crono's first
        tech
        """

        # self._bitmasks stores raw int bitmasks in an order that CT likes.
        self._bitmasks: list[int] = []

        # Associate bitmask with PCTechManagerGroup (num_techs, rock_used)
        # This is especially important for triple vs rock to prevent
        # re-definition of a bitmask.
        self._bitmask_group_dict: dict[int, PCTechManagerGroup] = {}

        # Needed for identifying by tech_id.
        self.__num_dual_groups = 0
        self.__num_triple_groups = 0  # not including rock techs
        self.__num_rock_groups = 0

        self._attack_dict: dict[ctenums.CharID, PCAttack] = {}

        # Add the single tech groups in a particular order.
        # just char_id in ctenums.CharID should work, but be explicit.
        for char_id in (ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                        ctenums.CharID.LUCCA, ctenums.CharID.ROBO,
                        ctenums.CharID.FROG, ctenums.CharID.AYLA,
                        ctenums.CharID.MAGUS):
            group = PCTechManagerGroup.from_pcs(char_id, rock_used=None)
            self._bitmasks.append(group.bitmask)
            self._bitmask_group_dict[group.bitmask] = group
            self._attack_dict[char_id] = PCAttack()

        if techs is not None:
            for tech in techs:
                self.add_tech(tech)

    @property
    def num_single_techs(self) -> int:
        """The number of single techs in this class."""
        return 56

    @property
    def num_dual_techs(self) -> int:
        """The number of dual techs in this class."""
        return self.__num_dual_groups*3

    @property
    def num_triple_techs(self) -> int:
        """The number of triple techs in this class."""
        return self.__num_triple_groups

    @property
    def num_rock_techs(self) -> int:
        """The number of rock techs in this class."""
        return self.__num_rock_groups

    @property
    def num_techs(self) -> int:
        return self.num_single_techs + self.num_dual_techs + \
            self.num_triple_techs + self.num_rock_techs

    def get_attack(self, char_id: ctenums.CharID) -> PCAttack:
        """
        Returns a character's attack data
        """
        return copy.deepcopy(self._attack_dict[char_id])

    def set_attack(self, char_id: ctenums.CharID, attack: PCAttack):
        """
        Set a character's attack data
        """
        self._attack_dict[char_id] = copy.deepcopy(attack)

    def add_tech(self, tech: PCTech) -> int:
        """
        Adds a tech and returns the tech_id where it is inserted.

        Note: the tech_id may change with future tech insertions.
        """
        bitmask = tech.battle_group.to_bitmask()
        rock_used = tech.rock_used

        bitmask_index = self._add_bitmask(bitmask, rock_used)
        group = self._bitmask_group_dict[bitmask]
        tech_index = group.add_tech(tech)

        return self._get_tech_id(bitmask_index, tech_index)

    def test_effect_dependencies(self, effect_index):
        pc_id = ctenums.CharID((effect_index-1) // 8)
        tech_num = (effect_index - 1) % 8
        target_learn_req = tech_num + 1
        target_mmp = effect_index
        pc_bitmask = 0x80 >> pc_id
        tech = self._bitmask_group_dict[pc_bitmask].get_tech(tech_num)

        for bitmask in self._bitmasks[8:]:
            if bitmask & pc_bitmask == 0:
                continue

            for grp_tech in self._bitmask_group_dict[bitmask].get_all_techs():
                bat_ind = grp_tech.battle_group.index(pc_id)
                pc_effect_ind = grp_tech.control_header.get_effect_index(bat_ind)
                if pc_effect_ind == effect_index:
                    # grp_tech.effect_headers[bat_ind] = tech.effect_headers[0]
                    # grp_tech.effect_mps[bat_ind] = tech.effect_mps[0]

                    print(f"{grp_tech.name} uses {tech.name} as an effect")

                if grp_tech.rock_used is None and grp_tech.get_learn_requirement(pc_id) == target_learn_req:
                    print(f"{grp_tech.name} uses {tech.name} as a requirement")

                if target_mmp in grp_tech.menu_mp_reqs:
                    print(f"{grp_tech.name} uses {tech.name} as a menu requirement")


    def set_tech_by_id(self, tech: PCTech, tech_id: int):
        """
        Set tech based on tech_id (may not be fixed as techs are added).
        """

        bitmask = tech.battle_group.to_bitmask()
        group = self._bitmask_group_dict[bitmask]
        start_tech_id = self._get_tech_id(self._bitmasks.index(bitmask), 0)
        if not start_tech_id <= tech_id < start_tech_id+group.num_techs:
            raise ValueError("tech_id is not in tech's group")

        group_index = tech_id - start_tech_id
        self.set_tech(tech, group_index)


    def set_tech(self, tech: PCTech, index_in_group: int):
        """
        Insert a tech as a particular tech in its group.
        """

        tech_bitmask = tech.battle_group.to_bitmask()
        group = self._bitmask_group_dict[tech_bitmask]
        group.set_tech(index_in_group, tech)

        # # If setting a single tech, update the effect headers of derived combo techs
        # if group.num_pcs == 1:
        #     pc_id = ctenums.CharID(tech.battle_group[0])
        #     effect_index = 1 + self._bitmasks.index(tech_bitmask)*8 + index_in_group
        #     target_learn_req = index_in_group + 1
        #
        #     for bitmask in self._bitmasks[8:]:
        #         if bitmask & tech_bitmask == 0:
        #             continue
        #
        #         for grp_tech in self._bitmask_group_dict[bitmask].get_all_techs():
        #             bat_ind = grp_tech.battle_group.index(pc_id)
        #             pc_effect_ind = grp_tech.control_header.get_effect_index(bat_ind)
        #             if pc_effect_ind == effect_index:
        #                 grp_tech.effect_headers[bat_ind] = tech.effect_headers[0]
        #                 grp_tech.effect_mps[bat_ind] = tech.effect_mps[0]
        #
        #                 print(f"{grp_tech.name} uses {tech.name} as an effect")
        #
        #             if grp_tech.get_learn_requirement(pc_id) == target_learn_req:
        #                 print(f"{grp_tech.name} uses {tech.name} as a requirement")


    def reorder_single_techs(
            self,
            pc_id: ctenums.CharID,
            permutation: list[int],
            preserve_magic: bool = True
    ):
        """
        Reorder a PC's single techs and update all combo techs to use
        the new order.
        """

        if sorted(permutation) != list(range(8)):
            raise ValueError("Invalid Permutation")
        inverse_perm = [permutation.index(ind) for ind in range(8)]

        char_bitmask = ctt.PCTechBattleGroup.from_charids([pc_id]).to_bitmask()
        group = self._bitmask_group_dict[char_bitmask]

        reordered_techs = [
            copy.deepcopy(group.get_tech(permutation[ind]))
            for ind in range(8)
        ]

        if preserve_magic:
            for ind, tech in enumerate(reordered_techs):
                tech.control_header[0] = group.get_tech(ind).control_header[0]

        new_group = PCTechManagerGroup(char_bitmask, None, reordered_techs)
        self._bitmask_group_dict[char_bitmask] = new_group

        first_tech_id = 1 + 8*pc_id
        end_tech_id = first_tech_id + 8

        def get_reindexed_value(value: int):
            if first_tech_id <= value < end_tech_id:
                orig_tech_number = value - first_tech_id
                new_tech_number = inverse_perm[orig_tech_number]
                return first_tech_id + new_tech_number

            return value

        for bitmask in self._bitmasks[7:]:  # Skip single techs
            if char_bitmask & bitmask == 0:
                continue

            for tech in self._bitmask_group_dict[bitmask].get_all_techs():
                if tech is None:
                    continue
                pc_index = tech.battle_group.index(pc_id)
                effect_index = tech.control_header.get_effect_index(pc_index)
                new_effect_index = get_reindexed_value(effect_index)
                tech.control_header.set_effect_index(pc_index, new_effect_index)

                for ind, mmp in enumerate(tech.menu_mp_reqs):
                    tech.menu_mp_reqs[ind] = get_reindexed_value(tech.menu_mp_reqs[ind])

                if tech.rock_used is None:
                    old_learn_req = tech.get_learn_requirement(pc_id) - 1
                    new_learn_req = inverse_perm[old_learn_req] + 1
                    tech.set_learn_requirement(pc_id, new_learn_req)

    def get_tech(self, tech_id) -> PCTech:
        """
        Get (a copy of) the PCTech with the given tech_id.

        Notes:
        - Will raise IndexError if the given tech_id is out of range.
        - Will raise TechNotFoundException if the given tech_id is valid but
          has no PCTech associated with it.
        - Follows Chrono Trigger's tech_id system where Crono's first tech has
          an id of 1 (not 0).  Requesting tech_id=0 will raise an IndexError
        """

        if tech_id == 0:
            raise IndexError("Player Techs begin at tech_id 1")

        tech_id -= 1
        tech_counts = [self.num_single_techs, self.num_dual_techs,
                       self.num_triple_techs, self.num_rock_techs]

        if tech_id > sum(tech_counts):
            raise IndexError("tech_id out of range.")

        group_counts = [7, self.__num_dual_groups,
                        self.__num_triple_groups, self.__num_rock_groups]
        group_sizes = [8, 3, 1, 1]

        group_start = 0
        tech_start = 0

        group_index, tech_index = None, None
        for tech_count, group_count, group_size in (
                zip(tech_counts, group_counts, group_sizes)
        ):
            if tech_id < tech_start + tech_count:
                tech_id -= tech_start
                group_index = group_start + tech_id // group_size
                tech_index = tech_id % group_size
                break

            tech_start += tech_count
            group_start += group_count

        if group_index is None or tech_index is None:
            raise TechNotFoundException(
                "Failed to find tech group.")  # Should never happen.

        bitmask = self._bitmasks[group_index]
        group = self._bitmask_group_dict[bitmask]
        tech = group.get_tech(tech_index)  # May raise TechNotFoundException

        return copy.deepcopy(tech)

    def get_all_techs(self) -> dict[int, Optional[PCTech]]:
        """
        Returns a dictionary of copies of the currently assigned techs indexed
        by their tech index (CT 1-index)
        """

        ret_dict: dict[int, Optional[PCTech]] = {}

        tech_id = 1
        for bitmask in self._bitmasks:
            for tech in self._bitmask_group_dict[bitmask].get_all_techs():
                if tech is not None:
                    ret_dict[tech_id] = copy.deepcopy(tech)
                tech_id += 1

        return ret_dict

    def _get_tech_id(self, bitmask_index, tech_list_index):
        """
        Internal method to determine a tech's tech_id from the index of its
        bitmask and it's index within its group.

        Note: This uses CT's 1-indexing of techs rather than the usual 0.
        """
        if bitmask_index < 7:
            return 1 + 8*bitmask_index + tech_list_index

        start_tech_index = 7*8
        start_group_index = 7
        if bitmask_index < start_group_index + self.__num_dual_groups:
            dual_index = bitmask_index - start_group_index
            return start_tech_index + dual_index*3 + tech_list_index + 1

        start_tech_index += self.__num_dual_groups*3
        start_group_index += self.__num_dual_groups

        if tech_list_index != 0:
            print(self.__num_dual_groups, self.__num_triple_groups)
            raise ValueError("Triple groups have only one tech")

        if bitmask_index < start_group_index + self.__num_triple_groups:
            triple_index = bitmask_index - start_group_index
            return start_tech_index + triple_index + 1

        start_tech_index += self.__num_triple_groups
        start_group_index += self.__num_triple_groups

        rock_index = bitmask_index - start_group_index
        return start_tech_index + rock_index + 1

    def _add_bitmask(self, bitmask: int,
                     rock_used: typing.Optional[RockType]) -> int:
        if bitmask in self._bitmasks:
            return self._bitmasks.index(bitmask)

        group = PCTechManagerGroup(bitmask, rock_used)

        # Insert bitmask in order
        if group.num_pcs == 2:
            insertion_index = 7 + self.__num_dual_groups
        elif group.num_pcs == 3:
            insertion_index = 7 + self.__num_dual_groups + \
                self.__num_triple_groups
            if group.rock_used is not None:
                insertion_index += self.__num_rock_groups
        else:
            raise ValueError(
                f"Adding a single tech group {group.bitmask:02X}."
            )

        self._bitmasks.insert(insertion_index, bitmask)
        self._bitmask_group_dict[bitmask] = group

        # Maybe this could go up during computation of insertion_index,
        # but it feels wrong to increment until the group is actually in.
        if group.num_pcs == 2:
            self.__num_dual_groups += 1
        elif group.rock_used is None:
            self.__num_triple_groups += 1
        else:
            self.__num_rock_groups += 1

        self._bitmask_group_dict[group.bitmask] = group

        return insertion_index

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom):
        """Read techs into a PCTechManager from a ctrom.CTRom."""
        num_techs = ctt.get_total_tech_count(ct_rom)  # Includes dummy tech0

        tech_man = PCTechManager()
        for tech_id in range(1, num_techs):
            tech = PCTech.read_from_ctrom(ct_rom, tech_id)
            tech_man.add_tech(tech)

        for pc_id in ctenums.CharID:
            tech_man.set_attack(pc_id, PCAttack.read_from_ct_rom(ct_rom, pc_id))

        return tech_man

    def _verify_battle_groups(
            self,
            battle_groups: list[ctt.PCTechBattleGroup]) -> None:
        for bitmask in self._bitmasks:
            for tech in self._bitmask_group_dict[bitmask].get_all_techs():
                if tech is None:
                    continue
                    # raise ValueError(f"Unset tech in group {bitmask:02X}")

                if tech.battle_group != \
                   battle_groups[tech.control_header.battle_group_id]:
                    raise ValueError("Battle Group Mismatch")

    def _collect_update_battle_groups(self) -> bytes:
        """
        Returns a bytes object consisting of all battle groups in order.

        Warning: This has side effects.  All control headers will be updated
                 to use the correct battle_group_id.
        """

        # One battle group per bitmask is forced by CT.
        # Get each group's 0th tech's battle group.  So group i's forced
        # group is in position i in the list.
        first_techs: typing.Iterator[PCTech] = (
            self._bitmask_group_dict[bitmask].get_tech(0)
            for bitmask in self._bitmasks
        )

        battle_groups: list[ctt.PCTechBattleGroup] = [
            tech.battle_group for tech in first_techs
        ]

        for bitmask_ind, bitmask in enumerate(self._bitmasks):
            # Get all techs but the first, and add their battle groups
            # Also, re-order MMP relative the representative battle group
            group_techs =\
                self._bitmask_group_dict[bitmask].get_all_techs()
            for tech in group_techs:
                if tech is None:
                    tech = copy.deepcopy(group_techs[0])
                    tech.control_header[0] |= 0x80
                    # raise ValueError(f"Undefined Tech in group {bitmask:02X}")

                if tech.battle_group == battle_groups[bitmask_ind]:
                    new_battle_index = bitmask_ind
                else:
                    new_battle_index = len(battle_groups)
                    battle_groups.append(tech.battle_group)

                # Note to self:
                #   MMP are in representative battle group order for duals
                #   MMP are in pc-id order for triples.
                if tech.num_pcs ==2 and tech.menu_mp_reqs is not None:
                    new_mmp = sorted(
                        tech.menu_mp_reqs,
                        key=lambda x: battle_groups[bitmask_ind].index((x-1)//8)
                    )
                    tech.menu_mp_reqs = ctt.PCTechMenuMPReq(new_mmp)

                tech.control_header.battle_group_id = new_battle_index

        self._verify_battle_groups(battle_groups)
        battle_group_bytes = \
            b''.join(bytes(group) for group in battle_groups)

        return battle_group_bytes

    def _collect_update_effect_headers_and_mps(self) -> tuple[bytes, bytes]:
        """
        Returns bytes for the techs effect headers.

        Warning: This has side effects.  All control headers will be updated
                 to use the correct effect indices.
        """

        # begin with an empty header for effect 0 and 0 MP cost
        effect_headers: list[ctt.PCTechEffectHeader] = [
            ctt.PCTechEffectHeader()
        ]
        effect_mps = bytearray(1)

        # Single techs go in order.  self._bitmasks are in the right order
        # So the single techs are the first 7 bitmasks.
        for bitmask in self._bitmasks[0:7]:
            group = self._bitmask_group_dict[bitmask]
            if group.num_pcs != 1:
                raise ValueError("Expected single tech group")
            for ind in range(group.num_techs):
                tech = group.get_tech(ind)
                effect_headers.append(tech.effect_headers[0])
                effect_mps.append(tech.effect_mps[0])
                tech.control_header.set_effect_index(0, len(effect_headers)-1)

        # Now add basic attacks (mimic vanilla)
        for attack in self._attack_dict.values():
            if attack.effect_header in effect_headers:
                eff_ind = effect_headers.index(attack.effect_header)
                attack.control_header.set_effect_index(0, eff_ind)
            else:
                effect_headers.append(attack.effect_header)
                effect_mps.append(0)
                attack.control_header.set_effect_index(0, len(effect_headers)-1)

        for bitmask in self._bitmasks[7:]:
            group = self._bitmask_group_dict[bitmask]
            if group.num_pcs == 1:
                raise ValueError("Expected combo tech group")
            for tech_ind in range(group.num_techs):
                tech = group.get_tech(tech_ind)

                eff_ind = 0
                for eff_ind, effect_header in enumerate(tech.effect_headers):
                    new_effect = True
                    new_eff_ind = len(effect_headers)

                    if effect_header in effect_headers:
                        effect_header_ind = effect_headers.index(effect_header)
                        if effect_mps[effect_header_ind] == tech.effect_mps[eff_ind]:
                            new_effect = False
                            new_eff_ind = effect_header_ind

                    if new_effect:
                        effect_headers.append(effect_header)
                        effect_mps.append(tech.effect_mps[eff_ind])

                    tech.control_header.set_effect_index(eff_ind, new_eff_ind)

                # After loop eff_ind has the last used effect index.
                for var in range(eff_ind+1, 3):
                    if tech.control_header.get_effect_index(var) != 0:
                        print(tech.control_header)
                        print(tech.control_header.get_effect_index(var))
                        raise ValueError("Incorrectly set effect headers")

        for tech_id in range(1, self.num_techs+1):
            tech = self.get_tech(tech_id)
            ctl = tech.control_header
            for ind in range(3):
                eff_ind = ctl.get_effect_index(ind)
                if eff_ind == 0:
                    continue

                effect = tech.effect_headers[ind]
                if effect_headers[eff_ind] != effect:
                    raise ValueError

        effect_bytes = b''.join(effect for effect in effect_headers)
        return effect_bytes, effect_mps

    def _verify_effect_headers(self,
                               effect_headers: list[ctt.PCTechEffectHeader]):
        """
        Verify that the control headers of techs point to the correct index
        in parameter effect_headers.
        """
        for bitmask in self._bitmasks:
            for tech in self._bitmask_group_dict[bitmask].get_all_techs():
                if tech is None:
                    raise ValueError("Unset Tech")

                ctl = tech.control_header
                for ind in range(3):
                    eff_ind = ctl.get_effect_index(ind)
                    if eff_ind == 0:
                        continue

                    effect = tech.effect_headers[ind]
                    if effect_headers[eff_ind] != effect:
                        raise ValueError

    def _collect_control_headers(self) -> bytes:
        """Reteurn control header bytes ready to write to rom"""
        empty_header = ctt.PCTechControlHeader()  # Tech 0

        return (
            bytes(empty_header) +
            b"".join(
                tech.control_header for tech in self._get_tech_generator()
            ) +
            b"".join(
                self._attack_dict[pc_id].control_header
                for pc_id in ctenums.CharID
            )
        )

    def _collect_gfx_headers(self) -> bytes:
        """Reteurn graphics header bytes ready to write to rom"""
        empty_header = ctt.PCTechGfxHeader()  # Tech 0
        return bytes(empty_header) + b"".join(
            tech.graphics_header for tech in self._get_tech_generator()
        )

    def _collect_tech_names(self) -> bytes:
        """Return tech name bytes ready to write to rom."""
        empty_name = ctstrings.CTNameString.from_string("")
        return bytes(empty_name) + b"".join(
            bytes(ctstrings.CTNameString.from_string(tech.name))
            for tech in self._get_tech_generator()
        )

    def _collect_tech_descriptions_and_ptrs(self) -> tuple[bytes, list[int]]:
        """Returns tech descriptions as binary data and pointers into the data."""
        empty_string = ctstrings.CTString.from_str("{null}")
        desc_b = bytearray(empty_string)
        desc_ptrs: list[int] = [0]
        cur_ptr = len(empty_string)

        for tech in self._get_tech_generator():
            desc_ptrs.append(cur_ptr)
            cur_desc = ctstrings.CTString.from_str(tech.desc+"{null}")
            desc_b.extend(cur_desc)
            cur_ptr += len(cur_desc)

        return desc_b, desc_ptrs

    def _collect_target_data(self) -> bytes:
        """Return graphics header bytes ready to write to rom"""
        empty_header = ctt.TargetData()  # Tech 0
        return bytes(empty_header) + b"".join(
            tech.target_data for tech in self._get_tech_generator()
        )

    def _collect_atb_penalties(self) -> bytes:
        """Return graphics header bytes ready to write to rom"""
        data_size = 1 + self.num_techs + self.num_triple_techs + self.num_rock_techs
        first_triple_tech = 1 + self.num_techs - self.num_triple_techs

        data = bytearray(data_size)
        for ind, tech in enumerate(self._get_tech_generator()):
            data[ind+1] = tech.atb_penalty[0]
            if ind >= first_triple_tech:
                data[ind+1+self.num_triple_techs] = tech.atb_penalty[1]

        return bytes(data)

    def _get_tech_generator(self) -> Generator[PCTech, None, None]:
        """Easier Access to techs in tech_id order."""
        def generator() -> typing.Generator[PCTech, None, None]:
            for bitmask in self._bitmasks:
                for tech in self._bitmask_group_dict[bitmask].get_all_techs():
                    if tech is None:
                        raise ValueError("unset tech")
                    yield tech

        return generator()

    def _write_block_to_ct_rom(
            self, data: typing.ByteString, ct_rom: ctrom.CTRom, hint: int = 0x5F0000
    ) -> int:
        """Write a MARK_USED block to ct_rom.  Returns start of block on rom"""
        new_start = ct_rom.space_manager.get_free_addr(len(data), hint)
        ct_rom.seek(new_start)
        ct_rom.write(data, ctrom.freespace.FSWriteType.MARK_USED)

        return new_start


    @classmethod
    def _collect_attack_headers_from_ct_rom(
            cls,
            ct_rom: ctrom
    ) -> bytes:
        """
        Gather attack headers since they need to follow tech control headers
        """
        num_existing_techs = ctt.get_total_tech_count(ct_rom)
        attack_controls = b"".join(
            ctt.PCTechControlHeader.read_from_ctrom(ct_rom, ind)
            for ind in range(num_existing_techs, num_existing_techs + 7)
        )

        return attack_controls


    def _write_control_headers_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            hint: int = 0x5F0000):
        """
        Write control headers to ct_rom and update rom pointers.
        Needs to be done after effects/battle groups are finalized.
        """
        control_bytes = self._collect_control_headers()
        # control_bytes = control_bytes + attack_controls
        control_start = self._write_block_to_ct_rom(control_bytes, ct_rom, hint)
        pctechrefs.fix_control_refs(ct_rom.getbuffer(), control_start)

        num_controls = len(control_bytes) // ctt.ControlHeader.SIZE
        # Fix reference to attack indices.
        new_attack_indices = bytes(1+self.num_techs+i for i in range(7))
        ct_rom.seek(0x0C2583)
        ct_rom.write(new_attack_indices)

    @classmethod
    def _collect_extra_gfx_headers_from_ct_rom(
            cls,
            ct_rom: ctrom.CTRom
    ):
        """
        Collect non-tech gfx headers from ct_rom.
        """

        # Fetch additional gfx headers (run away, etc)
        num_existing_techs = ctt.get_total_tech_count(ct_rom)
        num_extra_headers = 11
        extra_gfx = b"".join(
            ctt.PCTechGfxHeader.read_from_ctrom(ct_rom, ind)
            for ind in range(num_existing_techs, num_existing_techs + num_extra_headers)
        )

        return extra_gfx

    def _write_gfx_headers_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            extra_gfx: bytes,
            hint: int = 0x5F0000
    ):
        """
        Write gfx headers to ct_rom and update rom pointers.
        """
        gfx_bytes = self._collect_gfx_headers()

        gfx_bytes = gfx_bytes + extra_gfx
        gfx_start = self._write_block_to_ct_rom(gfx_bytes, ct_rom, hint)

        # Fix references which read tech graphics
        pctechrefs.fix_gfx_refs(ct_rom.getbuffer(), gfx_start)

        # Fix references to non-tech graphics
        num_extra_headers = len(extra_gfx) // ctt.PCTechGfxHeader.SIZE
        gfx_count = 1 + self.num_techs + num_extra_headers

        # $C1/820D A9 79       LDA #$79 -- 0x79 is offset for running away gfx
        # It should be 7th from the back.
        ct_rom.getbuffer()[0x01820E] = gfx_count - 7

        # This is greendream loading
        # $C1/B365 A9 7A       LDA #$7A
        # $C1/B367 8D 93 AE    STA $AE93  [$7E:AE93]
        ct_rom.getbuffer()[0x01B366] = gfx_count - 6

        # This is poison ticking
        # $C1/8943 A9 7F       LDA #$7F
        ct_rom.getbuffer()[0x018944] = gfx_count - 1

        # This is SeraphSong effect, also 7F?
        # $C1/8BAF A9 7F       LDA #$7F
        ct_rom.getbuffer()[0x018BB0] = gfx_count - 1

    def _write_target_data_to_ct_rom(
            self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000):
        """
        Write target data to ct_rom and update references.
        """
        target_bytes = self._collect_target_data()
        target_start = self._write_block_to_ct_rom(target_bytes, ct_rom, hint)
        pctechrefs.fix_target_refs(ct_rom.getbuffer(), target_start)

    def _write_tech_names_to_ct_rom(
            self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000):
        """
        Write name data to ct_rom and update references.
        """
        name_bytes = self._collect_tech_names()
        name_start = self._write_block_to_ct_rom(name_bytes, ct_rom, hint)
        pctechrefs.fix_name_refs(ct_rom.getbuffer(), name_start)

    def _write_atb_penalties_to_ct_rom(
            self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000
    ):
        """
        Write atb penalty data to ct_rom and update references.
        """
        atb_penalty_bytes = self._collect_atb_penalties()
        atb_pen_start = self._write_block_to_ct_rom(atb_penalty_bytes, ct_rom, hint)
        pctechrefs.fix_atb_pen_refs(ct_rom.getbuffer(), atb_pen_start, self.num_triple_techs)

    @classmethod
    def _collect_extra_descs_from_ct_rom(
            cls,
            ct_rom: ctrom.CTRom
    ) -> list[bytes]:
        """Collect non-tech descs from ct rom"""
        num_extra_descs = 4
        num_existing_techs = ctt.get_total_tech_count(ct_rom)

        descs = [
            bytes(ctt.read_tech_desc_from_ctrom(ct_rom, ind+num_existing_techs))
            for ind in range(num_extra_descs)
        ]

        return descs

    def _write_descriptions_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            extra_descs: list[bytes],
            hint: int = 0x5F0000):
        """
        Write descriptions and pointers to ct_rom and update references.
        """
        desc_bytes, desc_ptrs = self._collect_tech_descriptions_and_ptrs()

        ptr_loc = len(desc_bytes)
        extra_desc_b = b"".join(desc for desc in extra_descs)
        for desc in extra_descs:
            desc_ptrs.append(ptr_loc)
            ptr_loc += len(desc)

        desc_bytes = desc_bytes + extra_desc_b
        total_len = len(desc_bytes) + 2*len(desc_ptrs)

        desc_ptr_start = ct_rom.space_manager.get_free_addr(total_len, hint)
        desc_start = desc_ptr_start + 2*len(desc_ptrs)

        desc_ptr_bytes = b"".join(
            int.to_bytes((0xFFFF & desc_start) + ptr, 2, "little")
            for ptr in desc_ptrs
        )
        ct_rom.seek(desc_ptr_start)
        ct_rom.write(desc_ptr_bytes, ctrom.freespace.FSWriteType.MARK_USED)
        ct_rom.write(desc_bytes, ctrom.freespace.FSWriteType.MARK_USED)

        pctechrefs.fix_desc_ptr_refs(ct_rom.getbuffer(), desc_ptr_start)

        # Loading menu page + a value to get menu page descs
        # $C2/BE2F 69 76       ADC #$76
        # Should be num desc ptrs - 3
        ct_rom.getbuffer()[0x02BE30] = 1 + self.num_techs + 1

    def _write_learn_requirements_to_ct_rom(self, ct_rom: ctrom.CTRom,
                                            hint: int = 0x5F0000):
        """
        Write learn requirements to ct_rom and update references.
        """

        learn_req_bitmasks = [
            bitmask for bitmask in self._bitmasks
            if (
                self._bitmask_group_dict[bitmask].num_pcs > 1 and
                self._bitmask_group_dict[bitmask].rock_used is None
            )
        ]

        # Only non_rock combo techs have learn requirements.
        num_learn_techs = sum(
            self._bitmask_group_dict[bitmask].num_techs
            for bitmask in learn_req_bitmasks
        )
        learn_req_size = num_learn_techs*ctt.PCTechLearnRequirements.SIZE
        learn_ref_size = len(learn_req_bitmasks)*5+1

        learn_req_start = ct_rom.space_manager.get_free_addr(
            learn_req_size+learn_ref_size, hint
        )

        learn_req_buf = io.BytesIO()
        learn_ref_buf = io.BytesIO()
        lrn_req_bank_offset = learn_req_start & 0xFFFF
        cur_tech_id = 0x39  # First dual tech is always this.

        for bitmask in learn_req_bitmasks:
            group = self._bitmask_group_dict[bitmask]

            cur_lrn_req_offset = learn_req_buf.tell() + lrn_req_bank_offset
            lrn_ref = ctt.PCTechLearnReferences()
            lrn_ref.bitmask = bitmask
            lrn_ref.first_tech_id = cur_tech_id
            lrn_ref.num_techs = group.num_techs
            lrn_ref.offset = cur_lrn_req_offset
            learn_ref_buf.write(lrn_ref)

            for tech in group.get_all_techs():
                if tech is None or tech.learn_reqs is None:
                    raise ValueError

                learn_req_buf.write(tech.learn_reqs)

            cur_tech_id += group.num_techs

        learn_ref_buf.write(b'\xFF') # Must FF-terminate learn refs

        ct_rom.seek(learn_req_start)
        learn_req_b = learn_req_buf.getvalue()
        ct_rom.write(learn_req_b, ctrom.freespace.FSWriteType.MARK_USED)
        ct_rom.write(learn_ref_buf.getvalue(), ctrom.freespace.FSWriteType.MARK_USED)

        pctechrefs.fix_lrn_req_refs(ct_rom.getbuffer(), learn_req_start)
        pctechrefs.fix_lrn_ref_refs(ct_rom.getbuffer(), learn_req_start+len(learn_req_b))

    def _write_menu_groups_to_ct_rom(self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000):
        """
        Write menu groups (bitmasks) to ct_rom and update references.
        Includes extra data like a listing of which tech_id begins each group.
        """

        num_dual_groups = sum(
            1 for bitmask in self._bitmasks
            if self._bitmask_group_dict[bitmask].num_pcs == 2
        )
        if num_dual_groups != self.num_dual_techs // 3:
            raise ValueError

        menu_group_start = self._write_block_to_ct_rom(
            bytes(self._bitmasks), ct_rom, hint
        )

        cur_tech_id = 1
        group_starts = []
        for bitmask in self._bitmasks:
            group = self._bitmask_group_dict[bitmask]
            group_starts.append(cur_tech_id)
            cur_tech_id += group.num_techs

        # If there are no duals/triples, put in a dummy value at the end because many
        # loops look to the start of the next group for a bound.
        if self.num_triple_techs == 0 and self.num_dual_techs == 0:
            group_starts.append(group_starts[-1]+8)
        elif self.num_triple_techs == 0:
            group_starts.append(group_starts[-1]+3)

        group_starts_start = self._write_block_to_ct_rom(
            bytes(group_starts), ct_rom, hint
        )

        pctechrefs.fix_menu_grp_refs(ct_rom.getbuffer(), menu_group_start)
        pctechrefs.fix_grp_begin_refs(ct_rom.getbuffer(), group_starts_start)

        # $FF/F863 A2 24       LDX #$24
        # This is a hardcoded number of menu groups.  The value should be an
        # index to the last menu group.
        ct_rom.getbuffer()[0x3ff864] = len(self._bitmasks) - 1

        # $FF/F910 C9 0F       CMP #$0F
        # A count of the dual groups.  Needs to be updated.
        ct_rom.getbuffer()[0x3FF911] = num_dual_groups

        # $FF/F936 C9 0F       CMP #$0F
        # This is the same but for triple techs.
        ct_rom.getbuffer()[0x3FF937] = self.num_triple_techs + self.num_rock_techs

        # These two need more care since the relative location of trip/rock
        # will vary depending on the reassignment
        # $FF/F97A BF 83 29 CC LDA $CC2983,x  --> 0x3FF97B  (Rock Techs)
        # $FF/F91A BF 79 29 CC LDA $CC2979,x  --> 0x3FF91B  (Triple Techs)
        trip_group_start = menu_group_start + 7 + num_dual_groups
        ct_rom.seek(0x3FF91B)
        ct_rom.write(int.to_bytes(byteops.to_rom_ptr(trip_group_start), 3, "little"))

        rock_group_start = menu_group_start + len(self._bitmasks) - self.num_rock_techs
        ct_rom.seek(0x3FF97B)
        ct_rom.write(int.to_bytes(byteops.to_rom_ptr(rock_group_start), 3, "little"))

    def _write_tech_ranges_to_ct_rom(self, ct_rom):
        """
        Updating references on the rom having to do with ranges for
        single, dual, and triple techs.
        """

        # The six bytes starting at 0x02BD65 give the group ranges for single,
        # dual, and triple techs.  We need to update them according to the db.
        # The format is sing start, #sing, dual_start, #dual, trip start, #trip
        num_dual_groups = self.num_dual_techs // 3
        first_trip_group = 7 + num_dual_groups
        ct_rom.getbuffer()[0x02BD68] = num_dual_groups
        ct_rom.getbuffer()[0x02BD69] = first_trip_group

        # The menu will bug if the number of triple groups is 0.
        num_triple_groups = max(self.num_triple_techs + self.num_rock_techs, 1)
        ct_rom.getbuffer()[0x02BD6A] = num_triple_groups

        # Ranges for battle menu to pick up techs
        # The battle menu will always be broken when there are too many techs.

        # $C1/CA37 A9 66       LDA #$66 <--- loading first triple tech id
        first_triple_id = 1+7*8 + self.num_dual_techs
        ct_rom.getbuffer()[0x01CA38] = first_triple_id

        # $C1/CCE5 A9 66       LDA #$66   <--- first triple tech id
        # $C1/CCE7 85 08       STA $08
        # $C1/CCE9 A9 75       LDA #$75   <--- last triple tech id+1
        # $C1/CCEB 85 0E       STA $0E
        ct_rom.getbuffer()[0x01CCE6] = first_triple_id
        ct_rom.getbuffer()[0x01CCEA] = first_triple_id + self.num_triple_techs + self.num_rock_techs

        # These are loading the techs-learned from ram.
        # When we change the number of dual groups, this has to change.
        orig_start = 0x2830 + 7
        trip_start = orig_start + first_trip_group
        trip_start_addr = int.to_bytes(trip_start, 2, "little")

        ct_rom.seek(0x01CD09)
        ct_rom.write(trip_start_addr)
        ct_rom.seek(0x01CDEF)
        ct_rom.write(trip_start_addr)

        ct_rom.getbuffer()[0x3FF9B5] = self.num_rock_techs

    def _write_menu_usability(self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000):
        """
        Update which tech ids can be used in the menu.
        """
        # Alter menu usability.  This is performed by setting the x80 bit in
        # memory corresponding to each tech.  $7E7700 + tech_id is where it
        # looks for tech #tech_id.  Sometimes there will be too many techs,
        # so we have to jump and extend the routine.

        # $FF/F82E A9 80       LDA #$80
        # $FF/F830 0C 09 77    TSB $7709  [$7E:7709]
        # $FF/F833 0C 0C 77    TSB $770C  [$7E:770C]
        # $FF/F836 0C 0F 77    TSB $770F  [$7E:770F]
        # $FF/F839 0C 1A 77    TSB $771A  [$7E:771A]
        # $FF/F83C 0C 1D 77    TSB $771D  [$7E:771D]
        # $FF/F83F 0C 21 77    TSB $7721  [$7E:7721]
        # $FF/F842 0C 24 77    TSB $7724  [$7E:7724]
        # $FF/F845 0C 27 77    TSB $7727  [$7E:7727]
        # $FF/F848 0C 29 77    TSB $7729  [$7E:7729]

        menu_usable_ids = [
            ind+1 for ind, tech in enumerate(self._get_tech_generator())
            if tech.menu_usable
        ]

        if len(menu_usable_ids) <= 9:
            # Just overwrite the IDs
            write_pos = 0x3FF831
            for tech_id in menu_usable_ids:
                ct_rom.getbuffer()[write_pos] = tech_id
                write_pos += 3

            write_pos += 1  # Get to the end of the command.
            num_nop = 0x3FF84B - write_pos
            nops = bytes.fromhex("EA"*num_nop)
            ct_rom.seek(write_pos)
            ct_rom.write(nops)
        else:
            new_rt: assemble.ASMList = []
            for tech_id in menu_usable_ids:
                new_rt.append(inst.TSB(0x7700+tech_id, AM.ABS))
            new_rt.append(inst.JSL())

            rt_addr = asmpatcher.add_jsl_routine(new_rt, ct_rom, hint)
            rt_rom_addr = byteops.to_rom_ptr(rt_addr)

            hook: assemble.ASMList = [
                inst.JSL(rt_rom_addr, AM.LNG)
            ]
            hook_b = assemble.assemble(hook)
            ct_rom.seek(0x3FF830)
            ct_rom.write(hook_b)

            num_nop = 0x3FF84B - ct_rom.tell()
            nops = bytes.fromhex("EA" * num_nop)
            ct_rom.write(nops)

    def _write_menu_mps_to_ct_rom(self, ct_rom: ctrom.CTRom, hint: int = 0x5F0000):
        """
        Write the mp values used by the menu and update references.
        """

        menu_mp_size = self.num_dual_techs*2 + (self.num_triple_techs+self.num_rock_techs)*3
        menu_mp_buf = io.BytesIO()

        for tech in self._get_tech_generator():
            if tech.num_pcs == 1:
                continue
            menu_mp_buf.write(tech.menu_mp_reqs)

        menu_mp_bytes = menu_mp_buf.getvalue()
        if len(menu_mp_bytes) != menu_mp_size:
            print(len(menu_mp_bytes), menu_mp_size)
            raise ValueError

        menu_mp_start = self._write_block_to_ct_rom(menu_mp_bytes, ct_rom, hint)
        pctechrefs.fix_menu_req_refs(ct_rom.getbuffer(), menu_mp_start)

        # Menu Req references that depend on number of techs
        trip_menu_mp_start = menu_mp_start + 2 * self.num_dual_techs
        trip_menu_mp_start_b = int.to_bytes(trip_menu_mp_start, 3, "little")

        # Menu MP start of trips
        # $FF/F947 BF 35 29 CC LDA $CC2935,x --> 0x3FF948
        ct_rom.seek(0x3FF948)
        ct_rom.write(trip_menu_mp_start_b)

        # $FF/F98C BF 53 29 CC LDA $CC2953,x
        # $CC2953 is the start of the rock part of the menu_mp_req
        if self.num_rock_techs == 0:
            mmp_offset = 0
        else:
            # self.triple_techs does not count rocks
            mmp_offset = 2 * self.num_dual_techs + 3 * self.num_triple_techs

        rock_mmp_start = menu_mp_start + mmp_offset
        ct_rom.seek(0x3FF98D)
        ct_rom.write(int.to_bytes(
            byteops.to_rom_ptr(rock_mmp_start), 3, "little")
        )

    def _write_blackhole_exceptions(
            self, ct_rom: ctrom.CTRom,
            black_hole_factor: float,
            black_hole_min: float
    ):
        """
        There's a weird BlackHole-only exception for tech animations.
        BlackHole will softlock unless this is set correctly.

        Also update black_hole's chance to kill.
        """

        # C14844  AD 93 AE       LDA $AE93    <-- Holds tech_id
        # C14847  C9 32          CMP #$37     <-- Default BlackHole id
        # C14849  F0 05          BEQ $C14850

        # Gather Black Hole IDs by testing graphics layer3 packet.
        black_hole_ids: list[int] = []
        for tech_id in range(1, 1+8*7):
            tech = self.get_tech(tech_id)
            if tech.graphics_header.layer3_packet_id == 0x08:
                black_hole_ids.append(tech_id)

        hook_addr = 0x014844
        return_addr = 0x014849

        if len(black_hole_ids) == 0:
            new_rt: assemble.ASMList = [
                inst.LDA(0xAE93, AM.ABS),
                inst.CMP(0x00, AM.IMM8)  # Will never branch
            ]
            new_rt_b = assemble.assemble(new_rt)
            ct_rom.seek(hook_addr)
            ct_rom.write(new_rt_b)
        elif len(black_hole_ids) == 1:
            new_rt: assemble.ASMList = [
                inst.LDA(0xAE93, AM.ABS),
                inst.CMP(black_hole_ids[0], AM.IMM8)  # Will never branch
            ]
            new_rt_b = assemble.assemble(new_rt)
            ct_rom.seek(hook_addr)
            ct_rom.write(new_rt_b)

            ct_rom.seek(0x0C2A72)
            mp = self.get_tech(black_hole_ids[0]).effect_mps[0]
            percent = sorted([1, round(black_hole_min + mp*black_hole_factor), 100])[1]
            ct_rom.write(bytes([percent]))
        else:
            new_rt: assemble.ASMList = [inst.LDA(0xAE93, AM.ABS)]
            for ind, tech_id in enumerate(black_hole_ids):
                new_rt.append(inst.CMP(tech_id, AM.IMM8))
                if ind != len(black_hole_ids):
                    new_rt.append(inst.BEQ("return"))

            new_rt.extend([
                "return",
                inst.JMP(byteops.to_rom_ptr(return_addr))
            ])
            asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)

    def write_to_ctrom(self, ct_rom: ctrom.CTRom,
                       black_hole_factor: float,
                       black_hole_min: float,
                       free_existing_tech_data: bool = True):
        """
        Write this PCTechManager to a ctrom.CTRom.

        In particular this method:
        1) Frees all existing tech data (to be re-written) if the parameter
           free_existing_tech_data is True.
        2) Writes all new tech data back to the ct_rom and marks it used
        3) Changes pointers to point to new tech data
        4) Patches the ct_rom for dc-specific changes
           - Patch menu-usable list to be arbitrarily long
           - Patch rock tech routines to allow multiple techs per rock
           - Patch target routines to allow pc-specific targeting other than
             Robo and Magus.
           - Expand to allow tech_ids exceeding 0x7F (max is 0xFE I think?)
        """
        hint = 0x5F0000

        # Gather some data about the existing tech data on ct_rom
        extra_gfx = self._collect_extra_gfx_headers_from_ct_rom(ct_rom)
        extra_descs = self._collect_extra_descs_from_ct_rom(ct_rom)

        # Now it's safe to wipe the old data

        for bitmask in self._bitmasks:
            group = self._bitmask_group_dict[bitmask]
            first_tech = copy.deepcopy(group.get_tech(0))
            first_tech.control_header[0] |= 0x80

            while group.has_free_space():
                group.add_tech(copy.deepcopy(first_tech))

        battle_group_bytes = self._collect_update_battle_groups()
        bat_group_start = self._write_block_to_ct_rom(battle_group_bytes, ct_rom, hint)
        pctechrefs.fix_bat_grp_refs(ct_rom.getbuffer(), bat_group_start)

        effect_header_bytes, effect_mps = self._collect_update_effect_headers_and_mps()
        effect_start = self._write_block_to_ct_rom(effect_header_bytes,
                                                   ct_rom, hint)
        pctechrefs.fix_effect_refs(ct_rom.getbuffer(), effect_start)

        mp_start = self._write_block_to_ct_rom(effect_mps, ct_rom, hint)
        pctechrefs.fix_mp_refs(ct_rom.getbuffer(), mp_start)

        self._write_control_headers_to_ct_rom(ct_rom, hint)
        self._write_menu_groups_to_ct_rom(ct_rom, hint)
        self._write_gfx_headers_to_ct_rom(ct_rom, extra_gfx, hint)
        self._write_target_data_to_ct_rom(ct_rom, hint)
        self._write_tech_names_to_ct_rom(ct_rom, hint)
        self._write_atb_penalties_to_ct_rom(ct_rom, hint)
        self._write_descriptions_to_ct_rom(ct_rom, extra_descs, hint)
        self._write_learn_requirements_to_ct_rom(ct_rom, hint)
        self._write_menu_mps_to_ct_rom(ct_rom, hint)
        self._write_menu_usability(ct_rom, hint)

        self._write_tech_ranges_to_ct_rom(ct_rom)
        self._update_rock_techs(ct_rom)
        self._write_blackhole_exceptions(ct_rom, black_hole_factor, black_hole_min)


    @classmethod
    def _free_block_on_ct_rom_rw(
            cls,
            ct_rom: ctrom.CTRom,
            rom_rw: cty.AbsPointerRW | cty.LocalPointerRW,
            record_size: int,
            num_records: int,
            overwrite_byte: Optional[int] = 0xFF
    ):

        start = rom_rw.get_data_start_from_ctrom(ct_rom)
        size = record_size*num_records

        cls._free_block_on_rom(ct_rom, start, size, overwrite_byte)

    @classmethod
    def _free_block_on_rom(
            cls,
            ct_rom: ctrom.CTRom,
            start: int,
            size: int,
            overwrite_byte: Optional[int] = None
    ):
        if overwrite_byte is not None:
            payload = bytes([overwrite_byte] * size)
            ct_rom.seek(start)
            ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_FREE)
        else:
            ct_rom.space_manager.mark_block(
                (start, start+size),
                ctrom.freespace.FSWriteType.MARK_FREE
            )


    @classmethod
    def _free_type_block_on_rom(
            cls,
            ct_rom: ctrom.CTRom,
            data_type: typing.Type[ctt.SizedBinaryData],
            num_records: int,
            overwrite_byte: Optional[int] = 0xFF
    ):
        """
        Free a block on the rom and optionally overwrite it.
        """
        rom_rw = data_type.ROM_RW
        if not (
                isinstance(rom_rw, cty.AbsPointerRW) or
                isinstance(rom_rw, cty.LocalPointerRW)
        ):
            raise TypeError

        cls._free_block_on_ct_rom_rw(ct_rom, rom_rw, data_type.SIZE, num_records,
                                     overwrite_byte)

    def _build_rock_ptrs(self) -> tuple[list[int], list[int]]:
        """
        builds a list of each character's rock techs as well as a pointer table to
        find the appropriate char/rock combo
        """
        ptrs = [0]
        tech_ids = []

        for pc in range(0, 7):
            rock_ids = [[], [], [], [], []]
            pc_bitmask = 0x80 >> pc

            start_index =  len(self._bitmasks) - self.__num_rock_groups
            first_rock_id = ctenums.ItemID.BLACK_ROCK
            first_rock_tech_id =  self.num_techs - self.num_rock_techs + 1

            for ind, bitmask in enumerate(self._bitmasks[start_index:]):
                if bitmask & pc_bitmask:
                    rock = self._bitmask_group_dict[bitmask].rock_used
                    if rock is None:
                        raise ValueError
                    rock_offset = rock - first_rock_id
                    tech_id = ind # first_rock_tech_id + ind
                    rock_ids[rock_offset].append(tech_id)

            for ind in range(5):
                ptrs.append(ptrs[-1] + len(rock_ids[ind]) + 1)
                tech_ids.extend(rock_ids[ind] + [0xFF])


            # for grp_id in range(db.first_rock_grp, len(db.menu_grps)):
            #     grp = db.menu_grps[grp_id]
            #     if grp & pc_bitmask != 0:
            #         offset = grp_id - db.first_rock_grp
            #         rock = db.rock_types[offset]
            #         tech = db.first_rock_tech + offset
            #         rock_ids[rock].append(tech)
            #
            # for i in range(0, 5):
            #     ptrs.append(ptrs[-1] + len(rock_ids[i]) + 1)
            #     techs.extend(rock_ids[i] + [0xFF])

        return ptrs, tech_ids

    def _update_rock_techs(self, ct_rom: ctrom.CTRom, ):
        """Modify the code on the rom which handles rock tech availability."""

        # --- Zeros out the part of ram for rock techs being learned
        # C282E1  08             PHP
        # C282E2  C2 30          REP #$30
        # C282E4  9C 57 28       STZ $2857
        # C282E7  A2 57 28       LDX #$2857
        # C282EA  A0 59 28       LDY #$2859
        # C282ED  A9 02 00       LDA #$0002
        # C282F0  54 7E 7E       MVN $7E,$7E
        # --- hook here for updated SR --
        # C282F3  A2 00 26       LDX #$2600
        # C282F6  A9 00 00       LDA #$0000
        # C282F9  E2 20          SEP #$20

        # --- Copies rocks learned into another place for ???
        # C2B9AF  A2 57 28       LDX #$2857
        # C2B9B2  A0 20 7F       LDY #$7F20
        # C2B9B5  A9 04          LDA #$04
        # C2B9B7  54 7E 7E       MVN $7E,$7E

        # 1) The three references to $2857 need to be the address of the first rock
        #    group in the techs-learned ram: 0x2837 + number of non-rock groups
        first_rock_group = len(self._bitmasks) - self.num_rock_techs
        rock_learn_start = 0x2837 + first_rock_group

        ct_rom.seek(0x0282E5)
        ct_rom.write(rock_learn_start.to_bytes(2, "little"))

        ct_rom.seek(0x0282E8)
        ct_rom.write(rock_learn_start.to_bytes(2, "little"))

        ct_rom.seek(0x02B9B0)
        ct_rom.write(rock_learn_start.to_bytes(2, "little"))

        rock_copy_start = 0x7F00 + first_rock_group
        ct_rom.seek(0x02B9B3)
        ct_rom.write(rock_copy_start.to_bytes(2, "little"))

        # 2) The "# C282EA  A0 59 28       LDY #$2859" should be two bytes after the rock start
        ct_rom.seek(0x0282EB)
        ct_rom.write(int.to_bytes(rock_learn_start + 2, 2, "little"))

        # 3) The "C282ED  A9 02 00       LDA #$0002" should be num rocks - 3 (unless negative)
        clear_num = 0 if self.num_rock_techs < 3 else self.num_rock_techs-3
        ct_rom.seek(0x0282EE)
        ct_rom.write(clear_num.to_bytes(2, "little"))

        # Now hook at:
        #   C282F3  A2 00 26       LDX #$2600
        #   C282F6  A9 00 00       LDA #$0000
        #   C282F9  E2 20          SEP #$20
        # and write a new subroutine for enabling rock techs.
        hook_addr = 0x0282F3

        ptrs, tech_ids = self._build_rock_ptrs()
        payload = bytes(ptrs) + bytes(tech_ids)
        ptr_addr = ct_rom.space_manager.get_free_addr(len(payload), 0x410000)
        ptr_rom_addr = byteops.to_rom_ptr(ptr_addr)
        tech_id_addr = ptr_addr + len(ptrs)
        tech_id_rom_addr = byteops.to_rom_ptr(tech_id_addr)

        ct_rom.seek(ptr_addr)
        ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_USED)

        # $4F/2000	 A2 00 26    LDX #$2600
        #     $4F/2003	 A0 00 00    LDY #$0000
        #     $4F/2006	 A9 00 00    LDA #$0000
        #     $4F/2009	 E2 20       SEP #$20   #8 bit A
        #     $4F/200B	 BD 2A 00    LDA $002A,x[$7E:FC4D]
        #     $4F/200E	 C9 AE       CMP #$AE
        #     $4F/2010	 90 37 	     BCC $37  #to rep #$20
        #     $4F/2012	 C9 B3       CMP #$B3
        #     $4F/2014	 B0 33       BCS $33
        #     OK.  Now get the pointer
        #     $4F/2016  	 38		SEC
        #     $4F/2017	 E9 AE		SBC #$AE
        #     # We have a rock, rock_id (in A) equipped to pc_id (in Y)
        #     $4F/2019	 8D 90 04	STA $TEMP
        #     $4F/201C	 98		TYA
        #     $4F/201D	 8D 92 04	STA $TEMPY
        #     $4F/2020	 0A		ASL         # ASL should CLC
        #     $4F/2021	 0A		ASL
        #     $4F/2022     6D 92 04       ADC $TEMPY  # 5*pc_id
        #     $4F/2025     6D 90 04       ADC $TEMP   # 5*pc_id + rock_id
        #     $4F/2028	 DA		PHX
        #     $4F/2029	 AA		TAX
        #     $4F/202A	 BF 00 12 4F	LDA $4F1200,x  #ptr to rock refs
        #     $4F/202E	 AA		TAX
        #     $4F/202F	 BF 00 13 4F	LDA $4F1300,x  .loop1
        #     $4F/2033	 C9 FF		CMP #$FF
        #     $4F/2035	 F0 0E		BEQ to the LDY
        #     $4F/2037     A8             TAY
        #     $4F/2038	 B9 A4 04	LDA $04A4, y
        #     $4F/203B	 F0 05		BEQ $05            # to INY and loop again
        #     $4F/203D	 A9 80		LDA #$80
        #     $4F/203F	 99 XX XX	STA $ROCKSTART, 9  # addr depends on num rocks
        #     $4F/2042	 E8		INY
        #     $4F/2043	 80 EA		BRA to .loop1 (-$20)
        #     $4F/2045     AC 92 04       LDY $TEMPY
        #     $4F/2048	 FA		PLX	.outloop1
        #     $4F/2049	 C2 20 		REP #$20
        #     $4F/204B     8A             TXA
        #     $4F/204C	 18		CLC
        #     $4F/204D	 69 50 00	ADC #$0050
        #     $4F/2050	 AA		TAX
        #     $4F/2051	 C8		INY
        #     $4F/2052	 C9 30 28	CMP #$2830
        #     $4F/2055	 90 AF		BCC $AF**    		# to LDA #$0000
        #     $4F/2057	 5C 1E 83 C2	JMP back to orig to end
        temp_addr = 0x0490
        temp_addr_y = 0x0492
        rt: assemble.ASMList = [
            inst.LDX(0x2600, AM.IMM16),
            inst.LDY(0x0000, AM.IMM16),
            "begin",
            inst.LDA(0x0000, AM.IMM16),
            inst.SEP(0x20),
            # Skip a PC if they aren't wearing a rock.
            inst.LDA(0x002A, AM.ABS_X),
            inst.CMP(ctenums.ItemID.BLACK_ROCK, AM.IMM8),
            inst.BCC("next_pc"),
            inst.CMP(ctenums.ItemID.GOLD_ROCK+1, AM.IMM8),
            inst.BCS("next_pc"),
            inst.SEC(),
            inst.SBC(ctenums.ItemID.BLACK_ROCK, AM.IMM8),
            # rock_offset in A, pc_id in Y
            inst.STA(temp_addr, AM.ABS),
            inst.TYA(),
            inst.STA(temp_addr_y, AM.ABS),  # Why didn't I STY?
            inst.ASL(mode=AM.NO_ARG),
            inst.ASL(mode=AM.NO_ARG),       # ASL will CLC
            inst.ADC(temp_addr_y, AM.ABS),  # 5*pc_id in A
            inst.ADC(temp_addr, AM.ABS),    # 5*pc_id + rock_offset
            inst.PHX(),
            inst.TAX(),
            inst.LDA(ptr_rom_addr, AM.LNG_X),
            inst.TAX(),
            "loop1",
            inst.LDA(tech_id_rom_addr, AM.LNG_X),
            inst.CMP(0xFF, AM.IMM8),
            inst.BEQ("after_loop1"),
            inst.TAY(),
            inst.LDA(0x04A4, AM.ABS_Y), # Range recording learnability of rock tech
            inst.BEQ("continue_loop1"),
            inst.LDA(0x80, AM.IMM8),
            inst.STA(rock_learn_start, AM.ABS_Y),
            "continue_loop1",
            inst.INX(),
            inst.BRA("loop1"),
            "after_loop1",
            inst.LDY(temp_addr_y, AM.ABS),
            inst.PLX(),
            "next_pc",
            inst.REP(0x20),
            inst.TXA(),
            inst.CLC(),
            inst.ADC(0x0050, AM.IMM16),
            inst.TAX(),
            inst.INY(),
            inst.CMP(0x2830, AM.IMM16),
            inst.BCC("begin"),
            inst.JMP(0xC2831E, AM.LNG)
        ]
        asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, hint = 0x410000)

    @classmethod
    def free_existing_tech_data_on_ct_rom(
            cls, ct_rom: ctrom.CTRom,
            overwrite_byte: Optional[int] = 0xFF
    ):
        num_techs = ctt.get_total_tech_count(ct_rom)
        num_menu_groups = ctt.get_pc_menu_group_count(ct_rom)
        num_dual_groups = ct_rom.getbuffer()[0x3FF911]
        num_trip_groups = ct_rom.getbuffer()[0x3FF937]
        num_rock_groups = ct_rom.getbuffer()[0x3FF9B5]

        num_controls = ctt.get_pc_control_header_count(ct_rom, num_techs)
        cls._free_type_block_on_rom(ct_rom, ctt.PCTechControlHeader, num_controls, overwrite_byte)

        num_effects = ctt.get_pc_effect_header_count(ct_rom, num_techs)
        cls._free_type_block_on_rom(ct_rom, ctt.PCTechEffectHeader, num_effects, overwrite_byte)
        cls._free_type_block_on_rom(ct_rom, ctt.PCEffectMP, num_effects, overwrite_byte)

        num_gfx = num_techs + 11
        cls._free_type_block_on_rom(ct_rom, ctt.PCTechGfxHeader, num_gfx)

        cls._free_type_block_on_rom(ct_rom, ctt.PCTechTargetData, num_techs)
        cls._free_type_block_on_rom(
            ct_rom, ctt.PCTechBattleGroup, ctt.get_pc_battle_group_count(ct_rom, num_techs),
            overwrite_byte
        )
        cls._free_type_block_on_rom(
            ct_rom, ctt.PCTechMenuGroup, ctt.get_pc_menu_group_count(ct_rom)
        )
        cls._free_type_block_on_rom(
            ct_rom, ctt.PCTechBattleGroup,
            ctt.get_pc_battle_group_count(ct_rom, num_techs)
        )
        cls._free_block_on_ct_rom_rw(
            ct_rom, ctt.get_tech_name_rom_rw(), 0xB,
            num_techs, overwrite_byte
        )

        # Descs and Desc Ptrs.
        num_desc_ptrs = num_techs + 4
        desc_ptr_rom_rw = ctt.PCTechDescriptionPointer.ROM_RW
        start = desc_ptr_rom_rw.get_data_start_from_ctrom(ct_rom)

        for ptr_ind in range(num_desc_ptrs):
            ptr_b = desc_ptr_rom_rw.read_data_from_ctrom(ct_rom, ptr_ind)
            ptr = int.from_bytes(ptr_b, "little")
            desc_len = len(ctt.read_tech_desc_from_ctrom_address(ct_rom, ptr))

            if overwrite_byte is None:
                ct_rom.space_manager.mark_block(
                    (ptr, ptr+desc_len),
                    ctrom.freespace.FSWriteType.MARK_FREE
                )
            else:
                payload = bytes([overwrite_byte]*desc_len)
                ct_rom.seek(ptr)
                ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_FREE)

        cls._free_type_block_on_rom(ct_rom, ctt.PCTechDescriptionPointer,
                               num_desc_ptrs, overwrite_byte)

        num_learn_reqs = 3*num_dual_groups + num_trip_groups - num_rock_groups
        cls._free_block_on_rom(
            ct_rom,
            ctt.PCTechLearnRW.get_learn_requirment_start(ct_rom.getbuffer()),
            ctt.PCTechLearnRequirements.SIZE*num_learn_reqs
        )

        # Learn Reqs and Refs
        learn_ref_start = ctt.PCTechLearnRW.get_learn_ref_start(ct_rom.getbuffer())
        learn_ref_size = 0
        while True:
            learn_ref_size += 1
            if ct_rom.getbuffer()[learn_ref_start+learn_ref_size] == 0xFF:
                break

        if (learn_ref_size % 5) != 1:
            raise ValueError

        cls._free_block_on_rom(ct_rom, learn_ref_start, learn_ref_size, overwrite_byte )

        # Menu Groups and group starts
        cls._free_type_block_on_rom(
            ct_rom, ctt.PCTechMenuGroup, num_menu_groups, overwrite_byte
        )
        ct_rom.seek(0x02BD18)
        group_starts_ptr_b = ct_rom.read(3)
        group_starts_ptr = byteops.to_file_ptr(
            int.from_bytes(group_starts_ptr_b, "little")
        )
        cls._free_block_on_rom(ct_rom, group_starts_ptr, num_menu_groups, overwrite_byte)

        # Menu MP
        menu_mp_size = num_dual_groups*2 + num_trip_groups*3
        start = ctt.MenuMPReqRW.get_data_start(ct_rom)
        cls._free_block_on_rom(ct_rom, start, menu_mp_size, overwrite_byte)

        # ATB Pen
        atb_rw = ctt.PCTechATBPenaltyRW(num_dual_groups*3, num_trip_groups)
        atb_start = atb_rw.get_data_start_from_ctrom(ct_rom)
        atb_size = num_techs + num_trip_groups
        cls._free_block_on_rom(ct_rom, atb_start, atb_size, overwrite_byte)


    def print_protected(self):
        """Debug method for tracking the group counts."""
        print(self.__num_dual_groups, self.__num_triple_groups,
              self.__num_rock_groups)

    def print_all_techs(self):
        """Debug method for displaying all techs."""
        for bitmask in self._bitmasks:
            group = self._bitmask_group_dict[bitmask]
            pcs = ' '.join(str(pc) for pc in group.pcs)
            print(f"Group: {group.bitmask:02X} ({pcs})")
            for tech in group.get_all_techs():
                if tech is None:
                    print("None")
                else:
                    print(f"    {tech.name}")


def fix_vanilla_techs(tech_man: PCTechManager):
    """
    Fix various bugs with the vanilla techs.
    """

    # Spin Kick
    # Uses Laserspin as an effect/mp cost, but uses Robo Tackle for Learning/Menu MP
    # Fix: Use Laserspin for all data.
    tech = tech_man.get_tech(ctenums.TechID.SPIN_KICK)
    tech.set_learn_requirement(ctenums.CharID.ROBO, ctenums.TechID.LASER_SPIN)
    tech.set_menu_mp_requirement(ctenums.CharID.ROBO, ctenums.TechID.LASER_SPIN)
    tech_man.set_tech_by_id(tech, ctenums.TechID.SPIN_KICK)

    # Fire Zone
    # Uses Robo Tackle as an effect/mp cost (only mp)
    # Uses laser spin as a learn requirement and menu mp.
    # Fix: Use Laserspin for all data (match Max Cyclone on which this is based)
    tech = tech_man.get_tech(ctenums.TechID.FIRE_ZONE)
    tech.set_learn_requirement(ctenums.CharID.ROBO, ctenums.TechID.LASER_SPIN)
    tech.set_menu_mp_requirement(ctenums.CharID.ROBO, ctenums.TechID.LASER_SPIN)
    tech_man.set_tech_by_id(tech, ctenums.TechID.FIRE_ZONE)

    # Double Cure
    # Uses menu MP of 0x0F, 0x0F, which is Marle’s Cure 2 twice.
    # Fix: Make one of them (either one) into Frog's Cure 2
    tech = tech_man.get_tech(ctenums.TechID.DOUBLE_CURE)
    tech.menu_mp_reqs[0] = ctenums.TechID.CURE_2_F
    tech_man.set_tech_by_id(tech, ctenums.TechID.DOUBLE_CURE)

    # Spin Strike
    # Uses Tail Spin’s Menu MP (equals learning requirement since it’s a rock tech)
    # but it uses Dino Tail for in-battle effect mp.
    # Fix: Use Tail Spin for in battle effect mp
    tail_spin = tech_man.get_tech(ctenums.TechID.TAIL_SPIN)
    spin_strike = tech_man.get_tech(ctenums.TechID.SPIN_STRIKE)
    ayla_bat_index = spin_strike.battle_group.index(ctenums.CharID.AYLA)
    spin_strike.effect_headers[ayla_bat_index] = tail_spin.effect_headers[0].get_copy()
    spin_strike.effect_mps[ayla_bat_index] = tail_spin.effect_mps[0]
    tech_man.set_tech_by_id(spin_strike, ctenums.TechID.SPIN_STRIKE)

    # Lifeline
    # Uses Cyclone as a learn requirement and a menu mp requirement.
    # However it uses Effect 0x10 (Marle’s Life2) for effect/mp for Crono
    # The result is that Crono ends up using 15 MP for lifeline (not one of his tech mp values)
    #   and the menu shows it costing only 2.
    # Fix: Have Crono use cyclone
    lifeline = tech_man.get_tech(ctenums.TechID.LIFE_LINE)
    crono_bat_index = lifeline.battle_group.index(ctenums.CharID.CRONO)
    marle_bat_index = lifeline.battle_group.index(ctenums.CharID.MARLE)

    # Copy Cyclone in for Crono's spot
    lifeline.control_header.set_effect_index(crono_bat_index, ctenums.TechID.CYCLONE)
    lifeline.control_header.set_effect_mp_only(crono_bat_index, True)
    cyclone = tech_man.get_tech(ctenums.TechID.CYCLONE)
    lifeline.effect_headers[crono_bat_index] = cyclone.effect_headers[0]
    lifeline.effect_mps[crono_bat_index] = cyclone.effect_mps[0]
    tech_man.set_tech_by_id(lifeline, ctenums.TechID.LIFE_LINE)

    # Slurpcut Combos - X-Strike, Blade Toss, 3D-Attack, Triple Raid
    # Combo techs using slurp cut do not apply Frog Weapon effects.  Fix it.
    tech_ids = (ctenums.TechID.X_STRIKE, ctenums.TechID.BLADE_TOSS,
                ctenums.TechID.THREE_D_ATTACK, ctenums.TechID.TRIPLE_RAID)
    for tech_id in tech_ids:
        slurpcut_tech = tech_man.get_tech(tech_id)
        frog_bat_index = slurpcut_tech.battle_group.index(ctenums.CharID.FROG)
        slurpcut_tech.effect_headers[frog_bat_index].applies_on_hit_effects = True
        tech_man.set_tech_by_id(slurpcut_tech, tech_id)

    # Same for confuse combo techs
    tech_ids = (ctenums.TechID.ICE_SWORD_2, ctenums.TechID.FIRE_SWORD_2)
    for tech_id in tech_ids:
        confuse_tech = tech_man.get_tech(tech_id)
        crono_bat_index = confuse_tech.battle_group.index(ctenums.CharID.CRONO)
        confuse_tech.effect_headers[crono_bat_index].applies_on_hit_effects = True
        tech_man.set_tech_by_id(confuse_tech, tech_id)
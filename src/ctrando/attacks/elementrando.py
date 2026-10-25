"""Module for reassigning elemental techs."""

import copy
from collections.abc import Iterable
import dataclasses
import enum
import itertools

from ctrando.arguments.characteroptions import TechRandoScheme, CharacterOptions

from ctrando.attacks import pctech, animationscript, animationcommands as ac
from ctrando.characters import ctpcstats
from ctrando.common import byteops, ctenums, ctrom
from ctrando.common.random import RNGType
from ctrando.items import itemdata


class TechElement(enum.Enum):
    LIGHTNING = enum.auto()
    FIRE = enum.auto()
    ICE = enum.auto()
    WATER = enum.auto()
    SHADOW = enum.auto()


# This is a dictionary for replacing animations.
# Given if character X originally did animation Y, and now character Z needs to do
# an analogous animation, the replacement animation id is _anim_replacements[X][Y][Z]
# If there is no need to replace the entry will not exist at some level.
_anim_replacements: dict[ctenums.CharID, dict[int, dict[ctenums.CharID, int]]] = {
    ctenums.CharID.LUCCA: {
        # 0x3C: Not sure, only used in Flare for one frame?
        0x3C: {
            ctenums.CharID.CRONO: 0x9F,
            ctenums.CharID.FROG: 0x22,
            ctenums.CharID.MAGUS: 0x22

        },
        # 0x45: Hold hands at the ready
        0x45: {
            ctenums.CharID.CRONO: 0x10,
            ctenums.CharID.MARLE: 0x10,
            ctenums.CharID.FROG: 0x1A,
        },
        # 0x46: Arms up as powering up flare
        0x46: {
            ctenums.CharID.CRONO: 0x22,
            ctenums.CharID.MARLE: 0x36,
            ctenums.CharID.FROG: 0x22,
            ctenums.CharID.MAGUS: 0x36,
        },
        # 0x43: Cross arms as flare goes off
        0x43: {
            ctenums.CharID.CRONO: 0x47,
            ctenums.CharID.MARLE: 0x35,
            ctenums.CharID.FROG: 0x0B,
            ctenums.CharID.MAGUS: 0x22
        }
    },
    ctenums.CharID.MARLE: {
        # 0x35: Arms out while ice is travelling
        0x35: {
            ctenums.CharID.CRONO: 0x41,  # Sword down hair blowing
            # 11 one arm up static, 1A laugh, 21 glasses, 22 arms crossed chanting
            # 23 protect arms up, 39 weird conductor
            # 46 hands up cast (good)
            ctenums.CharID.LUCCA: 0x23,
            ctenums.CharID.FROG: 0x1A,
            ctenums.CharID.MAGUS: 0x22,
        },
        # 0x36: Praying while powering up spell
        0x36: {
            ctenums.CharID.CRONO: 0x10,  # No really great ones
            ctenums.CharID.LUCCA: 0x46,
            # 0B Flex, 11 hold arms up, 1A laugh, 22 float and cast
            # 40 holding up masa
            ctenums.CharID.FROG: 0x22,
        }
    },
    ctenums.CharID.FROG: {
        # 0x1A: Laugh before water 2
        0x1A: {
            ctenums.CharID.CRONO: 0x44
        },
        # 0x41: Still frame of casting animation
        0x41: {
            ctenums.CharID.MAGUS: 0x38  # Point
        }
    },
    ctenums.CharID.MAGUS: {
        # 0x36: Magus spellcasting animation
        0x36: {
            ctenums.CharID.CRONO: 0x10,
            ctenums.CharID.LUCCA: 0x46,
            ctenums.CharID.FROG: 0x22
        },
        # 0x38: Magus pointing after dark bomb
        0x38: {
            ctenums.CharID.CRONO: 0xB,
            ctenums.CharID.MARLE: 0x35,
            ctenums.CharID.LUCCA: 0x0B,
            ctenums.CharID.FROG: 0x0B,
        }
    }
}

def get_replacement_animation_id(
        orig_char_id: ctenums.CharID,
        new_char_id: ctenums.CharID,
        animation_id: int
) -> int:
    """
    Given that orig_char_id performed animation_id in some script, this function
    returns an analogous animation_id for new_char_id to perform.
    """
    repl_dict = _anim_replacements.get(orig_char_id, dict())
    anim_id_dict = repl_dict.get(animation_id, dict())
    repl_anim = anim_id_dict.get(new_char_id, animation_id)
    return repl_anim


_elem_progression: dict[TechElement, tuple[ctenums.TechID, ...]] = {
    TechElement.LIGHTNING: (ctenums.TechID.LIGHTNING, ctenums.TechID.LIGHTNING_2,
                            ctenums.TechID.LUMINAIRE),
    TechElement.FIRE: (ctenums.TechID.FIRE, ctenums.TechID.FIRE_2,
                       ctenums.TechID.FLARE),
    TechElement.ICE: (ctenums.TechID.ICE, ctenums.TechID.ICE_2),
    TechElement.WATER: (ctenums.TechID.WATER, ctenums.TechID.WATER_2),
    TechElement.SHADOW: (ctenums.TechID.DARK_BOMB, ctenums.TechID.DARK_MIST,
                         ctenums.TechID.DARK_MATTER)
}

def replace_animations(
        anim_script: animationscript.PCTechAnimationScript,
        from_pc: ctenums.CharID,
        to_pc: ctenums.CharID,
        caster_id: int = 0
):
    """Reassign animation commands in a script from one pc to another"""
    if from_pc == to_pc:
        return

    caster_obj = anim_script.main_script.caster_objects[caster_id]

    for cmd in caster_obj:
        if isinstance(cmd, ac._PlayAnimationBase):
             cmd.animation_id = get_replacement_animation_id(
                 from_pc, to_pc, cmd.animation_id
             )


@dataclasses.dataclass
class _TechData:
    tech: pctech.PCTech
    script: animationscript.PCTechAnimationScript


def make_hex_mist_data(
        tech_man: pctech.PCTechManager,
        ct_rom: ctrom.CTRom,
        element: TechElement
) -> _TechData:
    """Returns _Techdata (tech + script) for Hexagon Mist"""
    if element == TechElement.WATER:
        base_tech = tech_man.get_tech(ctenums.TechID.WATER_2)
    elif element == TechElement.ICE:
        base_tech = tech_man.get_tech(ctenums.TechID.ICE_2)
    else:
        raise ValueError

    script_id = base_tech.graphics_header.script_id
    base_animation = animationscript.PCTechAnimationScript.read_from_ctrom(ct_rom, script_id)
    if element == TechElement.WATER:
        caster_obj = base_animation.main_script.caster_objects[0]
        caster_obj[6:14] = [
            ac.IncrementCounter1D(),
            ac.WaitForCounter1DValue(value=2),
            ac.PlaySound(sound=0xC3),
            ac.IncrementCounter(counter=0x1B),
            ac.Pause(duration=0x78),
            ac.PlaySound(sound=0xC4),
            ac.IncrementCounter(counter=0x1A),
            ac.PlaySound(sound=0xC5),
            ac.IncrementCounter(counter=0x19),
            ac.WaitForCounterValue(counter=0x1B, value=0),
            ac.WaitForCounter1DValue(value=3),
            ac.IncrementCounter1D(),
            ac.PlayAnimationFirstFrame(animation_id=0x03),
            ac.WaitForCounter1DValue(value=5)
        ]

        base_animation.main_script.target_objects[0][0] = ac.WaitForCounter1DValue(value=4)
        base_animation.main_script.target_objects[1][0] = ac.WaitForCounter1DValue(value=4)
    elif element == TechElement.ICE:
        caster_obj = base_animation.main_script.caster_objects[0]
        caster_obj[3:13] = [
            ac.WaitForCounter1DValue(value=2),
            ac.WaitForCounter1DValue(value=2),
            ac.PlaySound(sound=0xC3),
            ac.IncrementCounter(counter=0x1B),
            ac.IncrementCounter1D(),
            ac.Pause(duration=0x78),
            ac.PlaySound(sound=0xC4),
            ac.IncrementCounter(counter=0x1A),
            ac.PlaySound(sound=0xC5),
            ac.IncrementCounter(counter=0x19),
            ac.WaitForCounterValue(counter=0x1B, value=0),
            # ac.WaitForCounter1DValue(value=3),
            ac.PlayAnimationFirstFrame(animation_id=0x03),
            # ac.WaitForCounter1DValue(value=5)
        ]

    base_tech = copy.deepcopy(base_tech)
    base_tech.graphics_header.layer3_packet_id = 0x04
    base_tech.effect_headers[0].power = 0x2A  # Match Flare
    base_tech.effect_mps[0] = 20
    base_tech.name = "*Hex Mist"

    return _TechData(base_tech, base_animation)


def get_char_rando_elem_assignment(
        rando_scheme: TechRandoScheme,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        rng: RNGType
) -> dict[ctenums.CharID, TechElement]:

    char_id_pool = [ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                    ctenums.CharID.LUCCA, ctenums.CharID.FROG,
                    ctenums.CharID.MAGUS]
    elem_pool = [TechElement.LIGHTNING, TechElement.ICE,
                 TechElement.FIRE, TechElement.WATER,
                 TechElement.SHADOW]

    base_elem_dict = {
        k: v for k,v in zip(char_id_pool, elem_pool)
    }
    vanilla_elem_dict = {
        char_id: base_elem_dict[reassign_dict[char_id]]
        for char_id in ctenums.CharID
        if reassign_dict[char_id] in base_elem_dict
    }

    if rando_scheme == TechRandoScheme.VANILLA:
        return vanilla_elem_dict

    if rando_scheme == TechRandoScheme.SHUFFLE_ELEMENT:
        existing_elems = list(vanilla_elem_dict.values())
        rng.shuffle(existing_elems)
        return dict(zip(vanilla_elem_dict.keys(), existing_elems,
                        strict=True))

    if rando_scheme == TechRandoScheme.RANDOM_ELEMENT:
        return {
            char_id: rng.choice(elem_pool) for char_id in vanilla_elem_dict
        }

    raise ValueError


_techelem_to_elem_dict: dict[TechElement, ctenums.Element] = {
        TechElement.LIGHTNING: ctenums.Element.LIGHTNING,
        TechElement.FIRE: ctenums.Element.FIRE,
        TechElement.WATER: ctenums.Element.ICE,
        TechElement.ICE: ctenums.Element.ICE,
        TechElement.SHADOW: ctenums.Element.SHADOW
}


def write_elem_resistances(
        stat_man: ctpcstats.PCStatsManager,
        elem_assignment: dict[ctenums.CharID, TechElement | None]
):
    """If a characters has been assigned a new element, update their innate resistance."""
    for pc_id, tech_elem in elem_assignment.items():
        if tech_elem is None:
            continue
        elem = _techelem_to_elem_dict[tech_elem]
        stat_man.pc_stat_dict[pc_id].stat_block.innate_element_resisted = elem


def write_menu_element_graphics(
        ct_rom: ctrom.CTRom,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        tech_man: pctech.PCTechManager,
        tech_rando_scheme: TechRandoScheme
):
    """Update the element graphics in the menu."""
    elem_assignment = read_elem_assignment(reassign_dict, tech_man, tech_rando_scheme)

    orig_indices: dict[ctenums.Element, int] = {
        ctenums.Element.LIGHTNING: 0,
        ctenums.Element.SHADOW: 2,
        ctenums.Element.ICE: 4,
        ctenums.Element.FIRE: 6,
        ctenums.Element.NONELEMENTAL: 8
    }

    reassign: list[int] = []
    for pc_id in ctenums.CharID:
        elem = elem_assignment[pc_id]
        if elem is None:
            new_elem = ctenums.Element.NONELEMENTAL
        else:
            new_elem = _techelem_to_elem_dict[elem]

        reassign.append(orig_indices[new_elem])

    reassign_b = bytes(reassign)
    reassign_addr = ct_rom.space_manager.get_free_addr(len(reassign_b))
    reassign_rom_addr = byteops.to_rom_ptr(reassign_addr)

    ct_rom.seek(reassign_addr)
    ct_rom.write(reassign_b, ctrom.freespace.FSWriteType.MARK_USED)

    # fix menu magic type picture
    # $C2/A27C BF C6 A2 C2 LDA $C2A2C6,x[$C2:A2C6]
    # X has the pc-index which needs to be reeassigned
    ct_rom.seek(0x02A27D)
    ct_rom.write(reassign_rom_addr.to_bytes(3, "little"))


def read_elem_assignment(
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        tech_man: pctech.PCTechManager,
        tech_rando_scheme: TechRandoScheme
) -> dict[ctenums.CharID, TechElement | None]:  # Maybe should be ctenums.Element instead
    """
    Determine an elemental assignment given tech_man.  This is necessary because we do
    not store elemental assignment directly (duplicate data given tech_man).
    """
    char_id_pool = [ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                    ctenums.CharID.LUCCA,
                    ctenums.CharID.ROBO,
                    ctenums.CharID.FROG,
                    ctenums.CharID.AYLA,
                    ctenums.CharID.MAGUS]
    elem_pool = [TechElement.LIGHTNING, TechElement.ICE,
                 TechElement.FIRE,
                 None,
                 TechElement.WATER,
                 None,
                 TechElement.SHADOW]

    vanilla_dict = dict(zip(char_id_pool, elem_pool))

    if tech_rando_scheme in (TechRandoScheme.VANILLA, TechRandoScheme.CHAOS_ELEMENT):
        # We really should handle this better.  Maybe top MP spell gives element?
        return vanilla_dict

    ret_dict: dict[ctenums.CharID, TechElement | None] = {}
    for char_id, reassign_id in reassign_dict.items():
        vanilla_elem = vanilla_dict[reassign_dict[char_id]]
        if vanilla_elem is None:
            ret_dict[char_id] = None
            continue

        start = 1 + char_id*8
        end = start+8

        names = set(tech_man.get_tech(tech_id).name for tech_id in range(start, end))
        if reassign_id == ctenums.CharID.MAGUS:
            if "*Flare" in names:
                ret_dict[char_id] = TechElement.FIRE
            elif "*Luminaire" in names:
                ret_dict[char_id] = TechElement.LIGHTNING
            elif "*Hex Mist" in names:
                ret_dict[char_id] = TechElement.WATER
            else:
                ret_dict[char_id] = TechElement.SHADOW
        else:
            if names.intersection(("*Lightning", "*Lightning2", "*Luminaire")):
                ret_dict[char_id] = TechElement.LIGHTNING
            elif names.intersection(("*Ice", "*Ice 2")):
                ret_dict[char_id] = TechElement.ICE
            elif names.intersection(("*Water", "*Water 2")):
                ret_dict[char_id] = TechElement.WATER
            elif names.intersection(("*Fire", "*Fire 2", "*Flare")):
                ret_dict[char_id] = TechElement.FIRE
            elif names.intersection(("*Dark Bomb", "*Dark Mist", "*DarkMatter")):
                ret_dict[char_id] = TechElement.SHADOW
            else:
                raise ValueError

    return ret_dict


def update_rock_usability(
        tech_man: pctech.PCTechManager,
        item_man: itemdata.ItemDB
):
    first_rock_tech = tech_man.num_techs - tech_man.num_rock_techs

    rock_usage: dict[ctenums.ItemID, set[ctenums.CharID]] = {
        rock_id: set() for rock_id in (
            ctenums.ItemID.BLACK_ROCK, ctenums.ItemID.BLUE_ROCK,
            ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
            ctenums.ItemID.GOLD_ROCK
        )
    }

    for tech_id in range(first_rock_tech, tech_man.num_techs):
        tech = tech_man.get_tech(tech_id)
        if tech.rock_used is not None:
            rock_usage[tech.rock_used].update(tech.battle_group.to_char_ids())

    for rock_id in (ctenums.ItemID.BLACK_ROCK, ctenums.ItemID.BLUE_ROCK,
                    ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
                    ctenums.ItemID.GOLD_ROCK):

        chars_used = rock_usage.get(rock_id, [])
        if chars_used:
            item_man.item_dict[rock_id].secondary_stats.set_equipable_by(chars_used)
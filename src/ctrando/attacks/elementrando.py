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
        # 0x3: {
        #     # ctenums.CharID.CRONO: 0x48
        # },
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
        anim_script: animationscript.AnimationScript,
        from_pc: ctenums.CharID,
        to_pc: ctenums.CharID,
        caster_id: int = 0
):
    """Reassign animation commands in a script from one pc to another"""
    caster_obj = anim_script.main_script.caster_objects[caster_id]

    for cmd in caster_obj:
        if isinstance(cmd, ac._PlayAnimationBase):
             cmd.animation_id = get_replacement_animation_id(
                 from_pc, to_pc, cmd.animation_id
             )


@dataclasses.dataclass
class _TechData:
    tech: pctech.PCTech
    script: animationscript.AnimationScript


def _make_hex_mist_data(
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

    hex_cast: animationscript.ObjectScript = [
        ac.SetObjectFacing(facing=0xD),
        ac.PlayAnimationOnce(animation_id=7),
        ac.PlaySound(sound=0xC3),
        ac.IncrementCounter(counter=0x1B),
        ac.Pause(duration=0x78),
        ac.PlaySound(sound=0xC4),
        ac.IncrementCounter(counter=0x1A),
        ac.PlaySound(sound=0xC5),
        ac.IncrementCounter(counter=0x19),
        ac.WaitForCounterValue(counter=0x1B, value=0),
        ac.IncrementCounter1D(),
        ac.PlayAnimationFirstFrame(animation_id=0x03),
        ac.Pause(duration=0x0F),
        ac.ShowDamage(),
        ac.Unknown2E(),
        ac.EndTech(),
        ac.ReturnCommand()
    ]
    script_id = base_tech.graphics_header.script_id
    base_animation = animationscript.AnimationScript.read_from_ctrom(ct_rom, script_id)
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
    base_tech.name = "*Hex Mist"

    return _TechData(base_tech, base_animation)


def get_elem_assignment(
        rando_scheme: TechRandoScheme,
        rng: RNGType
) -> dict[ctenums.CharID, TechElement]:
    """
    Produces a random elemental assignment using the given scheme (unless chaos_element).
    """
    char_id_pool = [ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                    ctenums.CharID.LUCCA, ctenums.CharID.FROG,
                    ctenums.CharID.MAGUS]
    elem_pool = [TechElement.LIGHTNING, TechElement.ICE,
                 TechElement.FIRE, TechElement.WATER,
                 TechElement.SHADOW]

    if rando_scheme in (TechRandoScheme.VANILLA, TechRandoScheme.CHAOS_ELEMENT):
        chosen_elems = list(elem_pool)
    elif rando_scheme == TechRandoScheme.SHUFFLE_ELEMENT:
        chosen_elems = list(elem_pool)
        rng.shuffle(chosen_elems)
    elif rando_scheme == TechRandoScheme.RANDOM_ELEMENT:
        chosen_elems = rng.choices(elem_pool, k=len(char_id_pool))
    else:
        raise ValueError

    return {char: elem for char, elem in zip(char_id_pool, chosen_elems)}


def reassign_elemental_single_techs(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        elem_assignment: dict[ctenums.CharID, TechElement],
        ct_rom: ctrom.CTRom,
        rng: RNGType
):
    """
    Modifies the single techs in tech_man to match the elemental assignment.
    Also stores the updated animation scripts in animation_script_man.
    """
    element_name_progression: dict[TechElement, tuple[str, str, str]] = {
        TechElement.LIGHTNING: ("*Lightning", "*Lightning2", "*Luminaire"),
        TechElement.ICE: ("*Ice", "*Ice 2", "*Hex Mist"),
        TechElement.FIRE: ("*Fire", "*Fire 2", "*Flare"),
        TechElement.WATER: ("*Water", "*Water 2", "*Hex Mist"),
        TechElement.SHADOW: ("*Dark Bomb", "*Dark Mist", "*DarkMatter")
    }

    vanilla_pc_elem_dict: dict[ctenums.CharID, TechElement] = {
        ctenums.CharID.CRONO: TechElement.LIGHTNING,
        ctenums.CharID.MARLE: TechElement.ICE,
        ctenums.CharID.LUCCA: TechElement.FIRE,
        ctenums.CharID.FROG: TechElement.WATER,
        ctenums.CharID.MAGUS: TechElement.SHADOW
    }
    vanilla_pc_elem_dict_inv = {val: key for key, val in vanilla_pc_elem_dict.items()}

    base_tech_man = pctech.PCTechManager.read_from_ctrom(ct_rom)

    def get_tech_data(_tech_id: int) -> _TechData:
        _tech = base_tech_man.get_tech(_tech_id)
        _script_id = _tech.graphics_header.script_id
        return _TechData(
            _tech,
            animationscript.AnimationScript.read_from_ctrom(ct_rom, _script_id)
        )

    orig_data: dict[TechElement, tuple[_TechData, _TechData, _TechData]] = {
        TechElement.LIGHTNING: (
            get_tech_data(ctenums.TechID.LIGHTNING),
            get_tech_data(ctenums.TechID.LIGHTNING_2),
            get_tech_data(ctenums.TechID.LUMINAIRE)
        ),
        TechElement.ICE: (
            get_tech_data(ctenums.TechID.ICE),
            get_tech_data(ctenums.TechID.ICE_2),
            _make_hex_mist_data(tech_man, ct_rom, TechElement.ICE)
        ),
        TechElement.FIRE: (
            get_tech_data(ctenums.TechID.FIRE),
            get_tech_data(ctenums.TechID.FIRE_2),
            get_tech_data(ctenums.TechID.FLARE)
        ),
        TechElement.WATER: (
            get_tech_data(ctenums.TechID.WATER),
            get_tech_data(ctenums.TechID.WATER_2),
            _make_hex_mist_data(tech_man, ct_rom, TechElement.WATER)
        ),
        TechElement.SHADOW: (
            get_tech_data(ctenums.TechID.DARK_BOMB),
            get_tech_data(ctenums.TechID.DARK_MIST),
            get_tech_data(ctenums.TechID.DARK_MATTER)
        )
    }

    for char_id, orig_elem in vanilla_pc_elem_dict.items():
        if char_id not in elem_assignment:
            continue
        new_elem = elem_assignment[char_id]
        if new_elem == orig_elem:
            continue

        names_to_replace = element_name_progression[orig_elem]
        if char_id == ctenums.CharID.MAGUS:
            if new_elem != TechElement.WATER:
                names_to_replace = ("*Dark Bomb", None, "*DarkMatter",)

        start_id = char_id*8 + 1
        for tech_id in range(start_id, start_id+8):
            tech = tech_man.get_tech(tech_id)
            if tech.name not in names_to_replace:
                continue

            name_ind = names_to_replace.index(tech.name)
            repl_data: _TechData = orig_data[new_elem][name_ind]
            old_script_id = tech.graphics_header.script_id
            new_tech = copy.deepcopy(repl_data.tech)
            new_script = copy.deepcopy(repl_data.script)
            orig_pc = new_tech.battle_group.to_char_ids()[0]
            replace_animations(new_script, orig_pc, char_id)

            new_tech.battle_group[0] = char_id
            new_tech.control_header.set_effect_index(0, tech_id)
            new_tech.graphics_header.script_id = old_script_id
            animation_script_man.script_dict[old_script_id] = new_script
            tech_man.set_tech_by_id(new_tech, tech_id)

            animation_script_man.script_dict[old_script_id] = new_script
            tech_man.set_tech_by_id(new_tech, tech_id)


def chaos_reassign_elemental_single_techs(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        ct_rom: ctrom.CTRom,
        rng: RNGType
):
    """
    Modifies the single techs in tech_man by shuffling all elemental techs among
    characters.  A character can not receive two versions of the same tech as
    there are two Lit/Fire/Ice-2 spells.
    """

    # Think about removing duplication of this small function
    def get_tech_data(_tech_id: int) -> _TechData:
        _tech = tech_man.get_tech(_tech_id)
        _script_id = _tech.graphics_header.script_id
        return _TechData(
            _tech,
            animationscript.AnimationScript.read_from_ctrom(ct_rom, _script_id)
        )

    elem_names = (
        "*Lightning", "*Lightning2", "*Luminaire",
        "*Ice", "*Ice 2",
        "*Fire", "*Fire 2", "*Flare",
        "*Water", "*Water 2",
        "*Dark Bomb", "*Dark Mist", "*DarkMatter"
    )

    char_elem_usage: dict[ctenums.CharID, list[ctenums.TechID]] = {}
    for char_id in (ctenums.CharID.CRONO, ctenums.CharID.MARLE, ctenums.CharID.LUCCA,
                    ctenums.CharID.FROG, ctenums.CharID.MAGUS):
        char_elem_usage[char_id] = []
        start_id = 1+char_id*8
        end_id = start_id+8
        for tech_id in range(start_id, end_id):
            tech = tech_man.get_tech(tech_id)
            if tech.name in elem_names:
                char_elem_usage[char_id].append(ctenums.TechID(tech_id))


    char_elem_usage: dict[ctenums.CharID, tuple[ctenums.TechID, ...]] = {
        ctenums.CharID.CRONO: (ctenums.TechID.LIGHTNING, ctenums.TechID.LIGHTNING_2, ctenums.TechID.LUMINAIRE,),
        ctenums.CharID.MARLE: (ctenums.TechID.ICE, ctenums.TechID.ICE_2,),
        ctenums.CharID.LUCCA: (ctenums.TechID.FIRE, ctenums.TechID.FIRE_2, ctenums.TechID.FLARE,),
        ctenums.CharID.FROG: (ctenums.TechID.WATER, ctenums.TechID.WATER_2,),
        ctenums.CharID.MAGUS: (
            ctenums.TechID.LIGHTNING_2_M, ctenums.TechID.FIRE_2_M, ctenums.TechID.ICE_2_M,
            ctenums.TechID.DARK_BOMB, ctenums.TechID.DARK_MIST, ctenums.TechID.DARK_MATTER)
    }
    elem_capacity: dict[ctenums.CharID, int] = {
        key: len(val) for key,val in char_elem_usage.items()
    }
    elem_assignment: dict[ctenums.CharID, list[ctenums.TechID]] = {
        x: [] for x in char_elem_usage.keys()
    }

    elem_tech_ids: list[ctenums.TechID] = [
        ctenums.TechID.LIGHTNING, ctenums.TechID.LIGHTNING_2, ctenums.TechID.LUMINAIRE,
        ctenums.TechID.FIRE, ctenums.TechID.FIRE_2, ctenums.TechID.FLARE,
        ctenums.TechID.ICE, ctenums.TechID.ICE_2,
        ctenums.TechID.WATER, ctenums.TechID.WATER_2,
        ctenums.TechID.LIGHTNING_2_M, ctenums.TechID.ICE_2_M, ctenums.TechID.FIRE_2_M,
        ctenums.TechID.DARK_BOMB, ctenums.TechID.DARK_MIST, ctenums.TechID.DARK_MATTER
    ]

    duplicates: tuple[tuple[ctenums.TechID, ctenums.TechID], ...] = (
        (ctenums.TechID.LIGHTNING_2, ctenums.TechID.LIGHTNING_2_M),
        (ctenums.TechID.ICE_2, ctenums.TechID.ICE_2_M),
        (ctenums.TechID.FIRE_2, ctenums.TechID.FIRE_2_M)
    )

    tech_pool: list[ctenums.TechID] = list(elem_tech_ids)
    char_pool = [ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                 ctenums.CharID.LUCCA, ctenums.CharID.FROG,
                 ctenums.CharID.MAGUS]

    for dup_pair in duplicates:
        chosen_chars = rng.sample(char_pool, k=2)
        for tech, char in zip(dup_pair, chosen_chars):
            elem_assignment[char].append(tech)
            tech_pool.remove(tech)
            if len(elem_assignment[char]) >= elem_capacity[char]:
                char_pool.remove(char)

    for tech in tech_pool:
        char = rng.choice(char_pool)
        elem_assignment[char].append(tech)
        if len(elem_assignment[char]) >= elem_capacity[char]:
            char_pool.remove(char)

    orig_data: dict[ctenums.TechID, _TechData] = {
        tech_id: get_tech_data(tech_id) for tech_id in elem_tech_ids
    }


    def get_new_data(_char_id: ctenums.CharID, _tech_id: ctenums.TechID) -> _TechData:
        for _dup_pair in duplicates:
            if _tech_id in _dup_pair:
                if _char_id == ctenums.CharID.MAGUS:
                    _tech_id = _dup_pair[1]
                else:
                    _tech_id = _dup_pair[0]
                break

        return orig_data[_tech_id]

    for char_id, assignment in elem_assignment.items():
        orig_techs = char_elem_usage[char_id]

        for old_tech_id, new_tech_id in zip(orig_techs, assignment):
            repl_data = get_new_data(char_id, new_tech_id)

            old_script_id = orig_data[old_tech_id].tech.graphics_header.script_id
            new_tech = copy.deepcopy(repl_data.tech)
            new_script = copy.deepcopy(repl_data.script)
            orig_pc = new_tech.battle_group.to_char_ids()[0]
            replace_animations(new_script, orig_pc, char_id)

            new_tech.battle_group[0] = char_id
            new_tech.control_header.set_effect_index(0, old_tech_id)
            new_tech.graphics_header.script_id = old_script_id
            animation_script_man.script_dict[old_script_id] = new_script
            tech_man.set_tech_by_id(new_tech, old_tech_id)


def get_reassign_techs(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        item_man: itemdata.ItemDB,
        ct_rom: ctrom.CTRom,  # For script lookups
        use_magus_duals: bool,
        tech_random_scheme: TechRandoScheme,
        elem_assignment: dict[ctenums.CharID, TechElement],
        rng: RNGType
):
    """
    Does the full modification of tech_man, animation_script_man, and item_man to
    implement the given tech_random_scheme (with derived elem_assignment).
    - Update all single techs with the given scheme.
    - Rebuild all combo techs (from tech_man) with eligible characters
    - Reindex animation script and record the updated scripts in animation_script_man
    - Update rock equipability to reflect who can perform the techs.
    """
    all_techs = tech_man.get_all_techs()
    combo_techs = {tech_id: tech for tech_id, tech in all_techs.items()
                   if tech.num_pcs > 1}
    combo_tech_scripts: dict[int, animationscript.AnimationScript] = {}

    for tech_id, tech in combo_techs.items():
        script_id = tech.graphics_header.script_id
        combo_tech_scripts[script_id] = animationscript.AnimationScript.read_from_ctrom(
            ct_rom, script_id)

    tech_char_usage: dict[int, dict[ctenums.CharID, str]] = {}
    for tech_id, tech in combo_techs.items():
        tech_usage: dict[ctenums.CharID, str] = {}
        for mp_req in tech.menu_mp_reqs:
            char_id = ctenums.CharID((mp_req - 1) // 8)
            part = all_techs[mp_req]
            tech_usage[char_id] = part.name

        tech_char_usage[tech_id] = tech_usage

    if tech_random_scheme in (
        TechRandoScheme.RANDOM_ELEMENT, TechRandoScheme.SHUFFLE_ELEMENT,
        TechRandoScheme.VANILLA
    ):
        reassign_elemental_single_techs(tech_man, animation_script_man,
                                        elem_assignment, ct_rom, rng)
    elif tech_random_scheme == TechRandoScheme.CHAOS_ELEMENT:
        chaos_reassign_elemental_single_techs(tech_man, animation_script_man, ct_rom, rng)
    else:
        raise ValueError

    # Now tech_man has the correct, new single techs.  Get all possible combo techs.
    new_combo_techs = make_new_combo_techs(
        tech_man, combo_techs, combo_tech_scripts, tech_char_usage,
        use_magus_duals
    )

    for chars, techs in new_combo_techs.items():
        bitmask = pctech.ctt.PCTechBattleGroup.from_charids(list(chars)).to_bitmask()
        tech_man.remove_bitmask(bitmask)

    rock_usage: dict[ctenums.ItemID, set[ctenums.CharID]] = {
        rock_id: set() for rock_id in (
            ctenums.ItemID.BLACK_ROCK, ctenums.ItemID.BLUE_ROCK,
            ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
            ctenums.ItemID.GOLD_ROCK
        )
    }

    cur_script_id = 0x39
    for chars, techs in new_combo_techs.items():
        if len(chars) == 2:
            num_techs = 3
        elif len(chars) == 3:
            num_techs = 1
        else:
            raise ValueError

        if len(techs) <= num_techs:
            chosen_data = techs
        else:
            chosen_data = rng.sample(techs, num_techs)

        for tech_data in chosen_data:
            tech = tech_data.tech
            tech.graphics_header.script_id = cur_script_id
            animation_script_man.script_dict[cur_script_id] = tech_data.script
            cur_script_id += 1
            if cur_script_id == 0x75:  # don't overwrite some hard-coded script ids
                cur_script_id = 0x81
            tech_man.add_tech(tech)

            if tech.rock_used is not None:
                rock_usage[tech.rock_used].update(
                    tech.battle_group.to_char_ids()
                )

    update_rock_usability(item_man, rock_usage)


def make_new_combo_techs(
        tech_man: pctech.PCTechManager,
        combo_techs: dict[int, pctech.PCTech],
        combo_tech_scripts: dict[int, animationscript.AnimationScript],
        char_tech_usage: dict[int, dict[ctenums.CharID, str]],
        use_magus_duals: bool,
) -> dict[frozenset[ctenums.CharID], list[_TechData]]:
    """Make new combo techs given the single techs present."""

    # First store which tech names each character has
    char_tech_name_ind_dict: dict[ctenums.CharID, dict[str, int]] = {}
    for char_id in ctenums.CharID:
        start_id = 1+char_id*8
        name_dict: dict[str, int] = {}
        for ind in range(8):
            tech_id = start_id + ind
            tech = tech_man.get_tech(tech_id)
            name_dict[tech.name] = ind

        char_tech_name_ind_dict[char_id] = name_dict

    tech_group_dict: dict[frozenset[ctenums.CharID], list[_TechData]] = {}
    for dual_group in itertools.combinations(ctenums.CharID, 2):
        tech_group_dict[frozenset(dual_group)] = []

    for triple_group in itertools.combinations(ctenums.CharID, 3):
        tech_group_dict[frozenset(triple_group)] = []

    for tech_id, tech in combo_techs.items():
        char_options: dict[ctenums.CharID, tuple[ctenums.CharID, ...]] = {}
        tech_usage = char_tech_usage[tech_id]

        for char_id, name in tech_usage.items():
            options = tuple(
                char_id for char_id, tech_names in char_tech_name_ind_dict.items()
                if name in tech_names
            )
            char_options[char_id] = options

        chars = tuple(char_options.keys())
        for combo in itertools.product(
                *(char_options[x] for x in chars)
        ):
            if len(set(combo)) != tech.num_pcs:
                continue  # May happen if one character fills multiple roles

            # Filter out unallowed Magus combos techs:
            # 1) Any dual unless use_magus_duals
            # 2) Any non-rock triple
            if ctenums.CharID.MAGUS in combo:
                if tech.num_pcs == 2 and not use_magus_duals:
                    continue
                if tech.num_pcs == 3 and tech.rock_used is None:
                    continue

            # We should have a tuple of characters who can perform the tech now
            reassign_dict = {
                old_char: new_char for old_char, new_char in zip(chars, combo)
            }
            new_tech_ids: dict[ctenums.CharID, int] = {}
            for char_id, new_char_id in reassign_dict.items():
                old_effect_name = char_tech_usage[tech_id][char_id]
                new_tech_id = char_tech_name_ind_dict[new_char_id][old_effect_name]
                new_tech_id = 1 + new_char_id*8 + new_tech_id
                new_tech_ids[new_char_id] = new_tech_id

            reassigned_tech = get_reassigned_combo_tech(
                tech, tech_man, reassign_dict,
                new_tech_ids
            )

            script_id = tech.graphics_header.script_id
            script = copy.deepcopy(combo_tech_scripts[script_id])

            for ind, char in enumerate(reassigned_tech.battle_group.to_char_ids()):
                orig_char = tech.battle_group.to_char_ids()[ind]
                replace_animations(script, orig_char, char, ind)

            tech_group_dict[frozenset(reassign_dict.values())].append(
                _TechData(reassigned_tech, script))

    return tech_group_dict


def get_reassigned_combo_tech(
        tech: pctech.PCTech,
        tech_manager: pctech.PCTechManager,
        reassignment: dict[ctenums.CharID, ctenums.CharID],
        reassignment_tech_ids: dict[ctenums.CharID, int],
) -> pctech.PCTech:

    """
    Take an existing tech and assign it to a new group of characters.
    - reassignment tells how original characters should be reassigned to new characters
    - reassignment tech_ids tell which tech_ids the new characters will use in the new tech
    """
    tech = copy.deepcopy(tech)

    bat_grp_chars = tech.battle_group.to_char_ids()
    new_bat_grp_chars = [reassignment[x] for x in bat_grp_chars]
    new_bat_grp = pctech.ctt.PCTechBattleGroup.from_charids(new_bat_grp_chars)
    new_menu_mps = pctech.ctt.PCTechMenuMPReq(list(reassignment_tech_ids.values()))

    tech.battle_group = new_bat_grp
    tech.menu_mp_reqs = new_menu_mps

    for ind, char_id in enumerate(bat_grp_chars):
        reassign_char = reassignment[char_id]
        new_effect_tech_id = reassignment_tech_ids[reassign_char]
        new_effect_tech_level = ((new_effect_tech_id - 1) % 8) + 1

        single_tech = tech_manager.get_tech(new_effect_tech_id)

        orig_index = tech.control_header.get_effect_index(ind)
        if orig_index <= 1+7*8:
            tech.control_header.set_effect_index(ind, reassignment_tech_ids[reassign_char])
            tech.effect_headers[ind] = single_tech.effect_headers[0]
        tech.effect_mps[ind] = single_tech.effect_mps[0]

        if tech.rock_used is None:
            tech.set_learn_requirement(reassign_char, new_effect_tech_level)

    if tech.num_pcs == 3:
        tech.menu_mp_reqs = pctech.ctt.PCTechMenuMPReq(
            sorted(tech.menu_mp_reqs)
        )
    return tech


_techelem_to_elem_dict: dict[TechElement, ctenums.Element] = {
        TechElement.LIGHTNING: ctenums.Element.LIGHTNING,
        TechElement.FIRE: ctenums.Element.FIRE,
        TechElement.WATER: ctenums.Element.ICE,
        TechElement.ICE: ctenums.Element.ICE,
        TechElement.SHADOW: ctenums.Element.SHADOW
}


def write_elem_resistances(
        stat_man: ctpcstats.PCStatsManager,
        elem_assignment: dict[ctenums.CharID, TechElement]
):
    """If a characters has been assigned a new element, update their innate resistance."""
    for pc_id, tech_elem in elem_assignment.items():
        elem = _techelem_to_elem_dict[tech_elem]
        stat_man.pc_stat_dict[pc_id].stat_block.innate_element_resisted = elem


def write_menu_element_graphics(
        ct_rom: ctrom.CTRom,
        tech_man: pctech.PCTechManager,
        tech_rando_scheme: TechRandoScheme
):
    """Update the element graphics in the menu."""
    elem_assignment = read_elem_assignment(tech_man, tech_rando_scheme)

    orig_indices: dict[ctenums.Element, int] = {
        ctenums.Element.LIGHTNING: 0,
        ctenums.Element.SHADOW: 2,
        ctenums.Element.ICE: 4,
        ctenums.Element.FIRE: 6,
        ctenums.Element.NONELEMENTAL: 8
    }

    reassign: list[int] = []
    for pc_id in ctenums.CharID:
        if pc_id not in elem_assignment:
            elem = ctenums.Element.NONELEMENTAL
        else:
            elem = _techelem_to_elem_dict[elem_assignment[pc_id]]

        reassign.append(orig_indices[elem])

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
        tech_man: pctech.PCTechManager,
        tech_rando_scheme: TechRandoScheme
) -> dict[ctenums.CharID, TechElement]:  # Maybe should be ctenums.Element instead
    """
    Determine an elemental assignment given tech_man.  This is necessary because we do
    not store elemental assignment directly (duplicate data given tech_man).
    """
    char_id_pool = [ctenums.CharID.CRONO, ctenums.CharID.MARLE,
                    ctenums.CharID.LUCCA, ctenums.CharID.FROG,
                    ctenums.CharID.MAGUS]
    elem_pool = [TechElement.LIGHTNING, TechElement.ICE,
                 TechElement.FIRE, TechElement.WATER,
                 TechElement.SHADOW]

    vanilla_dict = dict(zip(char_id_pool, elem_pool))

    if tech_rando_scheme in (TechRandoScheme.VANILLA, TechRandoScheme.CHAOS_ELEMENT):
        return vanilla_dict

    ret_dict: dict[ctenums.CharID, TechElement] = {}
    for char_id, vanilla_elem in vanilla_dict.items():
        start = 1 + char_id*8
        end = start+8

        names = set(tech_man.get_tech(tech_id).name for tech_id in range(start, end))
        if char_id == ctenums.CharID.MAGUS:
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
        item_man: itemdata.ItemDB,
        rock_usage: dict[ctenums.ItemID, Iterable[ctenums.CharID]],
):
    for rock_id in (ctenums.ItemID.BLACK_ROCK, ctenums.ItemID.BLUE_ROCK,
                    ctenums.ItemID.SILVERROCK, ctenums.ItemID.WHITE_ROCK,
                    ctenums.ItemID.GOLD_ROCK):

        chars_used = rock_usage.get(rock_id, [])
        if chars_used:
            item_man.item_dict[rock_id].secondary_stats.set_equipable_by(chars_used)


def apply_full_tech_rando(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        item_man: itemdata.ItemDB,
        ct_rom: ctrom.CTRom,
        character_options: CharacterOptions,
        stats_man: ctpcstats.PCStatsManager,
        rng: RNGType
):
    elem_assignment = get_elem_assignment(character_options.tech_rando_scheme, rng)

    get_reassign_techs(
        tech_man, animation_script_man, item_man, ct_rom,
        character_options.use_magus_dual_techs,
        character_options.tech_rando_scheme,
        elem_assignment,
        rng
    )
    write_elem_resistances(stats_man, elem_assignment)

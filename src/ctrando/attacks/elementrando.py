"""Module for reassigning elemental techs."""
import copy
import dataclasses
import enum
import itertools

from ctrando.attacks import pctech, animationscript, animationcommands as ac
from ctrando.common import ctenums, ctrom
from ctrando.common.random import RNGType


class TechElement(enum.Enum):
    LIGHTNING = enum.auto()
    FIRE = enum.auto()
    ICE = enum.auto()
    WATER = enum.auto()
    SHADOW = enum.auto()

# Some notes on animations
# Crono:
#   - Fire: Fire1,2 are ok.  Flare needs work

_anim_replacements: dict[ctenums.CharID, dict[int, dict[ctenums.CharID, int]]] = {
    ctenums.CharID.LUCCA: {
        # 0x3: {
        #     # ctenums.CharID.CRONO: 0x48
        # },
        # 0x3C: Not sure, only used in Flare for one frame?
        0x3C: {
            ctenums.CharID.CRONO: 0x9F
        },
        # 0x45: Hold hands at the ready
        0x45: {
            ctenums.CharID.CRONO: 0x10
        },
        # 0x46: Arms up as powering up flare
        0x46: {
            ctenums.CharID.CRONO: 0x22
        },
        # 0x43: Cross arms as flare goes off
        0x43: {
            ctenums.CharID.CRONO: 0x47,
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
        }
    },
    ctenums.CharID.MAGUS: {
        # 0x36: Magus spellcasting animation
        0x36: {
            ctenums.CharID.CRONO: 0x10,
            ctenums.CharID.LUCCA: 0x46
        },
        # 0x38: Magus pointing after dark bomb
        0x38: {
            ctenums.CharID.CRONO: 0xB,
            ctenums.CharID.MARLE: 0x35,
            ctenums.CharID.LUCCA: 0x0B,
        }
    }

}

def get_replacement_animation_id(
        orig_char_id: ctenums.CharID,
        new_char_id: ctenums.CharID,
        animation_id: int
) -> int:
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


def get_reassign_techs(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        elem_assignment: dict[ctenums.CharID, TechElement],
        ct_rom: ctrom.CTRom,  # For script lookups
        use_magus_duals: bool,
        rng: RNGType
):
    element_name_progression: dict[TechElement, tuple[str, str, str]] ={
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
    vanilla_pc_elem_dict_inv = {val: key for key,val in vanilla_pc_elem_dict.items()}

    def get_tech_data(tech_id: int) -> _TechData:
        tech = tech_man.get_tech(tech_id)
        script_id = tech.graphics_header.script_id
        return _TechData(
            tech,
            animationscript.AnimationScript.read_from_ctrom(ct_rom, script_id)
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

    for char_id, orig_elem in vanilla_pc_elem_dict.items():
        if char_id not in elem_assignment:
            continue
        new_elem = elem_assignment[char_id]
        if new_elem == orig_elem:
            continue

        names_to_replace = element_name_progression[orig_elem]
        if char_id == ctenums.CharID.MAGUS:
            names_to_replace = ("*DarkMatter",)

        start_id = char_id*8 + 1
        for tech_id in range(start_id, start_id+8):
            tech = tech_man.get_tech(tech_id)
            if tech.name not in names_to_replace:
                continue

            name_ind = names_to_replace.index(tech.name)
            repl_data: _TechData = orig_data[new_elem][name_ind]

            new_tech = copy.deepcopy(repl_data.tech)
            new_script = copy.deepcopy(repl_data.script)
            orig_pc = new_tech.battle_group.to_char_ids()[0]
            replace_animations(new_script, orig_pc, char_id)

            old_script_id = tech.graphics_header.script_id
            tech.graphics_header = new_tech.graphics_header
            tech.graphics_header.script_id = old_script_id
            tech.name = new_tech.name

            tech.effect_headers[0].power = new_tech.effect_headers[0].power
            animation_script_man.script_dict[old_script_id] = new_script
            tech_man.set_tech_by_id(tech, tech_id)

    new_combo_techs = make_new_combo_techs(
        tech_man, combo_techs, combo_tech_scripts, tech_char_usage,
        use_magus_duals
    )

    for chars, techs in new_combo_techs.items():
        bitmask = pctech.ctt.PCTechBattleGroup.from_charids(list(chars)).to_bitmask()
        tech_man.remove_bitmask(bitmask)

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
            tech_man.add_tech(tech)


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
):
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

        tech.control_header.set_effect_index(ind, reassignment_tech_ids[reassign_char])
        tech.effect_headers[ind] = single_tech.effect_headers[0]
        tech.effect_mps[ind] = single_tech.effect_mps[0]

        if tech.rock_used is None:
            tech.set_learn_requirement(reassign_char, new_effect_tech_level)

    return tech


def get_tech_names(tech_man: pctech.PCTechManager):
    techs = tech_man.get_all_techs()

    num_singles = 8*7
    for ind, tech in techs.items():
        if tech.num_pcs == 1:
            continue
        names: list[str] = []
        for mp_req in tech.menu_mp_reqs:
            part = techs[mp_req]
            names.append(part.name)

        names_str = ", ".join(x for x in names)
        print(f"{tech.name}: {names}")
        input()


def test_scripts(
        tech_man: pctech.PCTechManager,
        anim_script_man: animationscript.AnimationScriptManager,
        ct_rom: ctrom.CTRom
):
    """Just force some script changes without anything else"""

    from_char = ctenums.CharID.FROG
    to_elem = TechElement.ICE

    crono_techs = _elem_progression[TechElement.WATER]
    to_techs = _elem_progression[to_elem]

    for old_tech_id, new_tech_id in zip(crono_techs, to_techs):
        old_tech = tech_man.get_tech(old_tech_id)
        new_tech = tech_man.get_tech(new_tech_id)

        orig_script_id = old_tech.graphics_header.script_id
        new_script_id = new_tech.graphics_header.script_id
        old_tech.graphics_header = new_tech.graphics_header
        old_tech.graphics_header.script_id = orig_script_id

        old_tech.name = new_tech.name

        new_script = animationscript.AnimationScript.read_from_ctrom(ct_rom, new_script_id)
        replace_animations(new_script, ctenums.CharID.MARLE, ctenums.CharID.FROG)

        anim_script_man.script_dict[orig_script_id] = new_script
        tech_man.set_tech_by_id(old_tech, old_tech_id)
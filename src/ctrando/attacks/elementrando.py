"""Module for reassigning elemental techs."""
import copy
import dataclasses
import enum

from ctrando.attacks import pctech, animationscript, animationcommands as ac
from ctrando.common import ctenums, ctrom


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
            ctenums.CharID.CRONO: 0x47
        }
    },
    ctenums.CharID.MARLE: {
        # 0x35: Arms out while ice is travelling
        0x35: {
            ctenums.CharID.CRONO: 0x40,
            # 11 one arm up static, 1A laugh, 21 glasses, 22 arms crossed chanting
            # 23 protect arms up, 39 weird conductor
            # 46 hands up cast (good)
            ctenums.CharID.LUCCA: 0x23,
            ctenums.CharID.FROG: 0x1A,
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
        caster_obj[8:14] = [
            ac.PlaySound(sound=0xC3),
            ac.IncrementCounter(counter=0x1B),
            ac.Pause(duration=0x78),
            ac.PlaySound(sound=0xC4),
            ac.IncrementCounter(counter=0x1A),
            ac.PlaySound(sound=0xC5),
            ac.IncrementCounter(counter=0x19),
            ac.WaitForCounterValue(counter=0x1B, value=0),
            ac.PlayAnimationFirstFrame(animation_id=0x03),
            ac.WaitForCounter1DValue(value=4)
        ]

    base_tech.graphics_header.layer3_packet_id = 0x04
    base_tech.effect_headers[0].power = 0x2A  # Match Flare

    return _TechData(base_tech, base_animation)


def get_reassign_techs(
        tech_man: pctech.PCTechManager,
        animation_script_man: animationscript.AnimationScriptManager,
        elem_assignment: dict[ctenums.CharID, TechElement],
        ct_rom: ctrom.CTRom  # For script lookups
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

    for char_id, orig_elem in vanilla_pc_elem_dict.items():
        if char_id not in elem_assignment:
            continue
        new_elem = elem_assignment[char_id]
        if new_elem == orig_elem:
            continue

        names_to_replace = element_name_progression[orig_elem]
        replacement_names = element_name_progression[new_elem]

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
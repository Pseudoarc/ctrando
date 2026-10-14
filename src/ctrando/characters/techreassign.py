"""Module for handling tech reassignment due to element/character rando"""
import copy
import dataclasses
import enum
import itertools
from typing import Sequence

from ctrando.arguments import characteroptions, techoptions
from ctrando.attacks import (
    pctech,
    cttechtypes as ctty,
    animationcommands as ac,
    animationscript,
    elementrando,
    pctechrandomizer,
    techrebalance
)
from ctrando.attacks.elementrando import TechElement
from ctrando.characters import charactermods
from ctrando.common import ctenums, ctrom, random


@dataclasses.dataclass()
class TechScriptPair:
    tech: pctech.PCTech
    script: animationscript.PCTechAnimationScript


class AltTechID(enum.Enum):
    # Crono
    # Marle
    ARROW_HAIL = enum.auto()
    HASTE_ALL = enum.auto()
    # Lucca
    DOUBLE_TAP = enum.auto()
    PROTECT_ALL = enum.auto()
    # Robo
    # Frog
    # Ayla
    # Magus
    GALE_SLASH = enum.auto()
    BLURP = enum.auto()
    IRON_ORB = enum.auto()
    BURST_BALL = enum.auto()
    # Extra Elementals
    HEXAGON_MIST_WATER = enum.auto()
    HEXAGON_MIST_ICE = enum.auto()
    # Duals
    CRONO_CROSS = enum.auto()
    AMPLIFIRE = enum.auto()
    ROBO_TOSS = enum.auto()


@dataclasses.dataclass()
class BaseTechData:
    vanilla_tech_pairs: dict[int, TechScriptPair]
    alt_tech_pairs: dict[AltTechID, TechScriptPair]
    attacks: dict[ctenums.CharID, pctech.PCAttack]


def collect_vanilla_tech_data(
        base_rom: ctrom.CTRom,
        tech_opts: techoptions.TechOptions,
) -> BaseTechData:
    """
    Collects tech data and tech scripts from a mostly vanilla rom.
    :param base_rom:  A vanilla Chrono Trigger Rom with Mauron pc tech patch applied
    :return: All techs and scripts for vanilla and alt techs in a BaseTechData object
    """

    base_tech_man = pctech.PCTechManager.read_from_ctrom(base_rom)
    pctech.fix_vanilla_techs(base_tech_man)
    if tech_opts.normalize_techs:
        techrebalance.rebalance_vanilla_tech_man(base_tech_man)

    tech_data_dict = base_tech_man.get_all_techs()

    vanilla_tech_dict: dict[int, TechScriptPair] = dict()
    for tech_id, tech in tech_data_dict.items():
        if tech is None:
            continue
        script_id = tech.graphics_header.script_id
        script = animationscript.PCTechAnimationScript.read_from_ctrom(
            base_rom, script_id
        )
        vanilla_tech_dict[tech_id] = TechScriptPair(tech, script)

    alt_tech_dict: dict[AltTechID, TechScriptPair] = dict()
    alt_tech_dict[AltTechID.ARROW_HAIL] = TechScriptPair(
        charactermods.get_arrow_hail_tech(base_tech_man),
        animationscript.make_arrow_rain_script(base_rom)
    )
    alt_tech_dict[AltTechID.HASTE_ALL] = TechScriptPair(
        charactermods.get_haste_all_tech(base_tech_man),
        animationscript.make_single_marle_haste_all_script(base_rom)
    )
    alt_tech_dict[AltTechID.DOUBLE_TAP] = TechScriptPair(
        charactermods.get_double_tap_tech(base_tech_man),
        animationscript.make_double_tap_script(base_rom)
    )
    alt_tech_dict[AltTechID.GALE_SLASH] = TechScriptPair(
        charactermods.get_gale_slash_tech(base_tech_man),
        animationscript.make_gale_slash_script(base_rom)
    )
    alt_tech_dict[AltTechID.BLURP] = TechScriptPair(
        charactermods.get_blurp_tech(base_tech_man),
        charactermods.get_blurp_script(base_rom)
    )
    alt_tech_dict[AltTechID.IRON_ORB] = TechScriptPair(
        charactermods.get_iron_orb_tech(base_tech_man),
        animationscript.make_iron_orb_script(base_rom)
    )
    alt_tech_dict[AltTechID.BURST_BALL] = TechScriptPair(
        charactermods.get_burst_ball_tech(base_tech_man),
        charactermods.get_burst_ball_script(base_rom)
    )
    hex_mist_water_data = elementrando.make_hex_mist_data(
        base_tech_man, base_rom, elementrando.TechElement.WATER)
    hex_mist_ice_data = elementrando.make_hex_mist_data(
        base_tech_man, base_rom, elementrando.TechElement.ICE)

    alt_tech_dict[AltTechID.HEXAGON_MIST_WATER] = TechScriptPair(
        hex_mist_water_data.tech, hex_mist_water_data.script
    )
    alt_tech_dict[AltTechID.HEXAGON_MIST_ICE] = TechScriptPair(
        hex_mist_ice_data.tech, hex_mist_ice_data.script
    )
    alt_tech_dict[AltTechID.PROTECT_ALL] = TechScriptPair(
        charactermods.get_prot_all_tech(base_tech_man),
        animationscript.make_single_lucca_prot_all_script(base_rom)
    )
    alt_tech_dict[AltTechID.CRONO_CROSS] = make_crono_cross_data(base_tech_man, base_rom)
    alt_tech_dict[AltTechID.ROBO_TOSS] = make_robo_toss_data(base_tech_man, base_rom)
    alt_tech_dict[AltTechID.AMPLIFIRE] = make_amplifire_data(base_tech_man, base_rom)

    attack_dict: dict[ctenums.CharID, pctech.PCAttack] = {
        char_id: base_tech_man.get_attack(char_id)
        for char_id in ctenums.CharID
    }

    fix_lightning_script(vanilla_tech_dict[ctenums.TechID.LIGHTNING].script)

    return BaseTechData(vanilla_tech_dict, alt_tech_dict, attack_dict)


def make_amplifire_data(
        base_tech_man: pctech.PCTechManager,
        base_rom: ctrom.CTRom
) -> TechScriptPair:
    pc_script = animationscript.make_rr_amplifire_script(base_rom)

    base_tech = base_tech_man.get_tech(ctenums.TechID.ANTIPODE_2)
    base_tech.name = "Amplifire"
    base_tech.target_data = ctty.PCTechTargetData(b'\x07\x00')
    base_tech.battle_group = ctty.PCTechBattleGroup.from_charids(
        [ctenums.CharID.ROBO, ctenums.CharID.ROBO])
    base_tech.menu_mp_reqs = ctty.PCTechMenuMPReq(
        bytes([ctenums.TechID.LASER_SPIN, ctenums.TechID.LASER_SPIN]))
    base_tech.control_header.set_effect_index(0, ctenums.TechID.LASER_SPIN)
    base_tech.control_header.set_effect_index(1, ctenums.TechID.LASER_SPIN)

    f1 = base_tech_man.get_tech(ctenums.TechID.CURE_BEAM)
    base_tech.graphics_header = f1.graphics_header
    base_tech.graphics_header.layer3_packet_id = 0x5A
    # base_tech.graphics_header.assembly_packet_1 = 0x23
    # base_tech.graphics_header.assembly_packet_2 = 0x13
    # base_tech.graphics_header.sprite_packet_1 = 0xeb
    # base_tech.graphics_header.sprite_packet_2 = 0x0
    # base_tech.graphics_header.palette = 0x11

    return TechScriptPair(base_tech, pc_script)


def make_robo_toss_data(
        base_tech_man: pctech.PCTechManager,
        base_rom: ctrom.CTRom,
) -> TechScriptPair:
    # script = animationscript.get_fixed_r_series_beast_toss_script(base_rom)
    dod_script = animationscript.EnemyTechAnimationScript.read_from_ctrom(
         base_rom, 0x43)
    sv_script = animationscript.PCTechAnimationScript.read_from_ctrom(
        base_rom, 0x41)

    script = animationscript.EnemyTechAnimationScript.read_from_ctrom(
        base_rom, 0x43
    )
    pc_script = animationscript.PCTechAnimationScript(
        script.main_script, script.miss_script
    )

    pc_script = animationscript.make_rr_doors_of_doom_script()

    # pc_script = animationscript.PCTechAnimationScript.read_from_ctrom(
    #     base_rom, 0x5F
    # )

    base_tech = base_tech_man.get_tech(ctenums.TechID.BEAST_TOSS)
    base_tech.battle_group = ctty.PCTechBattleGroup.from_charids(
        [ctenums.CharID.ROBO, ctenums.CharID.ROBO]
    )

    # base_tech.graphics_header.layer3_packet_id = 0x3F
    base_tech.graphics_header.assembly_packet_1 = 0x08
    base_tech.graphics_header.assembly_packet_2 = 0x00
    base_tech.graphics_header.sprite_packet_1 = 0xC0
    base_tech.graphics_header.sprite_packet_2 = 0xC4
    base_tech.graphics_header.palette = 0x04
    base_tech.graphics_header.layer3_packet_id = 0x62

    base_tech.target_data = ctty.TargetData(b'\x08\x00')
    base_tech.name = "Robo Toss"

    # base_tech.control_header.set_effect_index(0, ctenums.TechID.ROBO_TACKLE)
    base_tech.menu_mp_reqs = ctty.PCTechMenuMPReq(
        bytes([ctenums.TechID.ROBO_TACKLE, ctenums.TechID.ROBO_TACKLE])
    )

    return TechScriptPair(base_tech, pc_script)


def make_crono_cross_data(
        tech_man: pctech.PCTechManager,
        ct_rom: ctrom.CTRom
) -> TechScriptPair:
    base_tech = tech_man.get_tech(ctenums.TechID.X_STRIKE)
    base_tech.battle_group = ctty.PCTechBattleGroup.from_charids(
        [ctenums.CharID.CRONO, ctenums.CharID.CRONO]
    )
    base_tech.control_header.set_effect_index(1, ctenums.TechID.CYCLONE)
    base_tech.effect_headers[1] = base_tech.effect_headers[0].get_copy()
    base_tech.menu_mp_reqs = ctty.PCTechMenuMPReq(
        bytes([ctenums.TechID.CYCLONE, ctenums.TechID.CYCLONE]))
    base_tech.name = "Crono Cross"

    script = animationscript.PCTechAnimationScript.read_from_ctrom(
        ct_rom, base_tech.graphics_header.script_id
    )

    return TechScriptPair(base_tech, script)



def fix_lightning_script(
        script: animationscript.PCTechAnimationScript
):
    """Lightning's script relies on animation duration.  Add counter checks."""
    cast_scr: animationscript.ObjectScript = script.main_script.caster_objects[0]
    # cast_scr.insert()
    cast_scr.insert(9, ac.IncrementCounter1D())
    for ind, cmd in enumerate(cast_scr[9:]):
        if isinstance(cmd, ac.WaitForCounter1DValue) and cmd.value >= 3:
            cmd.value += 1

    for obj_group in (
            script.main_script.effect_objects,
            script.main_script.target_objects
    ):
        for obj_script in obj_group:
            if obj_script is None:
                continue

            for ind, cmd in enumerate(obj_script):
                if isinstance(cmd, ac.WaitForCounter1DValue) and cmd.value >= 3:
                    cmd.value += 1


def _get_single_tech_range(
        char_id: ctenums.CharID) -> tuple[int, int]:
    start = 1 + char_id*8
    return start, start + 8



def collect_single_techs(
        base_tech_data: BaseTechData,
        char_id: ctenums.CharID,
        reassign_id: ctenums.CharID,
        char_opts: characteroptions.CharacterOptions
) -> list[TechScriptPair]:
    out_data: list[TechScriptPair] = []

    start, end = _get_single_tech_range(reassign_id)
    for tech_id in range(start, end):
        data = base_tech_data.vanilla_tech_pairs[tech_id]
        # Crono Reassigns
        # Marle Reassigns
        if tech_id == ctenums.TechID.PROVOKE and char_opts.use_phys_marle:
            data = base_tech_data.alt_tech_pairs[AltTechID.ARROW_HAIL]
        elif tech_id == ctenums.TechID.HASTE and char_opts.use_haste_all:
            data = base_tech_data.alt_tech_pairs[AltTechID.HASTE_ALL]
        # Lucca Reassigns
        elif tech_id == ctenums.TechID.FLAME_TOSS and char_opts.use_phys_lucca:
            data = TechScriptPair(
                charactermods.get_phys_flame_toss(data.tech),
                data.script)
        elif tech_id == ctenums.TechID.NAPALM and char_opts.use_phys_lucca:
            data = base_tech_data.alt_tech_pairs[AltTechID.DOUBLE_TAP]
        elif tech_id == ctenums.TechID.MEGABOMB and char_opts.use_phys_lucca:
            data = TechScriptPair(
                charactermods.get_phys_megabomb(data.tech),
                data.script)
        elif tech_id == ctenums.TechID.PROTECT and char_opts.use_protect_all:
            data = base_tech_data.alt_tech_pairs[AltTechID.PROTECT_ALL]
        # Magus Reassigns
        elif tech_id == ctenums.TechID.DARK_BOMB and char_opts.use_daltonized_magus:
            data = base_tech_data.alt_tech_pairs[AltTechID.GALE_SLASH]
        elif tech_id == ctenums.TechID.DARK_MIST and char_opts.use_daltonized_magus:
            data = base_tech_data.alt_tech_pairs[AltTechID.BLURP]
        elif tech_id == ctenums.TechID.BLACK_HOLE and char_opts.use_daltonized_magus:
            data = base_tech_data.alt_tech_pairs[AltTechID.IRON_ORB]
        elif tech_id == ctenums.TechID.DARK_MATTER and char_opts.use_daltonized_magus:
            data = base_tech_data.alt_tech_pairs[AltTechID.BURST_BALL]

        tech = reassign_single_tech(data.tech, char_id)
        script = copy.deepcopy(data.script)

        out_data.append(TechScriptPair(tech, script))

    return out_data


def reassign_single_tech(
        tech: pctech.PCTech,
        new_pc_id: ctenums.CharID,
) -> pctech.PCTech:
    """
    Modify a single tech to be used by another character
    :param tech: The tech to reassign
    :param new_pc_id: The CharID of the character who will receive the tech
    :return: The tech with reassigned data
    """

    new_tech = copy.deepcopy(tech)
    new_tech.battle_group = ctty.PCTechBattleGroup.from_charids([new_pc_id])

    return new_tech



_names_to_distinguish: frozenset[str] = frozenset(["*Cure 2"])
_name_suffix_dict: dict[ctenums.CharID, str] = {
    ctenums.CharID.CRONO: "C",
    ctenums.CharID.MARLE: "M",
    ctenums.CharID.LUCCA: "L",
    ctenums.CharID.ROBO: "R",
    ctenums.CharID.FROG: "F",
    ctenums.CharID.AYLA: "A",
    ctenums.CharID.MAGUS: "J"
}
def get_modified_tech_name(
        tech: pctech.PCTech,
        char_identity: ctenums.CharID
):
    name = tech.name
    if name in _names_to_distinguish:
        name += _name_suffix_dict[char_identity]
    return name


def build_combo_tech_profiles(
       base_data: BaseTechData
) -> dict[tuple[str, ...], TechScriptPair]:

    ret_dict: dict[tuple[str, ...], TechScriptPair] = dict()
    for ind, tech_pair in base_data.vanilla_tech_pairs.items():
        if tech_pair.tech.battle_group.number_of_pcs == 1:
            continue
        if tech_pair.tech.menu_mp_reqs is None:  # Should be identical to the above
            continue

        bat_grp_pcs = tech_pair.tech.battle_group.to_char_ids()
        mmps = list(tech_pair.tech.menu_mp_reqs)
        names: list[str] = []

        for pc in bat_grp_pcs:
            for mmp in mmps:
                mmp_char = (mmp-1)//8
                if mmp_char == pc:
                    base_tech = base_data.vanilla_tech_pairs[mmp].tech
                    name = get_modified_tech_name(base_tech, pc)
                    names.append(name)
                    break
            else:
                raise ValueError

            mmps.remove(mmp)

        key = tuple(names)
        val = tech_pair
        ret_dict[key] = val

    ret_dict[("Cyclone", "Cyclone")] = base_data.alt_tech_pairs[AltTechID.CRONO_CROSS]
    ret_dict[("Robo Tackle", "Robo Tackle")] = base_data.alt_tech_pairs[AltTechID.ROBO_TOSS]
    ret_dict[("Laser Spin", "Laser Spin")] = base_data.alt_tech_pairs[AltTechID.AMPLIFIRE]

    return ret_dict


def get_reassigned_combo_tech(
        tech: pctech.PCTech,
        tech_learn_names: Sequence[str],
        single_tech_assign_dict: dict[ctenums.CharID, list[TechScriptPair]],
        char_tech_name_index_dict: dict[ctenums.CharID, dict[str, int]],
        new_battle_group: Sequence[ctenums.CharID], *,
        make_copy: bool = False
):
    if make_copy:
        tech = copy.deepcopy(tech)

    new_tech_bat_grp = ctty.PCTechBattleGroup.from_charids(new_battle_group)
    new_mmps: list[int] = []
    tech.battle_group = new_tech_bat_grp
    for ind, (pc_id, learn_name) in enumerate(zip(new_battle_group, tech_learn_names)):
        tech_index = char_tech_name_index_dict[pc_id][learn_name]
        tech_level = tech_index + 1

        tech_id = 1 + pc_id*8 + tech_index

        single_tech = single_tech_assign_dict[pc_id][tech_index].tech
        orig_index = tech.control_header.get_effect_index(ind)
        if orig_index <= 1 + 7*8:
            slurp_flag = tech.effect_headers[ind].has_slurpcut_restriction
            throw_flag = tech.effect_headers[ind].has_rockthrow_restriction
            x = tech.effect_headers[ind][10:]

            tech.control_header.set_effect_index(ind, tech_id)
            tech.effect_headers[ind] = single_tech.effect_headers[0].get_copy()
            tech.effect_headers[ind].has_slurpcut_restriction = slurp_flag
            tech.effect_headers[ind].has_rockthrow_restriction = throw_flag
            tech.effect_headers[ind][10:] = x
        tech.effect_mps[ind] = single_tech.effect_mps[0]

        if tech.rock_used is None:
            tech.set_learn_requirement(pc_id, tech_level)

        new_mmps.append(tech_id)

    if tech.num_pcs == 3:
        new_mmps = sorted(new_mmps)
    tech.menu_mp_reqs = ctty.PCTechMenuMPReq(new_mmps)

    return tech


def get_reassigned_tech_script(
        script: animationscript.PCTechAnimationScript,
        orig_identities: Sequence[ctenums.CharID],
        new_identities: Sequence[ctenums.CharID], *,
        make_copy: bool = False
):
    if make_copy:
        script = copy.deepcopy(script)

    for ind, (orig_identity, new_identity) in enumerate(
        zip(orig_identities, new_identities)
    ):
        # Move from elementrando to this module
        elementrando.replace_animations(script, orig_identity, new_identity, ind)

    return script


def make_new_combo_techs(
        base_tech_data: BaseTechData,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        single_tech_assign_dict: dict[ctenums.CharID, list[TechScriptPair]],
        char_options: characteroptions.CharacterOptions
) -> dict[frozenset[ctenums.CharID], list[TechScriptPair]]:
    """
    Make new combo techs given single tech assignment.
    :param base_tech_data: All vanilla techs and scripts
    :param reassign_dict: Assignment of char_id to new identity
    :param single_tech_assign_dict: Current assignment of character single techs
    :param char_options: CharacterOptions (mods like Magus duals)
    :return:
    """

    # First store which tech names each character has
    # Names may be given a character suffix if we want to distinguish them.
    # At present this is only for Marle/Frog Cure2.
    char_tech_name_ind_dict: dict[ctenums.CharID, dict[str, int]] = {}
    for char_id in ctenums.CharID:
        single_techs = single_tech_assign_dict[char_id]
        if len(single_techs) != 8:
            raise ValueError

        name_dict: dict[str, int] = dict()
        for ind, pair in enumerate(single_techs):
            name = get_modified_tech_name(pair.tech, reassign_dict[char_id])
            name_dict[name] = ind

        char_tech_name_ind_dict[char_id] = name_dict

    tech_group_dict: dict[frozenset[ctenums.CharID], list[TechScriptPair]] = {}
    for dual_group in itertools.combinations(ctenums.CharID, 2):
        tech_group_dict[frozenset(dual_group)] = []

    for triple_group in itertools.combinations(ctenums.CharID, 3):
        tech_group_dict[frozenset(triple_group)] = []

    for tech_id, data in base_tech_data.vanilla_tech_pairs.items():
        if tech_id < 0x39:
            continue

    no_repeat_names = {
        "Amplifire", "Robo Toss", "Double Cure", "Crono Cross"
    }
    learn_data = build_combo_tech_profiles(base_tech_data)
    for learn_list, tech_pair in learn_data.items():
        char_choices: list[list[ctenums.CharID]] = []
        for tech_name in learn_list:
            char_choices.append(
                [x for x in ctenums.CharID
                 if tech_name in char_tech_name_ind_dict[x]]
            )

        num_pcs = len(learn_list)
        for char_selection in itertools.product(*char_choices):
            group = frozenset(char_selection)
            if len(group) != num_pcs:
                continue

            reassign_list = [reassign_dict[x] for x in char_selection]
            if ctenums.CharID.MAGUS in reassign_list and (
                num_pcs == 3 or not char_options.use_magus_dual_techs
            ):
                continue

            if tech_pair.tech.name in no_repeat_names:
                group_names = {
                    pair.tech.name for pair in tech_group_dict[group]
                }
                if tech_pair.tech.name in group_names:
                    continue

            # Reassign animations, etc now because we don't want to lose the
            # order of the assignment.
            tech = get_reassigned_combo_tech(
                tech_pair.tech, learn_list, single_tech_assign_dict,
                char_tech_name_ind_dict, char_selection, make_copy=True
            )
            script = get_reassigned_tech_script(tech_pair.script, tech_pair.tech.battle_group.to_char_ids(),
                                                reassign_list, make_copy=True)

            tech_group_dict[group].append(TechScriptPair(tech, script))

    return tech_group_dict


# class TechElement(enum.Enum):
#     LIGHTNING = enum.auto()
#     FIRE = enum.auto()
#     ICE = enum.auto()
#     WATER = enum.auto()
#     SHADOW = enum.auto()


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


def chaos_reassign_elemental_single_techs(
        base_data: BaseTechData,
        char_reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        single_tech_assignment: dict[ctenums.CharID, list[TechScriptPair]],
        rng: random.RNGType
):
    base_tech_ids: list[ctenums.TechID] = [
        ctenums.TechID.LIGHTNING, ctenums.TechID.LIGHTNING_2, ctenums.TechID.LUMINAIRE,
        ctenums.TechID.FIRE, ctenums.TechID.FIRE_2, ctenums.TechID.FLARE,
        ctenums.TechID.ICE, ctenums.TechID.ICE_2,
        ctenums.TechID.WATER,ctenums.TechID.WATER_2,
        ctenums.TechID.FIRE_2, ctenums.TechID.LIGHTNING_2, ctenums.TechID.ICE_2,
        ctenums.TechID.DARK_BOMB, ctenums.TechID.DARK_MIST, ctenums.TechID.DARK_MATTER
    ]

    base_element_names = [
        base_data.vanilla_tech_pairs[tech_id].tech.name
        for tech_id in set(base_tech_ids)
    ]

    num_replacement_dict: dict[ctenums.CharID, int] = {
        char_id: 0 for char_id in ctenums.CharID
    }
    for char_id in ctenums.CharID:
        for tech_pair in single_tech_assignment[char_id]:
            if tech_pair.tech.name in base_element_names:
                num_replacement_dict[char_id] += 1

    num_replacements = sum(num_replacement_dict.values())
    num_base_copies, num_overflow = divmod(num_replacements, len(base_tech_ids))
    overflow_ids = rng.sample(base_tech_ids, k=num_overflow)
    replacements = num_replacements*base_tech_ids + overflow_ids

    unique_replacement_dict: dict[ctenums.TechID, int] = dict()
    for tech_id in replacements:
        if tech_id in unique_replacement_dict:
            unique_replacement_dict[tech_id] += 1
        else:
            unique_replacement_dict[tech_id] = 1

    techs_to_assign = list(unique_replacement_dict.keys())
    rng.shuffle(techs_to_assign)

    magus_replacements: dict[ctenums.TechID, ctenums.TechID] = {
        ctenums.TechID.FIRE_2: ctenums.TechID.FIRE_2_M,
        ctenums.TechID.ICE_2: ctenums.TechID.ICE_2_M,
        ctenums.TechID.LIGHTNING_2: ctenums.TechID.LIGHTNING_2_M,
    }
    magus_x2_power = base_data.vanilla_tech_pairs[ctenums.TechID.FIRE_2_M].tech.effect_headers[0].power

    tech_assignments: dict[ctenums.CharID, list[ctenums.TechID]] = {
        char_id: [] for char_id in ctenums.CharID
    }
    for tech_id in techs_to_assign:
        num_copies = unique_replacement_dict[tech_id]
        chars_to_assign = rng.sample(
            [char_id for char_id, count in num_replacement_dict.items()
             if count > 0],
            k=num_copies
        )
        for char_id in chars_to_assign:
            tech_assignments[char_id].append(tech_id)
            num_replacement_dict[char_id] -= 1



    for char_id, tech_assignment_list in tech_assignments.items():
        for ind, tech_pair in enumerate(single_tech_assignment[char_id]):
            if tech_pair.tech.name in base_element_names:
                new_id = tech_assignment_list.pop()
                orig_pc = ctenums.CharID(tech_pair.tech.battle_group[0])
                new_pair = base_data.vanilla_tech_pairs[new_id]
                tech = reassign_single_tech(new_pair.tech, char_id)
                script = copy.deepcopy(new_pair.script)
                script = get_reassigned_tech_script(
                    script, [orig_pc], [char_reassign_dict[char_id]]
                )

                single_tech_assignment[char_id][ind] = TechScriptPair(tech, script)


def reassign_elemental_single_techs(
        base_data: BaseTechData,
        char_reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        single_tech_assignment: dict[ctenums.CharID, list[TechScriptPair]],
        elem_reassignment: dict[ctenums.CharID, TechElement],
        tech_options: techoptions.TechOptions,
        rng: random.RNGType
):
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

    elemental_techs: dict[TechElement, tuple[TechScriptPair, TechScriptPair, TechScriptPair]] = {
        TechElement.LIGHTNING: (
            base_data.vanilla_tech_pairs[ctenums.TechID.LIGHTNING],
            base_data.vanilla_tech_pairs[ctenums.TechID.LIGHTNING_2],
            base_data.vanilla_tech_pairs[ctenums.TechID.LUMINAIRE],
        ),
        TechElement.ICE: (
            base_data.vanilla_tech_pairs[ctenums.TechID.ICE],
            base_data.vanilla_tech_pairs[ctenums.TechID.ICE_2],
            base_data.alt_tech_pairs[AltTechID.HEXAGON_MIST_ICE],
        ),
        TechElement.FIRE: (
            base_data.vanilla_tech_pairs[ctenums.TechID.FIRE],
            base_data.vanilla_tech_pairs[ctenums.TechID.FIRE_2],
            base_data.vanilla_tech_pairs[ctenums.TechID.FLARE],
        ),
        TechElement.WATER: (
            base_data.vanilla_tech_pairs[ctenums.TechID.WATER],
            base_data.vanilla_tech_pairs[ctenums.TechID.WATER_2],
            base_data.alt_tech_pairs[AltTechID.HEXAGON_MIST_WATER]
        ),
        TechElement.SHADOW: (
            base_data.vanilla_tech_pairs[ctenums.TechID.DARK_BOMB],
            base_data.vanilla_tech_pairs[ctenums.TechID.DARK_MIST],
            base_data.vanilla_tech_pairs[ctenums.TechID.DARK_MATTER],
        )
    }

    magus_replacements: dict[str, TechScriptPair] = {
        "*Fire 2": base_data.vanilla_tech_pairs[ctenums.TechID.FIRE_2_M],
        "*Lightning2": base_data.vanilla_tech_pairs[ctenums.TechID.LIGHTNING_2_M],
        "*Ice 2": base_data.vanilla_tech_pairs[ctenums.TechID.ICE_2_M]
    }
    magus_x2_power = base_data.vanilla_tech_pairs[ctenums.TechID.FIRE_2_M].tech.effect_headers[0].power

    for char_id in ctenums.CharID:
        reassign_id = char_reassign_dict[char_id]
        element = vanilla_pc_elem_dict.get(reassign_id, None)
        new_element = elem_reassignment.get(char_id, None)

        if element == new_element or None in (element, new_element):
            continue

        names_to_replace = element_name_progression[element]
        if reassign_id == ctenums.CharID.MAGUS and new_element != TechElement.WATER:
            names_to_replace = ("*Dark Bomb", "Nothing", "*DarkMatter")

        for ind, tech_pair in enumerate(single_tech_assignment[char_id]):
            name = tech_pair.tech.name
            if name in names_to_replace:
                tech_level = names_to_replace.index(name)
                replacement_pair: TechScriptPair = elemental_techs[new_element][tech_level]

                orig_char_id = ctenums.CharID(replacement_pair.tech.battle_group[0])

                new_tech = reassign_single_tech(replacement_pair.tech, char_id)
                if reassign_id == ctenums.CharID.MAGUS:
                    if "2" in new_tech.name:
                        new_tech.effect_headers[0].power = magus_x2_power

                new_script = get_reassigned_tech_script(
                    replacement_pair.script, [orig_char_id], [reassign_id],
                    make_copy=True
                )
                # new_script = copy.deepcopy(replacement_pair.script)

                single_tech_assignment[char_id][ind] = TechScriptPair(new_tech, new_script)



def sort_tech_pair_list(
        tech_pair_list: list[TechScriptPair],
        rng: random.RNGType
) -> list[TechScriptPair]:
    def key(_pair:TechScriptPair) -> tuple[bool, bool, float]:
        return _pair.tech.rock_used is not None, not _pair.tech.is_damage_tech(), rng.random()

    tech_pair_list = sorted(tech_pair_list, key=key)
    return tech_pair_list


def do_element_sigle_tech_assignment(
        base_data: BaseTechData,
        single_tech_assignment: dict[ctenums.CharID, list[TechScriptPair]],
        char_reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        char_opts: characteroptions.CharacterOptions,
        tech_opts: techoptions.TechOptions,
        rng: random.RNGType
):
    if char_opts.tech_rando_scheme != characteroptions.TechRandoScheme.VANILLA:
        if char_opts.tech_rando_scheme in (
            characteroptions.TechRandoScheme.RANDOM_ELEMENT,
            characteroptions.TechRandoScheme.SHUFFLE_ELEMENT
        ):
            element_assignment = elementrando.get_char_rando_elem_assignment(
                char_opts.tech_rando_scheme,
                char_reassign_dict, rng
            )
            reassign_elemental_single_techs(
                base_data, char_reassign_dict, single_tech_assignment,
                element_assignment, tech_opts, rng
            )
        elif char_opts.tech_rando_scheme == characteroptions.TechRandoScheme.CHAOS_ELEMENT:
            chaos_reassign_elemental_single_techs(
                base_data, char_reassign_dict, single_tech_assignment, rng
            )
        else:
            raise ValueError


def get_reassign_techs_scripts(
        base_rom: ctrom.CTRom,
        char_reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        char_opts: characteroptions.CharacterOptions,
        tech_opts: techoptions.TechOptions,
        rng: random.RNGType  # For choosing when too many techs
) -> tuple[pctech.PCTechManager, animationscript.AnimationScriptManager]:

    base_data = collect_vanilla_tech_data(
        base_rom, tech_opts
    )

    single_tech_assignment: dict[ctenums.CharID, list[TechScriptPair]] = dict()
    for char_id, reassign_id in char_reassign_dict.items():
        single_tech_assignment[char_id] = collect_single_techs(
            base_data, char_id, reassign_id, char_opts
        )

    do_element_sigle_tech_assignment(
        base_data, single_tech_assignment, char_reassign_dict, char_opts,
        tech_opts, rng
    )

    new_tech_man = pctech.PCTechManager()
    orig_attacks: dict[ctenums.CharID, pctech.PCAttack] = dict()
    for char_id in ctenums.CharID:
        orig_attacks[char_id] = new_tech_man.get_attack(char_id)

    for char_id, reassign_id in char_reassign_dict.items():
        attack = copy.deepcopy(base_data.attacks[reassign_id])
        attack.control_header.battle_group_id = char_id
        new_tech_man.set_attack(char_id, attack)

    new_script_man = animationscript.AnimationScriptManager()

    for char_id in ctenums.CharID:
        for ind, pair in enumerate(single_tech_assignment[char_id]):
            tech_id = 1 + char_id*8 + ind
            pair.tech.graphics_header.script_id = tech_id
            new_script_man.script_dict[tech_id] = pair.script

    for char_id, tech_pairs in single_tech_assignment.items():
        for pair in tech_pairs:
            new_tech_man.add_tech(pair.tech)

    pctechrandomizer.modify_single_tech_powers_only(
        new_tech_man, tech_opts, tech_opts.custom_damage_mps, rng
    )

    single_tech_dict: dict[int, pctech.PCTech] = {
        key: val for key, val in new_tech_man.get_all_techs().items()
        if val is not None  # Just for static type checking
    }

    combo_tech_pairs = make_new_combo_techs(
        base_data, char_reassign_dict, single_tech_assignment, char_opts
    )

    for group, tech_pairs in combo_tech_pairs.items():
        for pair in tech_pairs:
            pctechrandomizer.update_dual_tech_power(pair.tech, single_tech_dict)

    current_tech_id = 0x39
    for group, tech_pairs in combo_tech_pairs.items():
        if len(group) == 2:
            num_techs = 3
        elif len(group) == 3:
            num_techs = 1
        else:
            raise ValueError

        tech_pairs = sort_tech_pair_list(tech_pairs, rng)[:num_techs]
        for pair in tech_pairs:
            pair.tech.graphics_header.script_id = current_tech_id
            new_script_man.script_dict[current_tech_id] = pair.script
            current_tech_id += 1
            new_tech_man.add_tech(pair.tech)

    pctechrandomizer.randomize_tech_order(
        new_tech_man, tech_opts.tech_order, tech_opts.preserve_magic, rng
    )

    return new_tech_man, new_script_man


def main():
    base_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    from ctrando.base import basepatch
    from ctrando.attacks import pctechrandomizer
    import random

    rng = random.Random("SAFSFSAFFVWAFSDF")
    basepatch.base_patch_ct_rom(base_rom)

    base_data = collect_vanilla_tech_data(base_rom)

    reassign_dict: dict[ctenums.CharID, ctenums.CharID] = {
        ctenums.CharID.CRONO: ctenums.CharID.CRONO,
        ctenums.CharID.MARLE: ctenums.CharID.MAGUS,
        ctenums.CharID.LUCCA: ctenums.CharID.MAGUS,
        ctenums.CharID.ROBO: ctenums.CharID.LUCCA,
        ctenums.CharID.FROG: ctenums.CharID.CRONO,
        ctenums.CharID.AYLA: ctenums.CharID.MARLE,
        ctenums.CharID.MAGUS: ctenums.CharID.CRONO,
    }

    char_opts = characteroptions.CharacterOptions()
    char_opts.use_daltonized_magus = True

    reassign_techs: dict[ctenums.CharID, list[TechScriptPair]] = dict()
    for char_id, reassign_id in reassign_dict.items():
        reassign_techs[char_id] = collect_single_techs(
            base_data, char_id, reassign_id, char_opts
        )

    elem_assignment: dict[ctenums.CharID, TechElement] = {
        ctenums.CharID.CRONO: TechElement.FIRE,
        ctenums.CharID.MARLE: TechElement.FIRE,
        ctenums.CharID.LUCCA: TechElement.WATER,
        ctenums.CharID.ROBO: TechElement.SHADOW,
        ctenums.CharID.FROG: TechElement.WATER,
        ctenums.CharID.AYLA: TechElement.LIGHTNING,
        ctenums.CharID.MAGUS: TechElement.ICE,
    }

    tech_opts = techoptions.TechOptions()
    reassign_elemental_single_techs(
        base_data, reassign_dict, reassign_techs, elem_assignment,
        tech_opts, rng
    )

    new_tech_man = pctech.PCTechManager()
    for char_id, tech_pairs in reassign_techs.items():
        for pair in tech_pairs:
            new_tech_man.add_tech(pair.tech)

    pctechrandomizer.modify_single_tech_powers_only(
        new_tech_man, tech_opts, tech_opts.custom_damage_mps, rng
    )

    single_tech_dict: dict[int, pctech.PCTech] = {
        key: val for key, val in new_tech_man.get_all_techs().items()
        if val is not None  # Just for static type checking
    }

    combo_tech_pairs = make_new_combo_techs(
        base_data, reassign_dict, reassign_techs, char_opts
    )

    for group, tech_pairs in combo_tech_pairs.items():
        for pair in tech_pairs:
            pctechrandomizer.update_dual_tech_power(pair.tech, single_tech_dict)

    for group, tech_pairs in combo_tech_pairs.items():
        if len(group) == 2:
            num_techs = 3
        elif len(group) == 3:
            num_techs = 1
        else:
            raise ValueError

        tech_pairs = sort_tech_pair_list(tech_pairs, rng)[:num_techs]
        for pair in tech_pairs:
            new_tech_man.add_tech(pair.tech)

    pass

if __name__ == "__main__":
    main()






"""Implement character buff/debuffs"""
import copy
import enum

from ctrando.common import ctenums, ctrom
from ctrando.characters import ctpcstats
from ctrando.attacks import pctech, animationscript, scriptreassign


class BlessingID(enum.Enum):
    LUCCA_PHYS_TEH = enum.auto()
    MARLE_PHYS_TECH = enum.auto()
    MARLE_HASTE_ALL = enum.auto()
    LUCCA_PROT_ALL = enum.auto()


def get_arrow_hail_tech(
    vanilla_tech_man: pctech.PCTechManager
) -> pctech.PCTech:
    provoke = vanilla_tech_man.get_tech(ctenums.TechID.PROVOKE)
    cyclone = vanilla_tech_man.get_tech(ctenums.TechID.CYCLONE)

    provoke.target_data = pctech.ctt.PCTechTargetData(b'\x08\x00')  # All enemies
    provoke.control_header[1:] = cyclone.control_header[1:]  # All but battle group
    provoke.effect_headers[0] = cyclone.effect_headers[0]
    provoke.effect_headers[0].power = 8
    provoke.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED

    provoke.effect_mps[0] = 2
    provoke.name = "Arrow Hail"

    return provoke


def get_phys_flame_toss(base_flame_toss: pctech.PCTech) -> pctech.PCTech:
    tech = copy.deepcopy(base_flame_toss)
    tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
    tech.effect_headers[0].applies_on_hit_effects = True
    tech.effect_headers[0].power = 8

    return tech


def get_phys_megabomb(base_mega_bomb: pctech.PCTech) -> pctech.PCTech:
    tech = copy.deepcopy(base_mega_bomb)
    tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
    tech.effect_headers[0].applies_on_hit_effects = True
    tech.effect_headers[0].power = 21

    return tech


def get_double_tap_tech(vanilla_tech_man: pctech.PCTechManager):
    backup = vanilla_tech_man.get_tech(ctenums.TechID.CONFUSE)

    tech = vanilla_tech_man.get_tech(ctenums.TechID.NAPALM)
    tech.control_header = backup.control_header
    tech.control_header.set_effect_mod(0, ctenums.WeaponEffects.DMG_50)
    tech.effect_headers[0] = backup.effect_headers[0]
    tech.effect_headers[0][1] = 2
    tech.effect_headers[0].damage_formula_id = pctech.ctt.DamageFormula.PC_RANGED
    tech.effect_headers[0].power = 12
    tech.effect_headers[0].applies_on_hit_effects = True

    tech.graphics_header.sprite_packet_1 = 0xEB
    tech.graphics_header.sprite_packet_2 = 0xEF
    tech.graphics_header.assembly_packet_1 = 0x23
    tech.graphics_header.assembly_packet_2 = 0x89
    tech.graphics_header.palette = 0x89
    tech.graphics_header.layer3_packet_id = 9
    tech.target_data[0], tech.target_data[1] = 7, 0

    tech.name = "Double Tap"

    return tech


def get_haste_all_tech(
        vanilla_tech_man: pctech.PCTechManager,
) -> pctech.PCTech:
    haste = vanilla_tech_man.get_tech(ctenums.TechID.HASTE)
    haste.target_data = pctech.ctt.PCTechTargetData(b'\x81\x00')
    haste.name = "*Haste All"
    haste.graphics_header.layer3_packet_id = 0x15
    haste.effect_mps[0] = 15

    return haste


def get_prot_all_tech(
        vanilla_tech_man: pctech.PCTechManager,
) -> pctech.PCTech:
    protect = vanilla_tech_man.get_tech(ctenums.TechID.PROTECT)
    protect.target_data = pctech.ctt.PCTechTargetData(b'\x81\x00')
    protect.effect_mps[0] = 12

    return protect


def get_reraise_tech(
        vanilla_tech_man: pctech.PCTechManager
) -> pctech.PCTech:
    lifeline = vanilla_tech_man.get_tech(ctenums.TechID.LIFE_LINE)
    life2 = vanilla_tech_man.get_tech(ctenums.TechID.LIFE_2_M)

    life2.target_data = pctech.ctt.PCTechTargetData(b'\x80\x00')
    life2.effect_headers[0] = copy.deepcopy(lifeline.effect_headers[0])
    life2.name = "*Reraise"

    return life2


def get_gale_slash_tech(
        vanilla_tech_man: pctech.PCTechManager
) -> pctech.PCTech:
    # Just get some physical tech as a base
    base_tech = vanilla_tech_man.get_tech(ctenums.TechID.SPINCUT)
    base_tech.battle_group = pctech.ctt.PCTechBattleGroup.from_charids([ctenums.CharID.MAGUS])
    base_tech.name = "Gale Slash"
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x0B\x01')  # Line (Slash)
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("34 E8 EC 21 98 98 FF")  # Copied with +0x80 for some indices
    )
    base_tech.effect_mps[0] = 6

    return base_tech


def get_blurp_script(base_rom: ctrom.CTRom) -> animationscript.PCTechAnimationScript:
    blurp_script = animationscript.read_enemy_tech_script_from_ctrom(base_rom, 0x5D)
    blurp_script.main_script.caster_objects[0][1] = animationscript.ac.PlayAnimationOnce(animation_id=0x5)

    return blurp_script


def get_blurp_tech(vanilla_tech_man: pctech.PCTechManager) -> pctech.PCTech:
    # Get some AoE Magic tech as a base
    base_tech = vanilla_tech_man.get_tech(ctenums.TechID.LIGHTNING_2_M)
    effect = base_tech.effect_headers[0]
    effect.status_effect = ctenums.StatusEffect.POISON
    effect.status_effect_chance = 80
    effect.power = 0xC  # maybe too low
    effect.inflicts_status = True

    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("5D 00 00 00 00 00 2B")
    )
    base_tech.name = "*Bluuurp!"

    return base_tech


def get_iron_orb_tech(vanilla_tech_man: pctech.PCTechManager) -> pctech.PCTech:
    # Use black hole as a base
    base_tech = vanilla_tech_man.get_tech(ctenums.TechID.BLACK_HOLE)
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x07\x00')
    base_tech.control_header.set_effect_mod(0, ctenums.WeaponEffects.IRON_ORB)
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.effect_headers[0].power = 0
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("41 C0 00 09 95 95 FF")
    )

    base_tech.name = "Iron Orb"

    return base_tech


def get_burst_ball_script(base_rom: ctrom.CTRom) -> animationscript.PCTechAnimationScript:
    burst_ball_script = animationscript.read_enemy_tech_script_from_ctrom(base_rom, 0x88)
    burst_ball_script.main_script.caster_objects[0][4] = animationscript.ac.PlayAnimationOnce(animation_id=0x22)
    return burst_ball_script


def get_burst_ball_tech(vanilla_tech_man: pctech.PCTechManager) -> pctech.PCTech:
    base_tech = vanilla_tech_man.get_tech(ctenums.TechID.LIGHTNING_2_M)
    base_tech.control_header.element = ctenums.Element.NONELEMENTAL
    base_tech.target_data = pctech.ctt.PCTechTargetData(b'\x07\x00')
    base_tech.effect_headers[0].power = 0x2A
    base_tech.effect_mps[0] = 20
    base_tech.graphics_header = pctech.ctt.PCTechGfxHeader(
        bytes.fromhex("88 CE 0B 35 A9 A9 4A")
    )

    base_tech.name = "*Burst Ball"
    return base_tech
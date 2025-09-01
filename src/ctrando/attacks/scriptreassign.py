"""Module for modifying existing scripts to use a different character."""
import copy

from ctrando.common import ctrom, ctenums
from ctrando.attacks import pctech, animationscript, animationcommands as ac


_magus_repl_anim: dict[ctenums.CharID, dict[int, int]] = {
    ctenums.CharID.LUCCA: {
        0x43: 0x22
    },
    ctenums.CharID.MARLE: {
        0x35: 0x22,
        # 0x36: 0x26,
    }
}


_script_reassign_id_dict: dict[tuple[ctenums.TechID, ctenums.CharID], animationscript.NewScriptID] = {
    (ctenums.TechID.ANTIPODE_2, ctenums.CharID.MARLE): animationscript.NewScriptID.MAGUS_LUCCA_ANTI2,
    (ctenums.TechID.ANTIPODE_3, ctenums.CharID.MARLE): animationscript.NewScriptID.MAGUS_LUCCA_ANTI3,
    (ctenums.TechID.ANTIPODE_2, ctenums.CharID.LUCCA): animationscript.NewScriptID.MAGUS_MARLE_ANTI2,
    (ctenums.TechID.ICE_SWORD_2, ctenums.CharID.MARLE): animationscript.NewScriptID.MAGUS_CRONO_ICESWORD2
}


def get_magus_reassigns(tech: pctech.PCTech) -> list[ctenums.CharID]:
    reassigns: list[ctenums.CharID] = []

    if ctenums.TechID.LIGHTNING_2 in tech.menu_mp_reqs:
        reassigns.append(ctenums.CharID.CRONO)
    if ctenums.TechID.ICE_2 in tech.menu_mp_reqs:
        reassigns.append(ctenums.CharID.MARLE)
    if ctenums.TechID.FIRE_2 in tech.menu_mp_reqs:
        reassigns.append(ctenums.CharID.LUCCA)

    return reassigns


_magus_duals = [
    ctenums.TechID.ICE_SWORD_2, ctenums.TechID.FIRE_SWORD_2,
    ctenums.TechID.SUPER_VOLT, ctenums.TechID.SPIRE,
    ctenums.TechID.ANTIPODE_2, ctenums.TechID.ANTIPODE_3,
    ctenums.TechID.FIRE_TACKLE, ctenums.TechID.BLAZE_TWISTER,
    ctenums.TechID.BLAZE_KICK, ctenums.TechID.GLACIER,
    ctenums.TechID.CUBE_TOSS,
]


def add_all_magus_reassign_techs(
        tech_man: pctech.PCTechManager,
        allowed_partners: set[ctenums.CharID] = None,
):
    if allowed_partners is None:
        allowed_partners = set(ctenums.CharID)

    for tech_id in _magus_duals:
        tech =  tech_man.get_tech(tech_id)
        possible_reassigns = get_magus_reassigns(tech)

        for reassign in allowed_partners.intersection(possible_reassigns):
            new_tech = copy.deepcopy(tech)
            new_tech = reassign_tech_to_magus(new_tech, reassign)
            if (tech_id, reassign) in _script_reassign_id_dict:
                new_script_id = _script_reassign_id_dict[(tech_id, reassign)]
                new_tech.graphics_header.script_id = new_script_id
            tech_man.add_tech(new_tech)


def reassign_tech_to_magus(
        tech: pctech.PCTech, from_pcid: ctenums.CharID,
):
    if from_pcid == ctenums.CharID.CRONO:
        from_effect_id = ctenums.TechID.LIGHTNING_2
        to_effect_id = ctenums.TechID.LIGHTNING_2_M
    elif from_pcid == ctenums.CharID.MARLE:
        from_effect_id = ctenums.TechID.ICE_2
        to_effect_id = ctenums.TechID.ICE_2_M
    elif from_pcid == ctenums.CharID.LUCCA:
        from_effect_id = ctenums.TechID.FIRE_2
        to_effect_id = ctenums.TechID.FIRE_2_M
    else:
        raise ValueError

    pcs = tech.battle_group.to_char_ids()
    other_pc = next((x for x in pcs if x != from_pcid))
    other_learn_req = tech.get_learn_requirement(other_pc)

    to_learn_req = ((to_effect_id - 1) % ctenums.CharID.MAGUS) + 1

    from_index = tech.battle_group.index(from_pcid)
    tech.battle_group[from_index] = ctenums.CharID.MAGUS

    from_mmp_index = tech.menu_mp_reqs.index(from_effect_id)
    tech.menu_mp_reqs[from_mmp_index] = to_effect_id

    tech.set_learn_requirement(ctenums.CharID.MAGUS, to_learn_req)
    tech.set_learn_requirement(other_pc, other_learn_req)

    return tech


def write_magus_animation_scripts(
        tech_man: pctech.PCTechManager,
        ct_rom: ctrom.CTRom
):

    for (tech_id, repl_char), new_script_id in _script_reassign_id_dict.items():
        tech = tech_man.get_tech(tech_id)
        orig_script_id = tech.graphics_header.script_id
        script = animationscript.AnimationScript.read_from_ctrom(ct_rom, orig_script_id)
        caster_obj_id = tech.battle_group.index(repl_char)
        caster_obj = script.main_script.caster_objects[caster_obj_id]

        repl_dict = _magus_repl_anim[repl_char]
        for cmd in caster_obj:
            if isinstance(cmd, ac._PlayAnimationBase):
                cmd.animation_id = repl_dict.get(cmd.animation_id, cmd.animation_id)
        script.write_to_ctrom(ct_rom, new_script_id)


def main():
    from ctrando.base import basepatch

    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    basepatch.base_patch_ct_rom(ct_rom)

    tech_man = pctech.PCTechManager.read_from_ctrom(ct_rom)
    add_all_magus_reassign_techs(tech_man)

    for (tech_id, repl_char), new_script_id in _script_reassign_id_dict.items():
        tech = tech_man.get_tech(tech_id)
        orig_script_id = tech.graphics_header.script_id
        script = animationscript.AnimationScript.read_from_ctrom(ct_rom, orig_script_id)
        caster_obj_id = tech.battle_group.index(repl_char)
        caster_obj = script.main_script.caster_objects[caster_obj_id]

        repl_dict = _magus_repl_anim[repl_char]
        for cmd in caster_obj:
            if isinstance(cmd, ac._PlayAnimationBase):
                cmd.animation_id = repl_dict.get(cmd.animation_id, cmd.animation_id)
        script.write_to_ctrom(ct_rom, new_script_id)

    # script = animationscript.AnimationScript.read_from_ctrom(ct_rom, ctenums.TechID.ANTIPODE_2)
    # lucca_obj = script.main_script.caster_objects[1]

    # repl_dict = _magus_repl_anim[ctenums.CharID.LUCCA]
    # for cmd in lucca_obj:
    #     if isinstance(cmd, ac._PlayAnimationBase):
    #         cmd.animation_id = repl_dict.get(cmd.animation_id, cmd.animation_id)

    # script.write_to_ctrom(ct_rom, 0x84)
    # tech = tech_man.get_tech(ctenums.TechID.ANTIPODE_2)
    # tech.graphics_header.script_id = 0x84
    # reassign_tech_to_magus(tech, ctenums.CharID.LUCCA)
    # tech_man.add_tech(tech)

    tech_man.write_to_ctrom(ct_rom, 5, 5)

    ct_rom.getbuffer()[0x0CE60B:0x0CE60B + 3] = bytearray.fromhex('EA EA 80')


    with open("/home/ross/Documents/ct-mod.sfc", "wb") as outfile:
        outfile.write(ct_rom.getvalue())


if __name__ == "__main__":
    main()

"""
Static scaling for bosses.
"""
import copy

from ctrando.bosses import bosstypes
from ctrando.common import ctenums
from ctrando.enemyai import enemyaitypes as aity, enemyaimanager as aim
from ctrando.enemydata import enemystats


def modify_hp_checks(ai_script: aity.EnemyAIScript, scale_factor: float):
    """
    Scale all hp check conditions in the enemy ai script.
    """

    for block in ai_script.action_script + ai_script.reaction_script:
        for condition in block.condition_list:
            if isinstance(condition, aity.IfHPLessThanEqual):
                temp_hp = condition.hp
                temp_hp = round(temp_hp*scale_factor)
                temp_hp = sorted([1, temp_hp, 0x7FFE])[1]

                # CT sees an 0xFF as the end of an AI script.
                if temp_hp & 0xFF == 0xFF:
                    temp_hp -= 1

                condition.hp = temp_hp


def scale_boss_hp(
        enemy_data: dict[ctenums.EnemyID, enemystats.EnemyStats],
        ai_manager: aim.EnemyAIManager,
        scale_factor: float,
        include_lavos: bool = False,
        include_midbosses: bool = True
):
    """
    Scale boss hp by some scale factor.
    Can choose to include midbosses (Krawlie, Atropos, Super Slash, Flea Plus)
    """

    midboss_ids = [
        bosstypes.BossID.ATROPOS_XR, bosstypes.BossID.SUPER_SLASH,
        bosstypes.BossID.FLEA_PLUS, bosstypes.BossID.KRAWLIE,
    ]

    lavos_ids = [
        bosstypes.BossID.LAVOS_SHELL, bosstypes.BossID.INNER_LAVOS,
        bosstypes.BossID.LAVOS_CORE
    ]
    boss_ids = list(bosstypes.BossID)
    for boss_id in bosstypes.BossID:
        if boss_id in midboss_ids and not include_midbosses:
            continue

        if boss_id in lavos_ids and not include_lavos:
            continue

        if boss_id == bosstypes.BossID.SON_OF_SUN:
            sos_eye_id = ctenums.EnemyID.SON_OF_SUN_EYE
            hp = enemy_data[sos_eye_id].hp
            if hp < 10000:
                raise ValueError
            hp = round(((hp - 10000) * scale_factor) + 10000)
            hp = sorted([1, hp, 0x7FFF])[1]
            enemy_data[sos_eye_id].hp = hp
            continue

        scheme = bosstypes.get_default_scheme(boss_id)
        part_ids: set[ctenums.EnemyID] = {part.enemy_id for part in scheme.parts}
        for part_id in part_ids:
            hp = round(enemy_data[part_id].hp*scale_factor)
            hp = sorted([1, hp, 0x7FFF])[1]
            enemy_data[part_id].hp = hp

            ai_script = ai_manager.script_dict[part_id]
            modify_hp_checks(ai_script, scale_factor)


def _get_block_with_cond(
        ai_script: list[aity.EnemyAIScriptBlock],
        condition: aity._EnemyAICondition
) -> tuple[int, aity.EnemyAIScriptBlock]:
    """Search the ai script for a block with a given condition.  Return a copy and its index."""

    for ind, block in enumerate(ai_script):
        if condition in block.condition_list:
            return ind, copy.deepcopy(block)

    raise ValueError("Condition not in AI Script.")


def set_element_safety_level(ai_man: aim.EnemyAIManager, safe_level: int):
    """
    Modify AI scripts of bosses so that any magic will trigger their weakness.
    - Nizbel I/II: Any magic will lower defense/shock
    - Retinite: Any magic will "harden sand"
    Question:  Should it be any magic as currently implemented or
      - Add a similar magic type (i.e. lit -> lit or fire)
      - Have all but the opposing type trigger (i.e. lit -> not shadow)
    """

    # There's a weird bug that I'm encountering:
    # - If I order the conditions as stat check, element check then the check will
    #   fail/softlock the game.
    # - If I order the conditions as element check, stat check then things work.
    # - This seems to be a CT bug.  Maybe not all conditions work correctly in compound checks.
    # - Or maybe there's some subtle freespace bug going on... Keep a watch.

    for enemy_id in (ctenums.EnemyID.NIZBEL, ctenums.EnemyID.NIZBEL_II):
        nizbel_script = ai_man.script_dict[enemy_id]
        lit_cond = aity.IfAttackElement(element=aity.AIElement.LIGHTNING,
                                        is_not_equal=False)

        ind, block = _get_block_with_cond(nizbel_script.reaction_script, lit_cond)
        block_ind = block.condition_list.index(lit_cond)
        block.condition_list[block_ind: block_ind+1] = [
            aity.IfAttackElement(element=aity.AIElement.MAGICAL,
                                 is_not_equal=False),
            aity.IfStatLessThanEqual(target=aity.Target.CURRENT_ENEMY,
                                     stat_offset=aity.StatOffset.LEVEL,
                                     value=safe_level),

        ]
        nizbel_script.reaction_script.insert(ind, block)

    for enemy_id in (ctenums.EnemyID.RETINITE_TOP, ctenums.EnemyID.RETINITE_BOTTOM):
        retinite_script = ai_man.script_dict[enemy_id]
        water_cond = aity.IfAttackElement(element=aity.AIElement.WATER,
                                          is_not_equal=False)
        ind, block = _get_block_with_cond(retinite_script.reaction_script, water_cond)
        block_ind = block.condition_list.index(water_cond)
        block.condition_list[block_ind: block_ind+1] = [
            aity.IfAttackElement(element=aity.AIElement.MAGICAL,
                                 is_not_equal=False),
            aity.IfStatLessThanEqual(target=aity.Target.CURRENT_ENEMY,
                                     stat_offset=aity.StatOffset.LEVEL,
                                     value=safe_level),
        ]
        retinite_script.reaction_script.insert(ind, block)

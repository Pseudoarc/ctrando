from ctrando.common.ctenums import EnemyID, ItemID
from ctrando.enemyai.enemyaimanager import EnemyAIManager
import ctrando.enemyai.enemyaitypes as aitypes


def fix_son_of_sun_ai(
        ai_manager: EnemyAIManager
):
    """
    Change the SoS script so that:
    1) SoS will not counter with Flare if all flames are dead.
    2) SoS will lose his fire if all flames are dead.
    """
    script = ai_manager.script_dict[EnemyID.SON_OF_SUN_EYE]
    condition = aitypes.IfNumLivingEnemiesLessThanEqual()
    condition.num_enemies = 1

    end_battle = aitypes.Tech(tech_index=0x7F, target=aitypes.Target.CURRENT_ENEMY)
    wander = aitypes.Wander()
    wander[2] = 6  # Whatever the vanilla script has

    new_reaction = aitypes.EnemyAIScriptBlock(
        condition_list=[aitypes.IfNumLivingEnemiesLessThanEqual(num_enemies=1)],
        action_list=[wander]
    )

    new_action = aitypes.EnemyAIScriptBlock(
        condition_list=[aitypes.IfNumLivingEnemiesLessThanEqual(num_enemies=1)],
        action_list=[aitypes.DisplayMessage(message_id=0x8D), end_battle]
    )

    script.action_script = [new_action] + script.action_script
    script.reaction_script = [new_reaction] + script.reaction_script


def fix_magus_masa2_ai(
        ai_manager: EnemyAIManager
):
    """Allow Masa2ne to reduce Magus's magic resistance."""
    script = ai_manager.script_dict[EnemyID.MAGUS]

    target_condition = aitypes.IfStatEqual(
        value=ItemID.MASAMUNE_1,
        target=aitypes.Target.ATTACKING_PC,
        stat_offset=0x29
    )

    for ind, block in enumerate(script.reaction_script):
        condition = block.condition_list[0]
        if condition == target_condition:
            new_condition = target_condition.get_copy()
            new_condition.value = ItemID.MASAMUNE_2

            new_block = aitypes.EnemyAIScriptBlock(
                condition_list=[new_condition],
                action_list=block.action_list.copy()
            )

            script.reaction_script.insert(ind, new_block)
            break
    else:
        raise IndexError

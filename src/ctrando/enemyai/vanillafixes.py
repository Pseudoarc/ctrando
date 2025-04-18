from ctrando.common.ctenums import EnemyID
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

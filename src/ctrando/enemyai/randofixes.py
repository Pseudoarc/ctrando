"""AI changes that arise from randomization."""

from ctrando.common.ctenums import EnemyID, ItemID
from ctrando.enemyai.enemyaimanager import EnemyAIManager
import ctrando.enemyai.enemyaitypes as aitypes

def fix_dino_slash_scripts(
        ai_manager: EnemyAIManager,
        new_slash_id: int
):
    slash_weak_ids = [
        EnemyID.REPTITE_GREEN, EnemyID.TERRASAUR, EnemyID.REPTITE_PURPLE,
        EnemyID.MEGASAUR, EnemyID.RUNNER, EnemyID.MASA_MUNE, EnemyID.NIZBEL,
        EnemyID.NIZBEL_II, EnemyID.GIGASAUR, EnemyID.LEAPER,
    ]

    target_condition = aitypes.IfHitByTechID(
        is_enemy_tech=False,
        tech_id=2,  # Slash Vanilla ID
        is_not_equal=False
    )
    repl_condition = target_condition.get_copy()
    repl_condition.tech_id = new_slash_id

    for enemy_id in slash_weak_ids:
        script = ai_manager.script_dict[enemy_id]

        for block in script.reaction_script:
            if block.condition_list[0] == target_condition:
                block.condition_list[0] = repl_condition
                break

        else:
            raise IndexError

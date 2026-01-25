"""AI changes that arise from randomization."""
from importlib.resources import files

from ctrando.common.ctenums import EnemyID, ItemID
from ctrando.enemyai.enemyaimanager import EnemyAIManager
import ctrando.enemyai.enemyaitypes as aitypes
from ctrando.enemyai import battlemessages


def fix_movement_locks(
        ai_manager: EnemyAIManager
):
    """
    Some enemies get stuck in some domains because of a movement of "1"
    attacked to an attack command.  Blindly replacing it.
    """
    for enemy_id in (EnemyID.MASA_MUNE, EnemyID.SLASH_SWORD, EnemyID.GATO,
                     EnemyID.KRAWLIE):
        script = ai_manager.script_dict[enemy_id]

        for block in script.action_script:
            actions = block.action_list

            for action in actions:
                if action.ACTION_ID == 1 and action[-1] == 1:
                    action[-1] = 0xA


def fix_dino_slash_scripts(
        ai_manager: EnemyAIManager,
        new_slash_id: int
):
    slash_weak_ids = [
        EnemyID.REPTITE_GREEN, EnemyID.TERRASAUR, EnemyID.REPTITE_PURPLE,
        EnemyID.MEGASAUR, EnemyID.RUNNER, EnemyID.MASA_MUNE, EnemyID.NIZBEL,
        EnemyID.NIZBEL_II, EnemyID.GIGASAUR, EnemyID.LEAPER,
        EnemyID.LAVOS_NIZBEL
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


def add_dream_devourer_ai(ai_manager: EnemyAIManager):
    script_b = files("ctrando.enemyai").joinpath("customscripts", "ddscript.bin").read_bytes()
    script = aitypes.EnemyAIScript.from_bytestring(script_b, 0)
    # print(script)
    ai_manager.script_dict[EnemyID.DREAM_DEVOURER] = script

    ai_manager.battle_msg_man.message_dict[0xE3] = battlemessages.BattleMessage.from_string(
        "Lowers defense and stores power"
    )

    barrier_count = 0

    num_action = len(script.action_script)
    for ind, block in enumerate(script.action_script + script.reaction_script):
        for action in block.action_list:
            if hasattr(action, "tech_id"):
                tech_id = getattr(action, "tech_id")
                if not hasattr(action, "message_id"):
                    raise TypeError

                if tech_id == 0x9A:
                    msg_id = 0xAA  # Destruction Rains
                elif tech_id == 0x69:
                    if barrier_count > 0:
                        msg_id = 0xB5
                    else:
                        msg_id = 0

                    barrier_count += 1
                elif tech_id == 0x8F:
                    msg_id = 0xA6
                elif tech_id == 0x89:
                    msg_id = 0x8E
                elif tech_id == 0x57:
                    if ind < num_action:
                        msg_id = 0x28
                    else:
                        msg_id = 0xA9
                elif tech_id == 0x58:
                    msg_id = 0x92
                elif tech_id == 0x62:
                    msg_id = 0xB7
                else:
                    msg_id = 0

                setattr(action, "message_id", msg_id)
            elif hasattr(action, "message_id"):
                msg_id = getattr(action, "message_id")
                if msg_id == 0x44:
                    msg_id = 0xE3
                else:
                    msg_id = 0

                setattr(action, "message_id", msg_id)

    # for ind, ct_str in ai_manager.battle_msg_man.message_dict.items():
    #     print(f"{ind:02X}: {ct_str}")
    # input()
    #
    script = ai_manager.script_dict[EnemyID.SCHALA]
    script.action_script[0].action_list[0] = aitypes.Wander(b'\x00\x01\x00\x00')
    # print(script)
    #
    # input()
"""
Module for the class that will manage AI Scripts + BattleMessages
"""
import copy
import typing

from ctrando.common import ctrom, ctenums
from ctrando.enemyai import enemyaitypes as aity, battlemessages as bm


class EnemyAIManager:
    """
    Class which stores enemy ai scripts and battle messages
    """
    def __init__(
            self,
            ai_script_dict: typing.Optional[dict[ctenums.EnemyID, aity.EnemyAIScript]] = None,
            battle_message_dict: typing.Optional[dict[int, bm.BattleMessage]] = None
    ):
        if battle_message_dict is None:
            battle_message_dict = dict()
        self.battle_msg_man = bm.BattleMessageManager(battle_message_dict)

        if ai_script_dict is None:
            ai_script_dict = dict()
        self.script_dict = copy.deepcopy(ai_script_dict)

    @classmethod
    def read_from_ct_rom(
            cls, ct_rom: ctrom.CTRom,
    ) -> 'EnemyAIManager':
        """Read an EnemyAIManager from a ct rom"""
        ret_man = EnemyAIManager()

        script_dict: dict[ctenums.EnemyID, aity.EnemyAIScript] = {}
        script_ptr_addr = aity.EnemyAIScript.get_script_ptr_start(ct_rom)
        used_message_ids: list[int] = []
        for ind in range(0x100):
            enemy_id = ctenums.EnemyID(ind)  # Testing to make sure it's in the enum
            script = aity.EnemyAIScript.read_from_ct_rom(ct_rom, enemy_id, script_ptr_addr)
            script_dict[enemy_id] = script
            used_message_ids += script.get_message_ids_used()

        ret_man.script_dict = script_dict

        num_messages = max(used_message_ids)+1
        ret_man.battle_msg_man = bm.BattleMessageManager.read_from_ct_rom(ct_rom, num_messages)

        return ret_man

    def write_to_ct_rom(self, ct_rom):
        """Write all scripts and battle messages to CT Rom"""
        self.battle_msg_man.free_existing_battle_messages(ct_rom)
        self.battle_msg_man.write_to_ct_rom(ct_rom)

        ai_ptr_start = aity.EnemyAIScript.get_script_ptr_start(ct_rom)
        for enemy_id, script in self.script_dict.items():
            aity.EnemyAIScript.free_script_on_ct_rom(ct_rom, enemy_id, ai_ptr_start)
            script.write_script_to_ct_rom(ct_rom, enemy_id, ai_ptr_start)

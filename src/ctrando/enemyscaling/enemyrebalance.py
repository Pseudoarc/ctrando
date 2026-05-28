"""Module to modify enemy stats to normalize difficulty."""
import typing

from ctrando.attacks import enemytech
from ctrando.common import ctenums, ctrom
from ctrando.enemydata import enemystats
from ctrando.enemyai import enemyaimanager, enemyaitypes as aity

def build_tech_usage(ai_manager: enemyaimanager.EnemyAIManager):
    usage_dict: dict[int, set[ctenums.EnemyID]] = {
        x: set() for x in range(0x100)
    }

    for enemy_id in ctenums.EnemyID:
        script = ai_manager.script_dict[enemy_id]
        for block in script.action_script + script.reaction_script:
            for action in block.action_list:
                tech_id: int | None = getattr(action, "tech_id", None)
                if tech_id is not None:
                    usage_dict[tech_id].add(enemy_id)


    return usage_dict


def _adjust_stat(
        enemy_stats: enemystats.EnemyStats,
        stat_name: typing.Literal["hp", "offense", "magic", "level"],
        factor: float
):
    stat = getattr(enemy_stats, stat_name)
    stat = round(stat*factor)
    setattr(enemy_stats, stat_name, stat)


def _update_usage(
        ai_script: aity.EnemyAIScript,
        replacement_dict: dict[int, int]
):
    for block in ai_script.action_script + ai_script.reaction_script:
        for action in block.action_list:
            tech_id: int = getattr(action, "tech_id", -1)
            if tech_id in replacement_dict:
                setattr(action, "tech_id", replacement_dict[tech_id])


def normalize_bosses(
        stat_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        ai_manager: enemyaimanager.EnemyAIManager,
        attack_manager: enemytech.EnemyAttackManager
):
    """Modify boss stats and behaviors for a more uniform difficulty"""

    tech_usage_dict = build_tech_usage(ai_manager)
    free_tech_ids = [tech_id for tech_id, usage in tech_usage_dict.items()
                     if not usage and tech_id < 0xFE]

    # Yakra
    # Boost Attack a bit, stronger counterattack, lower hp a bit
    stats = stat_dict[ctenums.EnemyID.YAKRA]
    _adjust_stat(stats, "offense", 1.25)
    _adjust_stat(stats, "hp", 0.75)

    counter_tech = attack_manager.get_tech(0x4E)
    counter_tech.effect.power = 0x10
    new_tech_id = free_tech_ids.pop()
    attack_manager.set_tech(counter_tech, new_tech_id)

    script = ai_manager.script_dict[ctenums.EnemyID.YAKRA]
    _update_usage(script, {0x4E: new_tech_id})

    # Guardian
    guardian_ids = (ctenums.EnemyID.GUARDIAN, ctenums.EnemyID.LAVOS_GUARDIAN)
    bit_ids = (ctenums.EnemyID.GUARDIAN_BIT,
               ctenums.EnemyID.LAVOS_GUARDIAN_LEFT,
               ctenums.EnemyID.LAVOS_GUARDIAN_RIGHT)

    for guardian_id in guardian_ids:
        stats = stat_dict[guardian_id]
        _adjust_stat(stats, "hp", 0.75)
        script = ai_manager.script_dict[guardian_id]

        block = script.action_script[0]
        block.action_list = block.action_list[2:]  # Count from 3

    for bit_id in bit_ids:
        stats = stat_dict[bit_id]
        _adjust_stat(stats, "hp", 1.2)

        script = ai_manager.script_dict[bit_id]
        block = script.action_script[-1]
        block.action_list = block.action_list[:-1]  # Remove a wander

    # R-Series More HP.  Slightly less offense.
    stats = stat_dict[ctenums.EnemyID.R_SERIES]
    _adjust_stat(stats, "hp", 2.25)
    _adjust_stat(stats, "offense", 0.9)
    script = ai_manager.script_dict[ctenums.EnemyID.R_SERIES]
    script.action_script[2].condition_list = [aity.IfTrue()]
    script.action_script[2].action_list = [
        aity.RandomAction(b'\x04'),
        aity.Attack(b'\x01\x00\x05\x05'),
        aity.Attack(b'\x01\x01\x05\x04'),
        aity.Wander(b'\x00\x00\x06\x05'),
        aity.Wander(b'\x00\x00\x06\x05'),
    ]
    script.action_script = script.action_script[:3]

    # Heckran Less HP.
    stats = stat_dict[ctenums.EnemyID.HECKRAN]
    _adjust_stat(stats, "hp", 0.85)

    # Masa Mune No run to hit
    # stats = stat_dict[ctenums.EnemyID.MASA_MUNE]
    # _adjust_stat(stats, "hp", 0.15)
    script = ai_manager.script_dict[ctenums.EnemyID.MASA_MUNE]
    for block in script.action_script:
        for action in block.action_list:
            if action.ACTION_ID == aity.Attack.ACTION_ID:
                action[-1] = 0  # Unsure, but this prevents wandering

    # Flea more power
    stats = stat_dict[ctenums.EnemyID.FLEA]
    _adjust_stat(stats, "offense", 1.5)
    _adjust_stat(stats, "magic", 1.5)

    # Slash more power
    stats = stat_dict[ctenums.EnemyID.SLASH]
    _adjust_stat(stats, "offense", 1.5)
    _adjust_stat(stats, "magic", 1.5)

    # Golem more burp
    burp_tech = attack_manager.get_tech(0x5D)
    burp_tech.effect.power = 0x06
    new_tech_id = free_tech_ids.pop()
    attack_manager.set_tech(burp_tech, new_tech_id)

    script = ai_manager.script_dict[ctenums.EnemyID.GOLEM]
    _update_usage(script, {0x5D: new_tech_id})

    # Yakra 13, stronger needles, earlier phase 2, less hp
    stats = stat_dict[ctenums.EnemyID.YAKRA_XIII]
    _adjust_stat(stats, "hp", 0.75)

    yakra_13_replacments = {
        0x0E: free_tech_ids.pop(),
        0xA8: free_tech_ids.pop()
    }

    for tech_id, replacement_id in yakra_13_replacments.items():
        base_tech = attack_manager.get_tech(tech_id)
        base_tech.effect.power = round(base_tech.effect.power*1.15)
        attack_manager.set_tech(base_tech, replacement_id)

    script = ai_manager.script_dict[ctenums.EnemyID.YAKRA_XIII]
    _update_usage(script, yakra_13_replacments)

    hp_thresh = round(stats.hp*2/3)
    block = script.action_script[1]
    block.condition_list[0] = aity.IfHPLessThanEqual(
        target=aity.Target.CURRENT_ENEMY,
        hp=hp_thresh
    )

    # Terra Mutant more power
    terra_ids = (ctenums.EnemyID.TERRA_MUTANT_BOTTOM, ctenums.EnemyID.TERRA_MUTANT_HEAD)
    for enemy_id in terra_ids:
        stats = stat_dict[enemy_id]
        _adjust_stat(stats, "offense", 2.0)
        _adjust_stat(stats, "magic", 1.5)

    # Atropos less hp, more damage
    stats = stat_dict[ctenums.EnemyID.ATROPOS_XR]
    _adjust_stat(stats, "hp", 0.75)
    _adjust_stat(stats, "offense", 1.5)
    _adjust_stat(stats, "magic", 1.5)

    # Gato don't run to hit, more damage
    stats = stat_dict[ctenums.EnemyID.GATO]
    _adjust_stat(stats, "offense", 1.25)
    script2 = ai_manager.script_dict[ctenums.EnemyID.GATO]
    action = script2.action_script[0].action_list[0]
    action[-1] = 0

    # Flea Plus / Super Slash Damage
    for enemy_id in (ctenums.EnemyID.SUPER_SLASH, ctenums.EnemyID.FLEA_PLUS):
        stats = stat_dict[enemy_id]
        _adjust_stat(stats, "offense", 1.5)
        _adjust_stat(stats, "magic", 1.5)


def main():
    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    ai_man = enemyaimanager.EnemyAIManager.read_from_ct_rom(ct_rom)

    usage = build_tech_usage(ai_man)
    print(
        [f"{x:02X}" for x, y in usage.items() if not y]
    )


if __name__ == "__main__":
    main()

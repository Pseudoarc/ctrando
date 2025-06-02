"""Module for randomizing enemy drop/charm rewards"""
from ctrando.arguments import battlerewards
from ctrando.common import ctenums
from ctrando.common.random import RNGType
from ctrando.enemydata import enemystats


def get_enemy_pool(
        enemy_stat_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        options: battlerewards.DropOptions | battlerewards.CharmOptions,
        rng: RNGType
) -> list[ctenums.EnemyID]:
    """Determine the enemies which will have a dropped item."""

    if isinstance(options, battlerewards.DropOptions):
        keep_rate = options.drop_rate
        pool_type = options.drop_enemy_pool
        attr_name = "drop_item"
    elif isinstance(options, battlerewards.CharmOptions):
        keep_rate = options.charm_rate
        pool_type = options.charm_enemy_pool
        attr_name = "charm_item"
    else:
        raise TypeError

    enemy_pool: list[ctenums.EnemyID] = []
    # The only important one (I think) is to not put anything on 0xFF
    restricted_enemies = [
        ctenums.EnemyID.UNUSED_FC, ctenums.EnemyID.UNUSED_FD,
        ctenums.EnemyID.UNUSED_FE, ctenums.EnemyID.UNUSED_FF
    ]

    if pool_type == battlerewards.EnemyPoolType.VANILLA:
        enemy_pool = [
            enemy_id for enemy_id, stats in enemy_stat_dict.items()
            if getattr(stats, attr_name) != ctenums.ItemID.NONE
        ]
    elif pool_type == battlerewards.EnemyPoolType.ALL:
        enemy_pool = [enemy_id for enemy_id in ctenums.EnemyID
                      if enemy_id not in restricted_enemies]
    else:
        print(pool_type)
        raise ValueError

    enemy_pool = [enemy_id for enemy_id in enemy_pool if rng.random() < keep_rate]

    return enemy_pool


def assign_rewards(
        enemy_pool: list[ctenums.EnemyID],
        options: battlerewards.DropOptions | battlerewards.CharmOptions,
        enemy_stat_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        rng: RNGType
):

    if isinstance(options, battlerewards.DropOptions):
        keep_rate = options.drop_rate
        pool_type = options.drop_reward_pool
        attr_name = "drop_item"
    elif isinstance(options, battlerewards.CharmOptions):
        keep_rate = options.charm_rate
        pool_type = options.charm_reward_pool
        attr_name = "charm_item"
    else:
        raise TypeError

    if pool_type == battlerewards.RewardPoolType.VANILLA:
        return

    restricted_items = [
        ctenums.ItemID.NONE, ctenums.ItemID.SCALING_LEVEL, ctenums.ItemID.OBJECTIVE_1,
        ctenums.ItemID.OBJECTIVE_2, ctenums.ItemID.OBJECTIVE_3, ctenums.ItemID.OBJECTIVE_4,
        ctenums.ItemID.OBJECTIVE_5, ctenums.ItemID.OBJECTIVE_6, ctenums.ItemID.OBJECTIVE_7,
        ctenums.ItemID.OBJECTIVE_7, ctenums.ItemID.OBJECTIVE_8, ctenums.ItemID.MASAMUNE_1,
        ctenums.ItemID.MASAMUNE_2, ctenums.ItemID.FIST, ctenums.ItemID.FIST_2,
        ctenums.ItemID.FIST_3, ctenums.ItemID.IRON_FIST, ctenums.ItemID.BRONZEFIST,
        ctenums.ItemID.UNUSED_49, ctenums.ItemID.UNUSED_4A,
        ctenums.ItemID.BENT_HILT, ctenums.ItemID.BENT_SWORD,
        ctenums.ItemID.MASAMUNE_0_ATK,
        ctenums.ItemID.UNUSED_56, ctenums.ItemID.UNUSED_57, ctenums.ItemID.UNUSED_58,
        ctenums.ItemID.UNUSED_59, ctenums.ItemID.WEAPON_END_5A, ctenums.ItemID.ARMOR_END_7B,
        ctenums.ItemID.HELM_END_94, # Rocks?
        ctenums.ItemID.RELIC_UNUSED, ctenums.ItemID.SERAPHSONG, ctenums.ItemID.HERO_MEDAL,
        ctenums.ItemID.ACCESSORY_END_BC,
        ctenums.ItemID.SEED,
        ctenums.ItemID.BIKE_KEY, ctenums.ItemID.PENDANT, ctenums.ItemID.GATE_KEY,
        ctenums.ItemID.PRISMSHARD, ctenums.ItemID.C_TRIGGER, ctenums.ItemID.TOOLS,
        ctenums.ItemID.JERKY, ctenums.ItemID.DREAMSTONE, ctenums.ItemID.RACE_LOG,
        ctenums.ItemID.MOON_STONE, ctenums.ItemID.SUN_STONE, ctenums.ItemID.RUBY_KNIFE,
        ctenums.ItemID.YAKRA_KEY, ctenums.ItemID.CLONE, ctenums.ItemID.TOMAS_POP,
        ctenums.ItemID.BUCKETFRAG, ctenums.ItemID.JETSOFTIME, ctenums.ItemID.PENDANT_CHARGE,
        ctenums.ItemID.RAINBOW_SHELL, ctenums.ItemID.UNUSED_EC, ctenums.ItemID.UNUSED_ED,
        ctenums.ItemID.UNUSED_EE, ctenums.ItemID.UNUSED_EF, ctenums.ItemID.UNUSED_F0,
        ctenums.ItemID.UNUSED_F1,
    ]

    if pool_type == battlerewards.RewardPoolType.SHUFFLE:
        item_assignment = {
            enemy_id: getattr(stats, attr_name) for enemy_id, stats in enemy_stat_dict.items()
            if enemy_id in enemy_pool
        }
    elif pool_type == battlerewards.RewardPoolType.RANDOM:
        allowed_items = [
            item_id for item_id in ctenums.ItemID
            if item_id not in restricted_items
        ]

        item_assignment = {
            enemy_id: rng.choice(allowed_items)
            for enemy_id in enemy_pool
        }
    else:
        raise TypeError

    for enemy_id, item_id in item_assignment.items():
        setattr(enemy_stat_dict[enemy_id], attr_name, item_id)

    for enemy_id in ctenums.EnemyID:
        if enemy_id in item_assignment:
            setattr(enemy_stat_dict[enemy_id], attr_name, item_assignment[enemy_id])
        else:
            setattr(enemy_stat_dict[enemy_id], attr_name, ctenums.ItemID.NONE)


def mark_charm_and_drop(
        enemy_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        mark_charm: bool,
        mark_drop: bool
):
    """Add a suffix to names of enemies with charm and/or drop."""
    for enemy_id, enemy_stats in enemy_dict.items():
        suffix = ""
        if mark_charm and enemy_stats.charm_item != ctenums.ItemID.NONE:
            suffix += "C"
        if mark_drop and enemy_stats.drop_item != ctenums.ItemID.NONE:
            suffix += "D"

        if suffix and "{null}" not in enemy_stats.name:
            cur_name = enemy_stats.name.ljust(0xB, " ")
            cur_name = cur_name[:-len(suffix)] + suffix
            enemy_stats.name = cur_name


def apply_reward_rando(
        reward_options: battlerewards.BattleRewards,
        enemy_dict: dict[ctenums.EnemyID, enemystats.EnemyStats],
        rng: RNGType
):

    drop_enemy_pool = get_enemy_pool(enemy_dict, reward_options.drop_options, rng)
    assign_rewards(drop_enemy_pool, reward_options.drop_options, enemy_dict, rng)

    charm_enemy_pool = get_enemy_pool(enemy_dict, reward_options.charm_options, rng)
    assign_rewards(charm_enemy_pool, reward_options.charm_options, enemy_dict, rng)

    mark_charm_and_drop(enemy_dict, reward_options.charm_options.mark_charmable_enemies,
                        reward_options.drop_options.mark_dropping_enemies)

    # for enemy_id, stats in enemy_dict.items():
    #     has_charm = stats.charm_item != ctenums.ItemID.NONE
    #     has_drop = stats.drop_item != ctenums.ItemID.NONE
    #
    #     if has_charm or has_drop:
    #         print(f"{stats.name}\t{stats.charm_item}\t{stats.drop_item}")




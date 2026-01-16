"""Module for adding objective checks to a rom"""
import typing

from ctrando.arguments import objectiveoptions
from ctrando.bosses import bosstypes as bty
from ctrando.items import itemdata
from ctrando.common import ctenums, ctrom, memory, distribution
from ctrando.common.random import RNGType
from ctrando.locations import scriptmanager
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.objectives import objectivetypes as oty
from ctrando.strings import ctstrings


def get_objective_count_checks(
        script: LocationEvent,
        obj_settings: objectiveoptions.ObjectiveOptions,
):
    ret_ef = (
        EF()
        .add_if(
            EC.if_not_flag(memory.Flags.HAS_ALGETTY_PORTAL),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_algetty_portal_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("{line break}  Earthbound Village Portal (Mt. Woe)"
                                         "{line break}                   Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.HAS_ALGETTY_PORTAL))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.BUCKET_AVAILABLE),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_bucket_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("{line break}     Bucket Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.BUCKET_AVAILABLE))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.LAVOS_GAUNTLET_DISABLED),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_gauntlet_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("{line break}     Lavos Gauntlet Disabled!{null}")
                )).add(EC.set_flag(memory.Flags.LAVOS_GAUNTLET_DISABLED))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE),
            EF()
            .add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_omen_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("{line break}    Omen Boss Unlocked!{null}")
                )).add(EC.set_flag(memory.Flags.BLACK_OMEN_ZEAL_AVAILABLE))
                .add(EC.set_flag(memory.Flags.OW_OMEN_DARKAGES))
                # .add(EC.set_flag(memory.Flags.OW_OMEN_PAST))  # Avoid lag with Magus Castle
                .add(EC.set_flag(memory.Flags.OW_OMEN_FUTURE))
            )
        ).add_if(
            EC.if_not_flag(memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS),
            EF().add_if(
                EC.if_mem_op_value(memory.Memory.OBJECTIVES_COMPLETED,
                                   OP.GREATER_OR_EQUAL,
                                   obj_settings.num_timegauge_objectives),
                EF()
                .add(EC.auto_text_box(
                    script.add_py_string("{line break}    1999 Added to Epoch!{null}")
                )).add(EC.set_flag(memory.Flags.HAS_APOCALYPSE_TIMEGAUGE_ACCESS))
            )
        )
    )

    return ret_ef


def write_simple_objective_to_ct_rom(
        script_manager: scriptmanager.ScriptManager,
        objective_item_id: ctenums.ItemID,
        objective_flag: memory.Flags,
        objective_locator: oty.HookLocator,
        objective_settings: objectiveoptions.ObjectiveOptions,
        temp_script_addr: int = 0x7F0310,
        object_id: typing.Optional[int] = None,
        function_id: typing.Optional[FID] = None,
        force_exploremode_off: bool = False,
):
    """
    Write an objective check to a ctrom (via script manager).
    - Use objective_locator to find where the hook should go.
    - Add an object to the script which handles the check unless obj/func
      are set (So multiple objectives can be handled by the same object)
    """

    hook_data = objective_locator(script_manager)
    script = hook_data.script
    pos = hook_data.pos

    if object_id is None:
        hook_object_id = script.num_objects
        hook_function_id = FID.ARBITRARY_0
    else:
        if function_id is None:
            raise ValueError("Object provided but no function provided")

        hook_object_id = object_id
        hook_function_id = function_id

    priority = 4  # shouldn't matter
    new_cmds = EF().add(EC.call_obj_function(hook_object_id, hook_function_id, priority, FS.HALT))
    if force_exploremode_off:
        new_cmds = (
            EF().add(EC.set_explore_mode(False))
            .append(new_cmds)
            .add(EC.set_explore_mode(True))
        )

    script.insert_commands(new_cmds.get_bytearray(), pos)

    if object_id is None:
        new_object_id = script.append_empty_object()
        if new_object_id != hook_object_id:
            raise ValueError

        script.set_function(
            hook_object_id, FID.STARTUP,
            EF().add(EC.return_cmd()).add(EC.end_cmd())
        )
        script.set_function(hook_object_id, FID.ACTIVATE, EF().add(EC.return_cmd()))
        script.set_function(hook_object_id, FID.TOUCH, EF().add(EC.return_cmd()))

    script.set_function(
        hook_object_id, hook_function_id,
        EF()
        .add_if(
            EC.if_flag(objective_flag),
            EF().add(EC.return_cmd())
        )
        .add(EC.set_flag(objective_flag))
        .add_if(
            EC.if_has_item(objective_item_id),
            EF().add(EC.remove_item(objective_item_id))
        )
        .add(EC.assign_val_to_mem(objective_item_id, 0x7F0200, 1))
        .add(EC.auto_text_box(
            script.add_py_string("{line break}   Objective {item} Complete!{null}")
        ))
        .add(EC.assign_mem_to_mem(memory.Memory.OBJECTIVES_COMPLETED,
                                   temp_script_addr, 1))
        .add(EC.increment_mem(temp_script_addr))
        .add(EC.assign_mem_to_mem(temp_script_addr,
                                  memory.Memory.OBJECTIVES_COMPLETED, 1))
        .append(get_objective_count_checks(script, objective_settings))
        .add(EC.return_cmd())
    )


def write_quest_objective(
        script_manager: scriptmanager.ScriptManager,
        quest_id: oty.QuestID,
        objective_item_id: ctenums.ItemID,
        objective_flag: memory.Flags,
        objective_settings: objectiveoptions.ObjectiveOptions
):
    """Writes a quest objective to the rom via the script manager."""

    # quest_data = oty.get_quest_data(quest_id)
    quest_locator = oty.get_quest_locator(quest_id)

    for locator in quest_locator:
        write_simple_objective_to_ct_rom(
            script_manager,
            objective_item_id,
            objective_flag,
            locator,
            objective_settings,
        )


def get_random_objectives(
        rng: RNGType
        # Eventually objective settings
) -> list[oty.ObjectiveType]:
    quest_list = list(oty.QuestID)
    starting_quest = 0
    ending_quest = starting_quest + 8

    quests = rng.sample(quest_list, 8)

    return quests


def get_objective_spec_distribution(
        obj_spec: str,
) -> distribution.Distribution[oty.ObjectiveType]:
    obj_spec = objectiveoptions.parse_objective_str(obj_spec)

    weight_value_pairs: list[tuple[float, list[oty.ObjectiveType]]] = []
    parts = obj_spec.split(",")

    for part in parts:
        if ":" in part:
            weight, obj_str = part.split(":")
        else:
            weight, obj_str = 1.0, part

        values = oty.get_obj_keys(obj_str)
        weight_value_pairs.append((weight, values))

    return distribution.Distribution(*weight_value_pairs)


def get_linked_objs(
    boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
) -> list[tuple[oty.ObjectiveType, ...]]:
    linked_spots = oty.get_associated_objectives()

    links = [
        tuple(boss_assign_dict.get(item, item) for item in link)
        for link in linked_spots
    ]

    return links


def get_random_objectives_from_settings(
        objective_settings: objectiveoptions.ObjectiveOptions,
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        rng: RNGType
) -> list[oty.ObjectiveType]:
    total_keys = list(bty.BossID) + list(oty.QuestID) + [None]
    base_distributions: list[distribution.Distribution[oty.ObjectiveType]] = [
        get_objective_spec_distribution(obj_spec)
        for obj_spec in objective_settings.objective_specifiers
    ]

    links = get_linked_objs(boss_assign_dict)
    links = links + oty.get_overlapping_quests()

    pool = list(total_keys)
    ret_list: list[oty.ObjectiveType] = []
    for obj_id in range(8):
        pairs = base_distributions[obj_id].get_weight_object_pairs()

        # Restrict pairs to items in pool
        for ind, (weight, obj) in enumerate(pairs):
            obj = [x for x in obj if x in pool]
            pairs[ind] = (weight, obj)

        try:
            cleaned_dist = distribution.Distribution[oty.ObjectiveType](*pairs)
            new_obj = cleaned_dist.get_random_item(rng)
        except distribution.ZeroWeightException:
            new_obj = rng.choice(tuple(x for x in pool if x in oty.QuestID))

        ret_list.append(new_obj)
        for link in links:
            if new_obj in link:
                remove_list = (x for x in link if x in pool and x is not None)
                for obj in remove_list:
                    pool.remove(obj)

        if new_obj is not None and new_obj in pool:
            pool.remove(new_obj)

    return ret_list


def write_test_objectives(
        script_manager: scriptmanager.ScriptManager,
        boss_assign_dict: dict[bty.BossSpotID, bty.BossID],
        item_manager: itemdata.ItemDB,
        objective_settings: objectiveoptions.ObjectiveOptions,
        objectives: list[oty.ObjectiveType],
):
    """
    Testing the objective system with some quests.
    """

    # put a note at every boss spot.
    # test = oty.get_boss_locator_dict()
    # for key, val in test.items():
    #     hook_data = val(script_manager)
    #     script, pos = hook_data.script, hook_data.pos
    #     name = key.name.lower().replace("_", " ")
    #     script.insert_commands(
    #         EC.auto_text_box(script.add_py_string(f"{name}" + "{null}")).to_bytearray(),
    #         pos
    #     )
    #
    #     if isinstance(val, oty.CommandSequenceLocator) and key == bty.BossSpotID.TYRANO_LAIR_NIZBEL:
    #         print(val.loc_id, val.cmd_sequence)
    #         print(script.get_function(val.obj_id, val.func_id))
    #         input()

    item_pool = [
        ctenums.ItemID.OBJECTIVE_1, ctenums.ItemID.OBJECTIVE_2,
        ctenums.ItemID.OBJECTIVE_3, ctenums.ItemID.OBJECTIVE_4,
        ctenums.ItemID.OBJECTIVE_5, ctenums.ItemID.OBJECTIVE_6,
        ctenums.ItemID.OBJECTIVE_7, ctenums.ItemID.OBJECTIVE_8,
    ]

    obj_flags = [
        memory.Flags.OBJECTIVE_1_COMPLETE, memory.Flags.OBJECTIVE_2_COMPLETE,
        memory.Flags.OBJECTIVE_3_COMPLETE, memory.Flags.OBJECTIVE_4_COMPLETE,
        memory.Flags.OBJECTIVE_5_COMPLETE, memory.Flags.OBJECTIVE_6_COMPLETE,
        memory.Flags.OBJECTIVE_7_COMPLETE, memory.Flags.OBJECTIVE_8_COMPLETE
    ]

    quests = objectives

    descs: list[str] = []
    for item_id, obj_id, flag in zip(item_pool, quests, obj_flags):
        if obj_id is None:
            continue
        elif isinstance(obj_id, oty.QuestID):
            quest_data = oty.get_quest_data(obj_id)
            item_name = quest_data.name
            item_desc = quest_data.desc
            locators = oty.get_quest_locator(obj_id)
        elif isinstance(obj_id, bty.BossID):
            boss_name_abbrev = oty.get_boss_item_name(obj_id)
            boss_name = obj_id.name.replace("_", " ").title()
            item_name = f"*{boss_name_abbrev}"
            item_desc = f"Defeat {boss_name}"
            locators = oty.get_boss_locator(obj_id, boss_assign_dict)
        else:
            raise TypeError

        item_manager[item_id].set_name_from_str(item_name)
        item_manager[item_id].set_desc_from_str(item_desc)
        item_manager[item_id].secondary_stats.is_key_item = True
        item_manager[item_id].secondary_stats.is_unsellable = True

        descs.append(item_desc)

        for locator in locators:
            write_simple_objective_to_ct_rom(
                script_manager,
                item_id,
                flag,
                locator,
                objective_settings
            )

    add_items_func = EF()
    for (item_id, obj_key) in zip(item_pool, objectives):
        if obj_key is not None:
            add_items_func.add(EC.add_item(item_id))
    add_items_func.add(EC.return_cmd())

    script = script_manager[ctenums.LocID.LOAD_SCREEN]
    script.set_function(1, FID.TOUCH, add_items_func)

    # Add a check right after waking up for 0-count rewards
    script = script_manager[ctenums.LocID.CRONOS_ROOM]
    obj_id = script.append_empty_object()
    script.set_function(obj_id, FID.STARTUP,
                        EF().add(EC.return_cmd()).add(EC.end_cmd()))
    script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))
    script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))
    script.set_function(
        obj_id, FID.ARBITRARY_0,
        get_objective_count_checks(script, objective_settings)
    )

    pos = script.find_exact_command(
        EC.call_pc_function(0, FID.ARBITRARY_6, 4, FS.CONT),
        script.get_object_start(8)
    )
    script.insert_commands(
        EC.call_obj_function(obj_id, FID.ARBITRARY_0, 4, FS.HALT).to_bytearray(),
        pos
    )

    # Modify Mom's text with objective thresholds.
    obj_text = (
        "MOM: Check your objectives in your{line break}"
        "inventory.  Your completion rewards{line break}"
        "are:{page break}"
    )

    obj_rewards = {
        "Algetty Portal": objective_settings.num_algetty_portal_objectives,
        "Bucket": objective_settings.num_bucket_objectives,
        "Lavos Gauntlet": objective_settings.num_gauntlet_objectives,
        "Omen Boss": objective_settings.num_omen_objectives,
        "1999 Time Gauge": objective_settings.num_timegauge_objectives,
    }

    items = sorted(
        [(key, val) for key, val in obj_rewards.items() if val in range(1, 9)],
        key=lambda x: x[1]
    )
    obj_rewards = dict(items)

    reward_text = ""
    for ind, (key, val) in enumerate(obj_rewards.items()):
        count_str = "Objectives:" if val > 1 else "Objective:"
        reward_text += f"{val} {count_str} {key}"
        if ind + 1 == len(items):
            end_str = "{null}"
        elif (ind + 1) % 4 == 0:
            end_str = "{page break}"
        else:
            end_str = "{line break}"
        reward_text += end_str

    obj_text += reward_text
    script.strings[6] = ctstrings.CTString.from_ascii(obj_text)

    script = script_manager[ctenums.LocID.LOAD_SCREEN]
    find_cmd = EC.assign_val_to_mem(
        0x0100, memory.Memory.SHOP_MULTIPLIER,2
    )

    obj_str = ""
    for ind, desc in enumerate(descs):
        obj_str += f"{ind+1}: {desc}"
        if ind == len(descs) - 1:
            obj_str += "{null}"
        elif (ind + 1) % 4 == 0:
            obj_str += "{full break}"
        else:
            obj_str += "{linebreak+0}"

    new_obj_id = script.append_empty_object()
    script.set_function(
        new_obj_id, FID.STARTUP,
        EF().add(EC.return_cmd()).add(EC.end_cmd())
    )
    script.set_function(
        new_obj_id, FID.ACTIVATE,
        EF()
        .set_label("start")
        .add(EC.decision_box(script.add_py_string(
            "      View Objectives{linebreak+0}"
            "      Start{null}"
        ), 0, 1))
        .add_if(
            EC.if_result_equals(0),
            EF().add(EC.auto_text_box(
                script.add_py_string(obj_str)
            ))
            .jump_to_label(EC.jump_back(), "start")
        )
        .add(EC.return_cmd())
    )

    pos = script.find_exact_command(find_cmd)
    script.insert_commands(
        EC.call_obj_function(new_obj_id, FID.ACTIVATE, 4, FS.HALT)
        .to_bytearray(), pos
    )

    # Repeat objective rewards in kitchen
    # script = script_manager[ctenums.LocID.CRONOS_KITCHEN]
    # pos = script.find_exact_command(
    #     EC.if_pc_active(ctenums.CharID.CRONO),
    #     script.get_function_start(0xF, FID.ACTIVATE)
    # )
    #
    # obj_reminder_func = (
    #     EF()
    #     .add(EC.auto_text_box(
    #         script.add_py_string()
    #     ))
    # )


def write_quest_counters(
        script_manager: scriptmanager.ScriptManager,
        temp_addr: int = 0x7F0310,
        excluded_quests: typing.Optional[list[oty.QuestID]] = None
):
    if excluded_quests is None:
        excluded_quests = []

    for quest_id in oty.QuestID:
        if quest_id in excluded_quests:
            continue

        locators = oty.get_quest_locator(quest_id)
        for locator in locators:
            hook_data = locator(script_manager)

            script = hook_data.script
            pos = hook_data.pos

            script.insert_commands(
                EF()
                .add(EC.assign_mem_to_mem(memory.Memory.QUESTS_COMPLETED, temp_addr, 1))
                .add(EC.increment_mem(temp_addr))
                .add(EC.assign_mem_to_mem(temp_addr, memory.Memory.QUESTS_COMPLETED, 1))
                .get_bytearray(), pos
            )


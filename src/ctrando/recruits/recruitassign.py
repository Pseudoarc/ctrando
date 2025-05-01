"""
Module with some useful functions for generating recruit event code.
"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.common.ctenums import ItemID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF

_char_music: dict[ctenums.CharID, int] = {
    ctenums.CharID.CRONO: 0x18,
    ctenums.CharID.MARLE: 0x7,
    ctenums.CharID.LUCCA: 0x1B,
    ctenums.CharID.FROG: 0x2A,
    ctenums.CharID.ROBO: 0xE,
    ctenums.CharID.AYLA: 0xB,
    ctenums.CharID.MAGUS: 0x28
}


def get_char_music(char_id: ctenums.CharID) -> int:
    """
    Get a character's theme music.
    """
    return _char_music[char_id]


def build_recruit_function(
        char_id: ctenums.CharID,
        is_recruited_flag: memory.Flags,
        pc_count_addr: int
        ) -> EF:
    """
    Returns a basic recruitment function.
    - If 1 or 2 PCs, add the character directly
    - Otherwise, bring up the switch menu after adding
    """
    not_full_recruit_func = (
        EF()
        .add(EC.party_follow())
        .add(EC.set_explore_mode(False))
        .add(EC.reset_animation())
        .add(EC.set_own_facing_pc(0))
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.generic_command(0x95, 0))  # Follow PC00 once
        .add(EC.add_pc_to_active(char_id))
        .add(EC.load_pc_in_party(char_id))
        .add(EC.set_flag(is_recruited_flag))
        .add(EC.name_pc(int(char_id)))
        .append(owu.get_increment_addr(memory.Memory.RECRUITS_OBTAINED))
        .add(EC.set_explore_mode(True))
        # This will end execution, so it needs to be last.
        .add(EC.set_controllable_infinite())
    )

    full_party_recruit_func = (
        EF()
        .add(EC.set_move_properties(False, True))
        .add(EC.set_move_destination(True, True))
        .add(EC.set_own_facing_pc(0))
        .add(EC.generic_command(0x95, 0))  # Follow PC00 once
        .add(EC.name_pc(char_id))
        .add(EC.add_pc_to_reserve(char_id))
        .add(EC.load_pc_in_party(char_id))
        .add(EC.set_flag(is_recruited_flag))
        .add(EC.set_explore_mode(True))
        .add(EC.switch_pcs())
    )

    recruit_func = (
        EF()
        .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, pc_count_addr, 1))
        .add_if_else(
            EC.if_mem_op_value(pc_count_addr, OP.GREATER_THAN, 7, 1),
            not_full_recruit_func,
            full_party_recruit_func
        )
        # .add(EC.set_explore_mode(True))
        .add(EC.return_cmd())
    )

    return recruit_func


type GearSpec = tuple[ItemID, ItemID, ItemID, ItemID]

_dynamic_gear_specs: dict[ctenums.CharID, dict[int, GearSpec]] = {
    ctenums.CharID.CRONO: {
        10: (ItemID.WOOD_SWORD, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.BANDANA),
        20: (ItemID.BOLT_SWORD, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.BANDANA),
        30: (ItemID.FLINT_EDGE, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.BANDANA),
        40: (ItemID.AEON_BLADE, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.SPEED_BELT)
    },
    ctenums.CharID.MARLE: {
        10: (ItemID.BRONZE_BOW, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.RIBBON),
        20: (ItemID.LODE_BOW, ItemID.BERET, ItemID.MAIDENSUIT, ItemID.RIBBON),
        30: (ItemID.SAGE_BOW, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.RIBBON),
        40: (ItemID.DREAM_BOW, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.HIT_RING),
    },
    ctenums.CharID.LUCCA: {
        10: (ItemID.AIR_GUN, ItemID.HIDE_CAP, ItemID.HIDE_TUNIC, ItemID.SIGHTSCOPE),
        20: (ItemID.AUTO_GUN, ItemID.BERET, ItemID.MAIDENSUIT, ItemID.SIGHTSCOPE),
        30: (ItemID.RUBY_GUN, ItemID.TABAN_HELM, ItemID.GOLD_SUIT, ItemID.SIGHTSCOPE),
        40: (ItemID.DREAM_GUN, ItemID.TABAN_HELM, ItemID.TABAN_VEST, ItemID.BANDANA)
    },
    ctenums.CharID.ROBO: {
        20: (ItemID.TIN_ARM, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.DEFENDER),
        30: (ItemID.STONE_ARM, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.DEFENDER),
        40: (ItemID.MAGMA_HAND, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.MUSCLERING),
    },
    ctenums.CharID.FROG: {
        10: (ItemID.BRONZEEDGE, ItemID.BRONZEHELM, ItemID.BRONZEMAIL, ItemID.POWERGLOVE),
        20: (ItemID.IRON_SWORD, ItemID.IRON_HELM, ItemID.TITAN_VEST, ItemID.POWERGLOVE),
        30: (ItemID.FLASHBLADE, ItemID.GOLD_HELM, ItemID.GOLD_SUIT, ItemID.POWERGLOVE),
        40: (ItemID.FLASHBLADE, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.POWERSCARF),
    },
    ctenums.CharID.AYLA: {
        40: (ItemID.FIST_3, ItemID.ROCK_HELM, ItemID.MESO_MAIL, ItemID.POWERSCARF),
    },
    ctenums.CharID.MAGUS: {
        40: (ItemID.DARKSCYTHE, ItemID.DOOM_HELM, ItemID.RAVENARMOR, ItemID.AMULET)
    }
}

def get_dynamic_gear_function(
        char_id: ctenums.CharID,
        temp_addr: int = 0x7F0308
) -> EF:

    stat_block_start = 0x7E2600 + 0x50*char_id
    cur_level_offset = 0x12
    equip_offset = 0x27  # Helm, Arm, Weap, Acc
    equip_addr = stat_block_start + equip_offset

    # print(f"{stat_block_start:06X}")
    # print(f"{stat_block_start+cur_level_offset:06X}")
    # input()

    func = (
        EF()
        .add(EC.assign_mem_to_mem(stat_block_start+cur_level_offset,
                                  temp_addr, 1))
    )

    progression = _dynamic_gear_specs[char_id]
    num_entries = len(progression.keys())
    progression = {
        key: progression[key] for key in sorted(progression.keys())
    }

    for ind, (level, (weapon, helm, armor, accessory)) in enumerate(progression.items()):
        first_bytes = (armor << 8) + helm
        second_bytes = (accessory << 8) + weapon
        assign_func = (
            EF()
            .add(EC.assign_val_to_mem(first_bytes, equip_addr, 2))
            .add(EC.assign_val_to_mem(second_bytes, equip_addr+2, 2))
        )
        if ind == num_entries:
            func.append(assign_func)
        else:
            func.add_if(
                EC.if_mem_op_value(temp_addr, OP.LESS_THAN, level),
                assign_func.jump_to_label(EC.jump_forward(), "end")
            )

    func.set_label("end")
    func.add(EC.pause(0))

    return func

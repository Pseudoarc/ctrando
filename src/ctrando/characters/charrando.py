"""Module for allowing duplicate characters"""
import copy
import dataclasses
import functools
import typing

from ctrando.arguments import characteroptions
from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM

from ctrando.base.openworld import prisoncatwalks, factorypowercore, prisoncells, spekkio

from ctrando.characters import ctpcstats
from ctrando.common import asmpatcher, byteops, ctrom, ctenums, memory
from ctrando.common.random import RNGType
from ctrando.items import itemdata

from ctrando.locations import scriptmanager, locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF

def reassign_bytes(
        orig_bytes: typing.ByteString,
        reassign_dict: dict[int, int],
        entry_width: int
) -> bytearray:
    """
    Shuffle entries in binary data.  The reassign_dict is to be interpreted
    as entry #key needs orig entry #value.
    """
    out_b = bytearray(orig_bytes)

    for key, val in reassign_dict.items():
        orig_start = entry_width*val
        orig_data = orig_bytes[orig_start: orig_start+entry_width]
        out_start = entry_width*key
        out_b[out_start:out_start+entry_width] = orig_data[:]

    return out_b


@dataclasses.dataclass()
class ShuffledRangeData:
    data_start: int
    entry_width: int
    num_entries: int


_gfx_data = ShuffledRangeData(0x242000, 3, 7)
_sasm_data = ShuffledRangeData(0x242300, 3, 7)
_really_unk_data = ShuffledRangeData(0x02B519, 1, 7)
_atk_byte_melee_data = ShuffledRangeData(0x0D4000, 1, 7)
_atk_byte_ranged_data = ShuffledRangeData(0x0D4000+7, 1, 7)
_atk_byte_crit_data = ShuffledRangeData(0x0D4000+14, 1, 7)
_death_anim_data = ShuffledRangeData(0x115F42, 4, 7)
_portrait_data = ShuffledRangeData(0x3F0000, 0x480, 7)
_attacK_range_spec = ShuffledRangeData(0x0CF63C, 1, 7)
_menu_damage_formulas = ShuffledRangeData(0x0291DB, 2, 7)


def write_shuffled_range(
        ct_rom: ctrom.CTRom,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        range_data: ShuffledRangeData
):

    ct_rom.seek(range_data.data_start)
    orig_data = ct_rom.read(range_data.entry_width*range_data.num_entries)
    shuffled_data = reassign_bytes(orig_data, reassign_dict, range_data.entry_width)
    ct_rom.seek(range_data.data_start)
    ct_rom.write(shuffled_data)


def reassign_graphics(
        ct_rom: ctrom.CTRom,
        reassignment: dict[ctenums.CharID, ctenums.CharID]
):
    # CT uses distance between consecutive pointers to determine packet size.
    # When we reassign, this is meaningless.  Make a copy of the pointers and
    # use the copy to do the endpoint lookups.

    # 242600	242783	PTR	N	"Pointers to character animations (?)
    # Probably this goes all the way to 0x242800 (2 byte ptrs)
    anim_start = 0x242600
    anim_end = 0x0243800 # 0x242784
    anim_size = anim_end - anim_start

    # 242800	242983	PTR	N	"Pointers to unconfirmed animation data
    # Probably this goes all the way to 0x242A00 (2 byte ptrs)
    unk_start = 0x242800
    unk_end = 0x242A00 # 0x242984
    unk_size = unk_end - unk_start

    endpoint_dict = {int(key+1):int(val+1) for key, val in reassignment.items()}

    ct_rom.seek(anim_start)
    anim_ptrs = ct_rom.read(anim_size)
    reassign_anim_ptrs = reassign_bytes(anim_ptrs, reassignment, 2)
    reassign_anim_endpt_ptrs = reassign_bytes(anim_ptrs, endpoint_dict, 2)
    ct_rom.seek(anim_start)
    ct_rom.write(reassign_anim_ptrs)
    anim_endpt_addr = ct_rom.write_data_to_freespace(reassign_anim_endpt_ptrs, 0x410000)

    ct_rom.seek(unk_start)
    unk_ptrs = ct_rom.read(unk_size)
    reassign_unk_ptrs = reassign_bytes(unk_ptrs, reassignment, 2)
    reassign_unk_endpt_ptrs = reassign_bytes(unk_ptrs, endpoint_dict, 2)
    ct_rom.seek(unk_start)
    ct_rom.write(reassign_unk_ptrs)
    unk_endpt_addr = ct_rom.write_data_to_freespace(reassign_unk_endpt_ptrs, 0x410000)

    # Anims:  Animation data is divided into 4 chunks, one for each direction the
    # character can face.  To determine where these chunks begin/end, the game
    # finds the size of the anim data by subtracting the ptr from the next ptr.
    # We are going to move the end points to the new block and read from there.
    #
    # $CC/E9EF BF 00 26 E4 LDA $E42600,x[$E4:2602]
    # $CC/E9F3 85 86       STA $86    [$00:0086]
    # $CC/E9F5 BF 01 26 E4 LDA $E42601,x[$E4:2603]
    # $CC/E9F9 85 87       STA $87    [$00:0087]
    #
    # Later for Y-menu animations.  This is loading the next pointer for
    # determining an endpoint
    # $C2/F4CE BF 02 00 E4 LDA $E40002,x[$E4:2604]
    #
    # Again, getting the endpoint by doing two INY to get to the next pointer
    # $C0/44EF C8          INY
    # $C0/44F0 C8          INY
    # $C0/44F1 B7 B5       LDA [$B5],y[$E4:2602]  <-- replace with LNG_X LDA
    # $C0/44F3 38          SEC
    # $C0/44F4 88          DEY
    # $C0/44F5 88          DEY

    # X is overwritten immediately after, so TYX and LDA from our new range
    snippet: assemble.ASMList = [
        inst.TYX(),
        inst.LDA(byteops.to_rom_ptr(anim_endpt_addr+2), AM.LNG_X),
        inst.SEC(),
        inst.NOP(),
    ]
    snippet_b = assemble.assemble(snippet)
    if not len(snippet_b) == 0x44F6 - 0x44EF:
        raise ValueError
    ct_rom.seek(0x0044EF)
    ct_rom.write(snippet_b)

    # Again for monster anims!
    # $C0/4746 C8          INY
    # $C0/4747 C8          INY
    # $C0/4748 B7 B5       LDA [$B5],y[$E4:260E]
    # $C0/474A 88          DEY
    # $C0/474B 88          DEY
    # $C0/474C 38          SEC

    ct_rom.seek(0x004746)
    ct_rom.write(snippet_b)

    # End point loading
    # $CC/EB34 BF 00 26 E4 LDA $E42600,x[$E4:260E]
    # $CC/EB38 85 88       STA $88    [$00:0088]
    # $CC/EB3A BF 00 28 E4 LDA $E42800,x[$E4:280E]

    anim_endpt_ptrs = [0x0CE9F0, 0x0CE9F6, 0x02F4CF, 0x0CEB35]
    # anim_endpt_addr = anim_endpt_addr + 2
    byteops.update_ptrs(ct_rom.getbuffer(), anim_endpt_ptrs, anim_start, anim_endpt_addr)

    # Unknown Anim data: Similar to the above.  The beginning of the next
    # object's data is used to determine length sometimes.  It's not divided by
    # four like animations.  Someone online said this data counts how many frames
    # to display each part of the animation.
    #
    # This is the next object's data being read
    # $CC/E9FB BF 00 28 E4 LDA $E42800,x[$E4:2802]
    # $CC/E9FF 85 88       STA $88    [$00:0088]
    # $CC/EA01 BF 01 28 E4 LDA $E42801,x[$E4:280B]
    # $CC/EA05 85 89       STA $89    [$00:0089]

    unk_endpt_ptrs = [0x0CE9FC, 0x0CEA02, 0x0CEB3B]
    byteops.update_ptrs(ct_rom.getbuffer(), unk_endpt_ptrs, unk_start, unk_endpt_addr)

    for range_data in (
        _gfx_data, _sasm_data, _really_unk_data,
        _atk_byte_melee_data, _atk_byte_ranged_data, _atk_byte_crit_data,
        _death_anim_data, _portrait_data, _attacK_range_spec, _menu_damage_formulas
    ):
        write_shuffled_range(ct_rom, reassignment, range_data)


def reassign_characters_config(
        char_reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        pc_stats: ctpcstats.PCStatsManager,
        char_opts: characteroptions.CharacterOptions
):

    if char_opts.use_phys_lucca:
        pc_stats.set_stat_growth(ctenums.CharID.LUCCA, ctpcstats.PCStat.HIT, 140)
    if char_opts.use_phys_marle:
        pc_stats.set_stat_growth(ctenums.CharID.MARLE, ctpcstats.PCStat.HIT, 140)


    orig_stats: dict[ctenums.CharID, ctpcstats.PCStatData] = {}
    for char_id in ctenums.CharID:
        orig_stats[char_id] = copy.deepcopy(pc_stats.pc_stat_dict[char_id])

    for char_id, reassign_id in char_reassign_dict.items():
        new_stats = copy.deepcopy(orig_stats[reassign_id])
        new_stats.stat_block.char_id = char_id

        pc_stats.pc_stat_dict[char_id] = new_stats
        pc_stats.set_character_assignment(char_id, reassign_id)



def reassign_characters(
        ct_rom: ctrom.CTRom,
        reassignment: dict[ctenums.CharID, ctenums.CharID]
):
    """Reassign Character Identities"""

    reassign_list = [reassignment[x] for x in ctenums.CharID]
    reassign_b = bytes(reassign_list)
    reassign_addr = ct_rom.write_data_to_freespace(reassign_b, 0x410000)

    reassign_graphics(ct_rom, reassignment)
    fix_overworld_sprites(ct_rom, reassign_addr)
    fix_pc_tech_targets(ct_rom, reassign_addr)


def fix_pc_tech_targets(
        ct_rom: ctrom.CTRom,
        reassign_addr: int
):
    reassign_rom_addr = byteops.to_rom_ptr(reassign_addr)

    def make_reassign_search_loop(
            target_char_id: ctenums.CharID,
            find_return_rom_addr: int,
            no_find_return_rom_addr: int
    ) -> assemble.ASMList:
        return [
            inst.TDC(),
            inst.TAX(),
            inst.PHY(),
            inst.TAY(),
            "loop_st",
            inst.LDA(0x2980, AM.ABS_Y),
            inst.TAX(),
            inst.LDA(reassign_rom_addr, AM.LNG_X),
            inst.CMP(target_char_id, AM.IMM8),
            inst.BEQ("out"),
            inst.INY(),
            inst.CPY(0x0003, AM.IMM16),
            inst.BNE("loop_st"),
            inst.TYX(),
            inst.PLY(),
            inst.JMP(no_find_return_rom_addr, AM.LNG),
            "out",
            inst.TYX(),
            inst.PLY(),
            inst.JMP(find_return_rom_addr, AM.LNG)
        ]

    # Robo area bomb routine
    #                      --------sub start--------
    # C122A4  9C 04 96       STZ $9604
    # C122A7  7B             TDC
    # C122A8  AA             TAX
    # C122A9  BD 80 29       LDA $2980,X
    # C122AC  C9 03          CMP #$03
    # C122AE  F0 07          BEQ $C122B7
    # C122B0  E8             INX
    # C122B1  E0 03 00       CPX #$0003
    # C122B4  D0 F3          BNE $C122A9
    # C122B6  60             RTS
    #                      ----------------

    hook_addr = 0x0122A7
    robo_area_rt = make_reassign_search_loop(
        ctenums.CharID.ROBO, 0xC122B7, 0xC122B6
    )

    asmpatcher.apply_jmp_patch(robo_area_rt, hook_addr, ct_rom, None, 0x410000)

    # C121D4  7B             TDC
    # C121D5  AA             TAX
    # C121D6  BD 80 29       LDA $2980,X
    # C121D9  C9 03          CMP #$03
    # C121DB  F0 07          BEQ $C121E4  # Find
    # C121DD  E8             INX
    # C121DE  E0 03 00       CPX #$0003
    # C121E1  D0 F3          BNE $C121D6
    # C121E3  60             RTS  # No find
    #                      ----------------
    hook_addr =  0x0121D4
    robo_line_rt = make_reassign_search_loop(ctenums.CharID.ROBO, 0xC121E4, 0xC121E1)
    asmpatcher.apply_jmp_patch(robo_line_rt, hook_addr, ct_rom, None, 0x410000)

    # C122D6  7B             TDC
    # C122D7  AA             TAX
    # C122D8  BD 80 29       LDA $2980,X
    # C122DB  C9 06          CMP #$06
    # C122DD  F0 07          BEQ $C122E6  # Find
    # C122DF  E8             INX
    # C122E0  E0 03 00       CPX #$0003
    # C122E3  D0 F3          BNE $C122D8
    # C122E5  60             RTS  # No Find
    #                      ----------------
    hook_addr = 0x0122D6
    magus_bh_rt = make_reassign_search_loop(
        ctenums.CharID.MAGUS, 0xC122E6, 0xC122E5
    )
    asmpatcher.apply_jmp_patch(magus_bh_rt, hook_addr, ct_rom, None, 0x410000)

def get_char_reassign_dict(
        rng: RNGType
) -> dict[ctenums.CharID, ctenums.CharID]:
    char_list = list(ctenums.CharID)

    x = { char_id: ctenums.CharID.AYLA for char_id in ctenums.CharID}
    # x[ctenums.CharID.MARLE] = ctenums.CharID.AYLA
    return x
    return {
        char_id: rng.choice(char_list) for char_id in ctenums.CharID
    }


def fix_overworld_sprites(
        ct_rom: ctrom.CTRom,
        reassign_start: int,
):

    # $7E2980, $7E2981, and $7E2982 have the pc-indices of the party.
    # We just need to apply reassign[] to them.
    # JSR $2BBC does the work.
    #
    # $C2/2B80 AF 80 29 7E LDA $7E2980[$7E:2980]
    # $C2/2B84 A0 00 B0    LDY #$B000
    # $C2/2B87 20 BC 2B    JSR $2BBC  [$C2:2BBC]
    # $C2/2B8A AF 80 29 7E LDA $7E2980[$7E:2980]
    # $C2/2B8E A0 00 BC    LDY #$BC00
    # $C2/2B91 20 CF 2B    JSR $2BCF  [$C2:2BCF]
    # $C2/2B94 AF 81 29 7E LDA $7E2981[$7E:2981]
    # $C2/2B98 A0 00 B4    LDY #$B400
    # $C2/2B9B 20 BC 2B    JSR $2BBC  [$C2:2BBC]
    # $C2/2B9E AF 81 29 7E LDA $7E2981[$7E:2981]
    # $C2/2BA2 A0 40 BC    LDY #$BC40
    # $C2/2BA5 20 CF 2B    JSR $2BCF  [$C2:2BCF]
    # $C2/2BA8 AF 82 29 7E LDA $7E2982[$7E:2982]
    # $C2/2BAC A0 00 B8    LDY #$B800
    # $C2/2BAF 20 BC 2B    JSR $2BBC  [$C2:2BBC]
    # $C2/2BB2 AF 82 29 7E LDA $7E2982[$7E:2982]
    # $C2/2BB6 A0 80 BC    LDY #$BC80
    # $C2/2BB9 4C CF 2B    JMP $2BCF  [$C2:2BCF]

    reassign_rom_addr = byteops.to_rom_ptr(reassign_start)
    def patch_block(
            _load_addr: int,
            _pc_id: int
    ):
        _return_addr = byteops.to_rom_ptr(_load_addr) + 4
        _commands: assemble.ASMList = [
            inst.LDA(0x7E2980+_pc_id, AM.LNG),
            inst.AND(0x00FF, AM.IMM16),
            inst.PHX(),
            inst.TAX(),
            inst.LDA(reassign_rom_addr, AM.LNG_X),
            inst.PLX(),
            inst.JMP(_return_addr, AM.LNG)
        ]
        asmpatcher.apply_jmp_patch(_commands, _load_addr, ct_rom, hint=0x410000)

    ptr_list = [0x022B80, 0x022B8A, 0x022B94, 0x022B9E, 0x022BA8, 0x022BB2]
    indices = [0, 0, 1, 1, 2, 2]

    for ptr, ind in zip(ptr_list, indices):
        patch_block(ptr, ind)


def modify_base_equipability(
        item_man: itemdata.ItemDB,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    for item_id in range(ctenums.ItemID.ACCESSORY_END_BC):
        item = item_man[ctenums.ItemID(item_id)]
        equippable_by = set(item.secondary_stats.get_equipable_by())
        new_equippable_by = [
            x for x in ctenums.CharID if reassign_dict[x] in equippable_by
        ]
        item.secondary_stats.set_equipable_by(new_equippable_by)


_anim_repl_dict: dict[ctenums.CharID, dict[ctenums.CharID, int]] = {

}

_static_anim_repl_dict: dict[ctenums.CharID, dict[int, dict[ctenums.CharID, int]]] = {
    ctenums.CharID.MARLE: {
        0xA8: {
            ctenums.CharID.CRONO: 0x1A,
            ctenums.CharID.LUCCA: 0x1A,
            ctenums.CharID.ROBO: 0x1A,
            ctenums.CharID.FROG: 0x1A,
            # ctenums.CharID.AYLA: 0x1A,
            ctenums.CharID.MAGUS: 0x1A
        }
    }
}


# Known issues:
#  - Marle window scene and after
#  - Robo holding door open scene
#  - Zenan Bridge
#  - Lavos various forms
def reassign_scripts(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    fix_prison_scenes(script_manager, reassign_dict)
    fix_lavos_scenes(script_manager, reassign_dict)
    fix_factory_power_core_escape(script_manager, reassign_dict)
    fix_zenan_bridge_scenes(script_manager, reassign_dict)
    # fix_other_attract_scenes(script_manager, reassign_dict)
    fix_inn_scripts(script_manager, reassign_dict)
    fix_portal_scenes(script_manager, reassign_dict)
    fix_guardian_drop(script_manager, reassign_dict)
    fix_marle_trial_scene(script_manager, reassign_dict)
    fix_spekkio_magic_learning(script_manager, reassign_dict)
    fix_eot_pc_npcs(script_manager, reassign_dict)


def fix_eot_pc_npcs(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    script = script_manager[ctenums.LocID.END_OF_TIME]
    starting_anim_dict: dict[ctenums.CharID, int | None] = {
        ctenums.CharID.CRONO: None,
        ctenums.CharID.MARLE: None,
        ctenums.CharID.LUCCA: 0x19,
        ctenums.CharID.ROBO: None,
        ctenums.CharID.FROG: 0x2A,
        ctenums.CharID.AYLA: 0x4F,
        ctenums.CharID.MAGUS: 0x22
    }

    fid_dict: dict[ctenums.CharID, FID] = {
        ctenums.CharID.CRONO: FID.ARBITRARY_0,
        ctenums.CharID.MARLE: FID.ARBITRARY_1,
        ctenums.CharID.LUCCA: FID.ARBITRARY_1,
        ctenums.CharID.ROBO: FID.ARBITRARY_6,
        ctenums.CharID.FROG: FID.ARBITRARY_0,
        ctenums.CharID.AYLA: FID.ARBITRARY_0,
        ctenums.CharID.MAGUS: FID.ARBITRARY_0
    }
    obj_id_st = 0x1D

    func_dict: dict[ctenums.CharID, EF] = {
        char_id: script.get_function(char_id+obj_id_st, fid_dict[char_id])
        for char_id in ctenums.CharID
    }

    # The full reassignment is more complicated/not worth the effort right now
    # At least this starts the npcs up in the correct animation.
    for char_id, reassign_id in reassign_dict.items():
        obj_id = obj_id_st + char_id
        script.set_function(
            obj_id, fid_dict[char_id], func_dict[reassign_id]
        )
        pos = script.get_object_start(obj_id)
        if starting_anim_dict[char_id] is None:
            if (anim_id := starting_anim_dict[reassign_id]) is not None:
                pos = script.find_exact_command(EC.return_cmd(), pos)
                script.insert_commands(
                    EC.play_animation(anim_id).to_bytearray(), pos)
        else:
            anim_id = starting_anim_dict[reassign_id]
            pos, _ = script.find_command(
                [EC.play_animation(0).command], pos
            )
            if anim_id is None:
                script.delete_commands(pos, 1)
            else:
                script.data[pos+1] = anim_id


def fix_guardian_drop(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    reassign_pc_arbs(
        script_manager[ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER],
        reassign_dict, list(range(1, 8)),
        [FID.ARBITRARY_2, FID.ARBITRARY_3, FID.ARBITRARY_4],
        [0x7F0214, 0x7F0216, 0x7F0218]
    )


def fix_inn_scripts(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):

    reassign_pc_arbs(
        script_manager[ctenums.LocID.PORRE_INN], reassign_dict,
        list(range(1, 8)), [FID.ARBITRARY_0], []
    )


def fix_other_attract_scenes(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    reassign_pc_arbs(
        script_manager[ctenums.LocID.ARRIS_DOME_GUARDIAN_CHAMBER],
        reassign_dict,
        list(range(1,8)),
        [FID.ARBITRARY_2, FID.ARBITRARY_3],
        [0x7F0214, 0x7F0216, 0x7F0218]
    )

    reassign_pc_arbs(
        script_manager[ctenums.LocID.MAGUS_CASTLE_FLEA],
        reassign_dict, list(range(1, 8)),
        [FID.ARBITRARY_1, FID.ARBITRARY_2], []
    )


def fix_zenan_bridge_scenes(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    script = script_manager[ctenums.LocID.ZENAN_BRIDGE_600]
    reassign_pc_arbs(
        script, reassign_dict,
        list(range(3, 3+7)),
        [FID.STARTUP, FID.ARBITRARY_1, FID.ARBITRARY_2],
        []
    )
    script = script_manager[ctenums.LocID.ZENAN_BRIDGE_BOSS]
    reassign_pc_arbs(
        script, reassign_dict,
        list(range(3, 3 + 7)),
        [FID.ARBITRARY_1, FID.ARBITRARY_2],
        []
    )



def fix_prison_scenes(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    script = script_manager[ctenums.LocID.PRISON_CATWALKS]
    crono_assigns = [x for x in ctenums.CharID if reassign_dict[x] == ctenums.CharID.CRONO]
    script.set_function(
        0, FID.ARBITRARY_0,
        prisoncatwalks.EventMod.make_tank_kill_func(crono_assigns)
    )

    pc_id_addr = 0x7F0218
    crono_cuff_anim_id = 0x6F
    crono_cuff_anim_alt_id = 0x43
    new_arb0 = EF()
    other_block = EF()
    for char_id in ctenums.CharID:
        if reassign_dict[char_id] == ctenums.CharID.CRONO:
            new_arb0.add_if(
                EC.if_mem_op_value(pc_id_addr, OP.EQUALS, char_id),
                EF().add(EC.static_animation(crono_cuff_anim_id))
            )
            other_block.add_if(
                EC.if_mem_op_value(pc_id_addr, OP.EQUALS, char_id),
                EF().add(EC.static_animation(crono_cuff_anim_alt_id))
            )
        else:
            new_arb0.add_if(
                EC.if_mem_op_value(pc_id_addr, OP.EQUALS, char_id),
                EF().add(EC.reset_animation())
            )

    new_arb0.add(EC.return_cmd())
    script.set_function(3, FID.ARBITRARY_0, new_arb0)

    script = script_manager[ctenums.LocID.PRISON_CELLS]
    pos = script.find_exact_command(
        EC.if_mem_op_value(memory.Memory.CRONO_TRIAL_PC1, OP.EQUALS, 0),
        script.get_function_start(
            prisoncells.EventMod.crono_obj, FID.ARBITRARY_7
        )
    )
    script.insert_commands(other_block.get_bytearray(), pos)
    pos += len(other_block)

    script.delete_jump_block(pos)


def fix_portal_scenes(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    data_dict: dict[ctenums.LocID, tuple[int, list[FID]]] = {
        ctenums.LocID.GUARDIA_FOREST_DEAD_END: (
            2, [FID.ARBITRARY_0, FID.ARBITRARY_1]
        ),
        # Bangor ok

    }

    for loc_id, (obj_id_st, fids) in data_dict.items():
        reassign_pc_arbs(
            script_manager[loc_id], reassign_dict,
            list(range(obj_id_st, obj_id_st+7)), fids, []
        )


def fix_marle_trial_scene(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):

    reassign_id = reassign_dict[ctenums.CharID.MARLE]
    if reassign_id == ctenums.CharID.MARLE:
        return


    static_anim_dict: dict[int, dict[ctenums.CharID, int]] = {
        0xC1: {  # Arms out before "FATHER"
            ctenums.CharID.CRONO: 68,
            ctenums.CharID.LUCCA: 158, # 104,
            ctenums.CharID.ROBO: 103,
            ctenums.CharID.FROG: 170,
            ctenums.CharID.AYLA: 90,
            ctenums.CharID.MAGUS: 240,
        },
        0x63 : {  # Anim while bursting through
            ctenums.CharID.CRONO: 86,  # 108 (fist), 110 (surprise) 187 (sword up)
            ctenums.CharID.LUCCA: 95, #73, # 62, #
            ctenums.CharID.ROBO: 159, # 108, # 88,
            ctenums.CharID.FROG: 156, # 139,
            ctenums.CharID.AYLA: 144,
            ctenums.CharID.MAGUS: 103,
        },
        0x61: {  # Anim when landing
            ctenums.CharID.CRONO: 87, # 224 # 47,  # 67, 68 (facing down sword out), 73 (kneel) 136 (sword in front)
            ctenums.CharID.LUCCA: 96,
            ctenums.CharID.ROBO: 151,
            ctenums.CharID.FROG: 157, # 140,
            ctenums.CharID.AYLA: 145,
            ctenums.CharID.MAGUS: 141,  # 72
        },
        0xC5: { # Holding up shard (facing left)
            ctenums.CharID.CRONO: 125,
            ctenums.CharID.LUCCA: 113, # 74,
            ctenums.CharID.ROBO: 154, # 133,
            ctenums.CharID.FROG: 219,
            ctenums.CharID.AYLA: 128,
            ctenums.CharID.MAGUS: 183, # 149,
        },
        0x42: { # Looking down/left
            ctenums.CharID.CRONO: 149,
            ctenums.CharID.LUCCA: 121, # 125, 133
            ctenums.CharID.ROBO: 57,
            ctenums.CharID.FROG: 62,
            ctenums.CharID.AYLA: 111,
            ctenums.CharID.MAGUS: 64,
        },
        0xA8: { # Embrace at end
            ctenums.CharID.CRONO: 234,
            ctenums.CharID.LUCCA: 99,
            ctenums.CharID.ROBO: 129,
            ctenums.CharID.FROG: 66,
            ctenums.CharID.AYLA: 104,
            ctenums.CharID.MAGUS: 61,
        }
    }

    normal_anim_dict: dict[int, dict[ctenums.CharID, int]] = {
        # 0x2A: {  # Jump celebration arms out
        #     ctenums.CharID.CRONO: 12
        # },
    }

    def get_repl_anim(_anim_dict: dict[int, dict[ctenums.CharID, int]],
                      _anim_id: int) -> int:
        nonlocal reassign_id

        if _anim_id not in static_anim_dict:
            return _anim_id

        _anim_dict = static_anim_dict[_anim_id]
        return _anim_dict.get(reassign_id, _anim_id)

    script = script_manager[ctenums.LocID.KINGS_TRIAL]
    pos = script.get_function_start(2, FID.ARBITRARY_0)
    end = script.get_function_end(2, FID.ARBITRARY_5)

    bounds: list[tuple[int, int]] = [
        (script.get_function_start(2, FID.ARBITRARY_0),
         script.get_function_end(2, FID.ARBITRARY_5)),
        (script.get_object_start(0x18),
         script.get_function_end(0x18, FID.ARBITRARY_0))
    ]

    for (pos, end) in bounds:
        while pos < end:
            pos, cmd = script.find_command(
                [EC.static_animation(0).command, EC.play_animation(0).command], pos)
            anim_id = script.data[pos + 1]
            if cmd.command == EC.static_animation(0).command:
                repl_id = get_repl_anim(static_anim_dict, anim_id)
            elif cmd.command == EC.play_animation(0).command:
                repl_id = get_repl_anim(normal_anim_dict, anim_id)
            else:
                raise ValueError

            script.data[pos + 1] = repl_id
            pos += len(cmd)


_load_pc_dict: dict[ctenums.CharID, int] = {
    char_id: EC.load_pc_in_party(char_id).command
    for char_id in ctenums.CharID
}
_load_pc_inv_dict: dict[int, ctenums.CharID] = {
    v:k for k, v in _load_pc_dict.items()
}
def reassign_pc_arbs(
        script: locationevent.LocationEvent,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID],
        char_obj_ids: list[int],
        function_ids: list[FID],
        pc_id_addrs: list[int],
):
    """
    Copy/Paste pc arbitrary functions into their reassigns.  This only works
    if there's no text or other pc-specific code
    :param script: The script to be edited
    :param reassign_dict: The correspondence between characters and their reassigned graphics
    :param char_obj_ids: The object ids in ctenums.CharID order.
    :param function_ids: The function ids to reassign
    :param pc_id_addrs: Memory addresses holding pc-ids which need to be reassigned
    :return: Nothing.  Edits the script in place.
    """

    func_dict: dict[ctenums.CharID, dict[FID, EF]] = {
        char_id: {
            function_id: script.get_function(char_obj_ids[char_id], function_id)
            for function_id in function_ids
        }
        for char_id in ctenums.CharID
    }

    script_offsets = {
        (pc_id_addr - 0x7F0200) // 2 for pc_id_addr in pc_id_addrs}

    for char_id, reassign_id in reassign_dict.items():
        obj_id = char_obj_ids[char_id]

        for function_id in function_ids:
            function = func_dict[reassign_id][function_id]
            if pc_id_addrs:
                function = function.copy()
                for ind, command in enumerate(function.commands):
                    if (command.command == 0x12 and
                        command.args[0] in script_offsets and
                        command.args[2] == OP.EQUALS
                    ):
                        command.args[1] = int(char_id)
                        offset = function.offsets[ind]
                        function.data[offset:offset+len(command)] = command.to_bytearray()
                    elif command.command in _load_pc_inv_dict:
                        new_cmd = EC.load_pc_in_party(char_id)
                        function.commands[ind] = new_cmd
                        offset = function.offsets[ind]
                        function.data[offset:offset + len(new_cmd)] = new_cmd.to_bytearray()
                    elif command.command == EC.load_pc_always(0).command:
                        new_cmd = EC.load_pc_always(char_id)
                        function.commands[ind] = new_cmd
                        offset = function.offsets[ind]
                        function.data[offset: offset+len(new_cmd)] = new_cmd.to_bytearray()


            script.set_function(obj_id, function_id, function)


def fix_lavos_scenes(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    reassign_pc_arbs(
        script_manager[ctenums.LocID.LAVOS_CORE],
        reassign_dict,
        list(range(1,8)),
        [FID.ARBITRARY_0, FID.ARBITRARY_1],
        [0x7F020E, 0x7F0210, 0x7F0212]
    )

    reassign_pc_arbs(
        script_manager[ctenums.LocID.TESSERACT],
        reassign_dict,
        list(range(1, 8)),
        [FID.STARTUP],
        [0x7F020E, 0x7F0210, 0x7F0212]
    )


def fix_factory_power_core_escape(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    script = script_manager[ctenums.LocID.FACTORY_RUINS_POWER_CORE]

    anim_dict = factorypowercore.EventMod.wall_hold_frame_dict

    for obj_id in range(2, 9):
        char_id = ctenums.CharID(obj_id-2)
        pos, _ = script.find_command(
            [EC.static_animation(0).command],
            script.get_function_start(obj_id, FID.ARBITRARY_4),
        )
        script.data[pos+1] = anim_dict[reassign_dict[char_id]]


def fix_spekkio_magic_learning(
        script_manager: scriptmanager.ScriptManager,
        reassign_dict: dict[ctenums.CharID, ctenums.CharID]
):
    script = script_manager[ctenums.LocID.SPEKKIO]

    reassign_pc_arbs(
        script, reassign_dict,
        list(range(1, 8)), [FID.ARBITRARY_2, FID.ARBITRARY_3], []
    )

    pos = script.find_exact_command(
        EC.if_pc_active(ctenums.CharID.CRONO),
        script.get_function_start(9, FID.ARBITRARY_0)
    )
    end = script.find_exact_command(
        EC.call_pc_function(0, FID.ARBITRARY_1, 4, FS.HALT),
        pos
    )
    script.delete_commands_range(pos, end)
    script.insert_commands(
        spekkio.EventMod.get_magic_learning_block(script, reassign_dict, False)
        .get_bytearray(), pos
    )


def main():
    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")

    from ctrando.base import basepatch
    basepatch.base_patch_ct_rom(ct_rom)

    reassign_dict: dict[ctenums.CharID, ctenums.CharID] = {
        ctenums.CharID.CRONO: ctenums.CharID.CRONO,
        ctenums.CharID.MARLE: ctenums.CharID.CRONO,
        ctenums.CharID.LUCCA: ctenums.CharID.CRONO,
        ctenums.CharID.ROBO: ctenums.CharID.CRONO,
        ctenums.CharID.FROG: ctenums.CharID.CRONO,
        ctenums.CharID.AYLA: ctenums.CharID.CRONO,
        ctenums.CharID.MAGUS: ctenums.CharID.CRONO,
    }

    reassign_characters(ct_rom, reassign_dict)

    with open("/home/ross/Documents/ct-mod.sfc", "wb") as outfile:
        outfile.write(ct_rom.getvalue())

if __name__ == "__main__":
    main()

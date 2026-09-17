"""Module for allowing duplicate characters"""
import copy
import dataclasses
import typing

from ctrando.arguments import characteroptions
from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.attacks import pctech, cttechtypes as ctty, animationscript
from ctrando.characters import charactermods
from ctrando.common import byteops, ctrom, ctenums


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

    anim_endpt_addr += 2
    # X is overwritten immediately after, so TYX and LDA from our new range
    snippet: assemble.ASMList = [
        inst.TYX(),
        inst.LDA(byteops.to_rom_ptr(anim_endpt_addr), AM.LNG_X),
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
    anim_endpt_addr = anim_endpt_addr + 2
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
        _death_anim_data, _portrait_data
    ):
        write_shuffled_range(ct_rom, reassignment, range_data)


def reassign_characters(
        ct_rom: ctrom.CTRom,
        reassignment: dict[ctenums.CharID, ctenums.CharID]
):
    """Reassign Character Identities"""

    reassign_graphics(ct_rom, reassignment)


@dataclasses.dataclass()
class TechScriptPair:
    tech: pctech.PCTech
    script: animationscript.PCTechAnimationScript


def reassign_single_tech(
        tech: pctech.PCTech,
        new_pc_id: ctenums.CharID,
):
    """Assumes techs will be in the same order for the reassignment"""

    new_tech = copy.deepcopy(tech)
    new_tech.battle_group = ctty.PCTechBattleGroup.from_charids([new_pc_id])
    mmp = new_tech.menu_mp_reqs[0]

    offset = (mmp - 1) % 8 + 1
    new_tech.menu_mp_reqs[0] = new_pc_id*8 + 1 + offset

    new_tech.graphics_header.script_id =

    return new_tech


def get_base_reassign_single_techs(
        vanilla_tech_dict: dict[int, pctech.PCTech],
        orig_pc_id: ctenums.CharID,
        reassign_pc_id: ctenums.CharID
) -> list[pctech.PCTech]:
    start_id = 1 + 8*orig_pc_id
    end_id = start_id + 8

    ret_list: list[pctech.PCTech] = []
    for tech_id in range(start_id, end_id):
        ret_list.append(
            reassign_single_tech(vanilla_tech_dict[tech_id], reassign_pc_id))

    return ret_list


def get_char_tech_scripts(
        vanilla_ct_rom: ctrom.CTRom,

)


def get_crono_single_techs(
        vanilla_rom: ctrom.CTRom,
        vanilla_tech_dict: dict[int, pctech.PCTech],
        reassign_char_id: ctenums.CharID
        # Any possible mods
) -> list[TechScriptPair]:
    techs = get_base_reassign_single_techs(
        vanilla_tech_dict, ctenums.CharID.CRONO, reassign_char_id)
    scripts =


def get_marle_single_techs(
        vanilla_tech_dict: dict[int, pctech.PCTech],
        reassign_char_id: ctenums.CharID,
        use_arrow_hail: bool,
        use_reraise: bool,

        # Any possible mods
) -> list[pctech.PCTech]:
    techs = get_base_reassign_single_techs(
        vanilla_tech_dict, ctenums.CharID.MARLE, reassign_char_id
    )

    if




def make_reassign_tech_man_single_only(
        base_tech_man: pctech.PCTechManager,
        reassignment_dict: dict[ctenums.CharID, ctenums.CharID],
        char_options: characteroptions.CharacterOptions
):
    new_tech_man = pctech.PCTechManager()
    base_techs = base_tech_man.get_all_techs()

    for char_id in ctenums.CharID:
        reassign_char_id = reassignment_dict[char_id]
        start_tech_id = 1 + char_id*8
        end_tech_id = start_tech_id + 8

        for tech_id in range(start_tech_id, end_tech_id):
            tech = base_techs[tech_id]
            if tech is None:
                raise ValueError

            new_tech_man.add_tech()



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

"""
This module provides routines for
1) Adding all decompressed sprite data to the rom and
2) Making all enemies and npcs use decompressed data
"""

from ctrando.base import basepatch
from ctrando.common import ctrom, byteops
from ctrando.compression import ctcompression

from ctrando.asm import assemble
from ctrando.asm import instructions as inst, assemble
from ctrando.asm.instructions import AddressingMode as AM


def build_gfx_copy_routine(bank: int) -> assemble.ASMList:
    """
    Generates a routine which mimics a vanilla routine for loading a tile from
    a graphics packet in the given bank.

    Notes
    -----
    This is supposed to be a very streamlined routine, so a different copy is
    used for each different bank that can have decompressed graphics.  The
    vanilla game has one for E2, E3, E4, and E5.
    """

    # Real X (gfx packet offset) sitting on Stack from pre-jump
    routine: assemble.ASMList = [
        inst.PLX(),
        inst.PHB(),
        inst.LDA(0x7F, AM.IMM8),
        inst.PHA(),
        inst.PLB(),
        inst.REP(0x20),
    ]

    from_addr = bank * 0x10000
    to_addr = 0

    for byte in range(0, 0x20, 2):
        routine += [
            inst.LDA(from_addr+byte, AM.LNG_X),
            inst.STA(to_addr+byte, AM.ABS_Y)
        ]

    routine += [
        inst.PLB(),
        inst.TYA(),
        inst.CLC(),
        inst.ADC(0x0020, AM.IMM16),
        inst.STA(0x2181, AM.ABS),
        inst.LDY(0xC5, AM.DIR),
        inst.RTL()
    ]

    return routine


def build_gfx_jump_routine(ptr_begin_offset: int) -> assemble.ASMList:
    """
    The returned routine enters with the bank in A and uses a jump table located at
    ptr_begin_offset to find the correct routine to load a tile.
    """
    # Bank in A
    # 16-bit X,Y
    # 8-bit A

    routine: assemble.ASMList = [
        inst.PHX(),
        inst.REP(0x20),
        inst.AND(0x00FF, AM.IMM16),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.SEP(0x20),
        inst.JMP(ptr_begin_offset & 0xFFFF, AM.ABS_X_16)
    ]

    return routine


def patch_graphics_loading(ct_rom: ctrom.CTRom):
    """
    Completely patches the rom to always use decompressed graphics.
    Requires *all* graphics packet pointers to point to decompressed graphics.
    """
    # C0E69B  C9 7F          CMP #$7F
    # C0E69D  D0 03          BNE $C0E6A2
    # C0E69F  82 20 02       BRL $C0E8C2
    # C0E6A2  38             SEC  <---  hook here
    # C0E6A3  E9 D2          SBC #$D2
    # C0E6A5  D0 03          BNE $C0E6AA
    # C0E6A7  82 12 01       BRL $C0E7BC

    hook_addr = 0xC0E6A2 - 0xC00000

    needed_banks = list(range(0xC0, 0x100)) + list(range(0x41, 0x60))

    dummy_rt = build_gfx_copy_routine(needed_banks[0])
    dummy_rt_b = assemble.assemble(dummy_rt)
    rt_size = len(dummy_rt_b)

    dummy_jump_rt = build_gfx_jump_routine(0)
    dummy_jump_rt_b = assemble.assemble(dummy_jump_rt)
    jump_rt_size = len(dummy_jump_rt_b)

    ptr_table_size = 0x200

    total_size = ptr_table_size + len(needed_banks)*rt_size + jump_rt_size

    start_addr = ct_rom.space_manager.get_free_addr(total_size, 0x410000)
    ptr_table_st = start_addr
    gfx_rt_st = start_addr + ptr_table_size


    gfx_rt_b = bytearray()
    cur_gfx_rt_st = gfx_rt_st

    ptr_table = bytearray([0]*0x200)
    for bank in needed_banks:
        next_rt = build_gfx_copy_routine(bank)
        next_rt_b = assemble.assemble(next_rt)

        ptr_table[2*bank:2*bank+2] = (cur_gfx_rt_st & 0xFFFF).to_bytes(2, "little")
        gfx_rt_b += next_rt_b
        cur_gfx_rt_st += len(next_rt_b)

    jump_rt = build_gfx_jump_routine(ptr_table_st)
    jump_rt_b = assemble.assemble(jump_rt)

    payload = ptr_table + gfx_rt_b + jump_rt_b
    jump_rt_st = start_addr + len(ptr_table) + len(gfx_rt_b)

    ct_rom.seek(start_addr)
    ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_USED)

    hook: assemble.ASMList = [
        inst.JSL(byteops.to_rom_ptr(jump_rt_st), AM.LNG),
        inst.RTS()
    ]
    hook_b = assemble.assemble(hook)

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_b)

    # print(f"{total_size:06X}")


def force_enemies_decompressed(ct_rom: ctrom.CTRom):
    """
    Force every enemy to use decompressed graphics packets.

    Notes
    -----
    This reclaims some bank 00 space that should be reclaimed (isn't yet).
    """

    # Original code: @ $C04775 (0x004775)
    #   LDX $6D       - Load (2*) the object number
    #   LDA $1101,X   - Look up the enemy_id of that object
    #   CMP #$F8      - Compare the enemy_id to 0xF8
    #   BCC $C04781   - If < 0xF8 jump to the compressed gfx routine
    #   BRL $C04845   - If >= 0xF8 jump to the uncompressed gfx routine

    # Upon entering the above code A holds the graphics packet id.  Only graphics packets
    # 0 through 6 (PCs) are compressed, so jump to the routines based on that.

    # @ $C04775
    #   CMP #$07      - Compare the graphics packet id to 7
    #   BCS $C04781   - If >= 7 jump to the compressed gfx routine
    #   BRA $C0477E   - If < 7 jump to the BRL

    AM = inst.AddressingMode
    routine: assemble.ASMList = [
        # inst.CMP(0x07, AM.IMM8),
        # inst.BCS(0x08, AM.REL_8),
        inst.BRA(0x07, AM.REL_8)
    ]

    routine_b = assemble.assemble(routine)

    ct_rom.seek(0x004775)
    ct_rom.write(routine_b)


def force_npcs_decompressed(ct_rom: ctrom.CTRom):
    """
    Overwrites a routine related to compression with a shorter routine for
    fetching the decompressed graphics packet pointer and writing it into the
    event script's object data.

    Notes
    -----
    Frees up some space in bank 00 which can be reclaimed (isn't yet).
    """
    routine: assemble.ASMList = [
        inst.LDA(0xE3, AM.DIR),
        inst.REP(0x20),
        inst.AND(0x00FF, AM.IMM16),
        inst.STA(0xD9, AM.DIR),
        inst.CLC(),
        inst.ADC(0xD9, AM.DIR),
        inst.ADC(0xD9, AM.DIR),
        inst.TAY(),
        inst.LDA(0xAF, AM.DIR_24_Y),
        inst.LDX(0x6D, AM.DIR),
        inst.STA(0x1280, AM.ABS_X),
        inst.INY(),
        inst.INY(),
        inst.SEP(0x20),
        inst.LDA(0xAF, AM.DIR_24_Y),
        inst.STA(0x1200, AM.ABS_X),
        inst.LDX(0xC7, AM.DIR),
        inst.SEC(),
        inst.RTS()
    ]
    routine_b = assemble.assemble(routine)
    ct_rom.seek(0x005C90)
    ct_rom.write(routine_b)

    hook: assemble.ASMList = [
        inst.SEC(),
        inst.RTS()
    ]
    hook_b = assemble.assemble(hook)
    ct_rom.seek(0x004629)
    ct_rom.write(hook_b)


def add_decompressed_gfx_packets(ct_rom: ctrom.CTRom):
    """
    Fetches each compressed npc/pc/enemy graphics packet, decompresses it,
    writes it back to the rom, and updates that packet's pointer.  Also frees
    all space used by the compressed packets.

    Notes
    -----
    This takes up a very large amount of rom data, about 10 banks worth.
    It's no trouble with exhirom expansion (adds 32 banks).
    """
    gfx_ptr_st = 0x242000
    ct_rom.seek(gfx_ptr_st + 7*3)

    packet_dict: dict[int: bytes] = {}

    for packet_id in range(7, 0xF8):
        ptr = int.from_bytes(ct_rom.read(3), "little")
        ptr = byteops.to_file_ptr(ptr)

        compr_len = ctcompression.get_compressed_length(ct_rom.getbuffer(), ptr)
        packet = ctcompression.decompress(ct_rom.getbuffer(), ptr)
        packet_dict[packet_id] = packet

        ct_rom.space_manager.mark_block(
            (ptr, ptr+compr_len),
            ctrom.freespace.FSWriteType.MARK_FREE
        )

    for packet_id, packet in packet_dict.items():
        new_addr = ct_rom.space_manager.get_free_addr(len(packet), 0x430000)
        ct_rom.seek(new_addr)
        ct_rom.write(packet, ctrom.freespace.FSWriteType.MARK_USED)

        ct_rom.seek(gfx_ptr_st + packet_id*3)
        rom_ptr = byteops.to_rom_ptr(new_addr)
        ct_rom.write(rom_ptr.to_bytes(3, "little"))


def apply_full_patch(ct_rom):
    """Applies all parts of the patch to use decompressed enemy/npc graphics"""

    force_enemies_decompressed(ct_rom)
    force_npcs_decompressed(ct_rom)
    add_decompressed_gfx_packets(ct_rom)

    patch_graphics_loading(ct_rom)


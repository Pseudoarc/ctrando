# Module for modifying xp gain after battle

from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.common import asmpatcher, ctrom, memory


def apply_share_xp(ct_rom: ctrom.CTRom):
    """
    Living party members share the xp instead of everyone getting the same regardless.
    """

    # Pushes XP to gain onto stack.
    # We will do this push, but also a push of alive-pc-modified XP
    # 8-bit A, 16-bit XY
    # C1F93E  AE 8C B2       LDX $B28C
    # C1F941  DA             PHX
    hook_addr = 0x01F93E
    return_addr = 0x01F942
    return_rom_addr = return_addr + 0xC00000

    pc1_status_addr_abs = 0xAEFF
    pc2_status_addr_abs = pc1_status_addr_abs + 1
    pc3_status_addr_abs = pc1_status_addr_abs + 2

    xp_addr_abs = 0xB28C
    routine: assemble.ASMList = [
        inst.LDX(xp_addr_abs, AM.ABS),
        inst.PHX(),
        inst.LDA(pc1_status_addr_abs, AM.ABS),
        inst.ORA(pc2_status_addr_abs, AM.ABS),
        inst.ORA(pc3_status_addr_abs, AM.ABS),
        inst.AND(0x80, AM.IMM8),
        inst.BEQ("all_alive"),
        inst.LDA(pc1_status_addr_abs, AM.ABS),
        inst.EOR(pc2_status_addr_abs, AM.ABS),
        inst.EOR(pc3_status_addr_abs, AM.ABS),
        inst.AND(0x80, AM.IMM8),
        inst.BEQ("one_alive"),
        # Two Alive
        inst.REP(0x20),
        inst.TXA(),  # XP to A
        inst.LSR(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(xp_addr_abs, AM.ABS),
        inst.BCS("overflow"),
        inst.TAX(),
        inst.BRA("end"),
        "one_alive",
        inst.REP(0x20),
        inst.TXA(),  # XP to A
        inst.ASL(mode=AM.NO_ARG),
        inst.BCS("overflow"),
        inst.ADC(xp_addr_abs, AM.ABS),
        inst.BCS("overflow"),
        inst.TAX(),
        inst.BRA("end"),
        "overflow",
        inst.LDX(0xFFFF, AM.IMM16),
        inst.BRA("end"),
        "all_alive",
        inst.LDX(xp_addr_abs, AM.ABS),
        "end",
        inst.SEP(0x20),
        inst.PHX(),
        inst.STX(xp_addr_abs, AM.ABS),
        inst.JMP(return_rom_addr, AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(routine, hook_addr, ct_rom)

    # C1F9DF  FA             PLX
    # C1F9E0  8E 8C B2       STX $B28C
    restore_addr = 0x01F9DF
    return_rom_addr = restore_addr + 0xC00004
    restore_routine: assemble.ASMList = [
        inst.PLX(),
        inst.STX(memory.Memory.TEMP_SCALED_XP_LO & 0xFFFF, AM.ABS),
        inst.PLX(),
        inst.STX(xp_addr_abs, AM.ABS),
        inst.JMP(return_rom_addr, AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(restore_routine, restore_addr, ct_rom)

    # FDAD21  AE 8C B2       LDX $B28C
    # Getting the XP ready for display.
    ct_rom.seek(0x3DAD21 + 1)
    ct_rom.write(
        (memory.Memory.TEMP_SCALED_XP_LO & 0xFFFF).to_bytes(2, "little")
    )

def apply_share_tp(ct_rom: ctrom.CTRom):
    """The party will share the TP among living members."""

    #                      --------sub start--------
    # C1F205  7B             TDC
    # C1F206  AA             TAX
    # C1F207  A9 FF          LDA #$FF
    # C1F209  9D 05 B3       STA $B305,X

    hook_addr = 0x01F205
    return_addr = 0x01F209
    return_rom_addr = return_addr + 0xC00000
    tp_addr_abs = 0xB2DB
    pc1_status_addr_abs = 0xAEFF
    pc2_status_addr_abs = pc1_status_addr_abs + 1
    pc3_status_addr_abs = pc1_status_addr_abs + 2

    # 8 bit A, 16-bit XY
    routine: assemble.ASMList = [
        inst.LDX(tp_addr_abs, AM.ABS),
        inst.LDA(pc1_status_addr_abs, AM.ABS),
        inst.ORA(pc2_status_addr_abs, AM.ABS),
        inst.ORA(pc3_status_addr_abs, AM.ABS),
        inst.AND(0x80, AM.IMM8),
        inst.BEQ("end"),
        inst.LDA(pc1_status_addr_abs, AM.ABS),
        inst.EOR(pc2_status_addr_abs, AM.ABS),
        inst.EOR(pc3_status_addr_abs, AM.ABS),
        inst.AND(0x80, AM.IMM8),
        inst.BEQ("one_alive"),
        # Two Alive
        inst.REP(0x20),
        inst.TXA(),  # XP to A
        inst.LSR(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(tp_addr_abs, AM.ABS),
        inst.BCS("overflow"),
        inst.TAX(),
        inst.BRA("end"),
        "one_alive",
        inst.REP(0x20),
        inst.TXA(),  # XP to A
        inst.ASL(mode=AM.NO_ARG),
        inst.BCS("overflow"),
        inst.ADC(tp_addr_abs, AM.ABS),
        inst.BCS("overflow"),
        inst.TAX(),
        inst.BRA("end"),
        "overflow",
        inst.LDX(0xFFFF, AM.IMM16),
        "end",
        inst.SEP(0x20),
        inst.STX(tp_addr_abs, AM.ABS),
        inst.TDC(),
        inst.TAX(),
        inst.LDA(0xFF, AM.IMM8),
        inst.JMP(return_rom_addr, AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(routine, hook_addr, ct_rom)


def fix_tp_doubling_bug(ct_rom: ctrom.CTRom):
    """Remove TP doubling bug"""

    # C1F4C3  AD DB B2       LDA $B2DB  <-- TP
    # C1F4C6  A6 00          LDX $00
    # C1F4C8  38             SEC
    # C1F4C9  FD 5A 5E       SBC $5E5A,X <--- TP to next
    # C1F4CC  9D 5A 5E       STA $5E5A,X <--- should be TP

    new_cmd_b = inst.STA(0xB2DB, AM.ABS).to_bytearray()
    ct_rom.seek(0x01F4CC)
    ct_rom.write(new_cmd_b)

    # The original does something weird.
    # Just store the new TP treshold and move on.
    ct_rom.seek(0x01F3F9)
    new_rt: assemble.ASMList = [
        inst.STA(0x5E5A, AM.ABS_X),
        inst.BRA(0x16, AM.REL_8)  # precomputed branch length
    ]
    new_rt_b = assemble.assemble(new_rt)

    ct_rom.write(new_rt_b)


def apply_xptp_mods(
        ct_rom: ctrom.CTRom,
        split_xp: bool,
        split_tp: bool,
        fix_tp_doubling: bool
):
    if split_xp:
        apply_share_xp(ct_rom)
    if split_tp:
        apply_share_tp(ct_rom)
    if fix_tp_doubling:
        fix_tp_doubling_bug(ct_rom)




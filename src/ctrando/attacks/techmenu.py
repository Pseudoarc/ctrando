"""Module for modifying the tech menu."""

from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.common import asmpatcher, byteops, ctrom

def show_all_single_techs_in_menu(ct_rom: ctrom.CTRom):
    """
    This function will modify the ct_rom so that the menu shows all techs,
    greying out unlearned techs.
    """

    # Y has char id
    # --- Computes number of techs learned ---
    # FFF87E  A9 08          LDA #$08
    # FFF880  85 00          STA $00
    # FFF882  B9 00 7F       LDA $7F00,Y
    # FFF885  4A             LSR
    # FFF886  B0 04          BCS $FFF88C
    # FFF888  C6 00          DEC $00
    # FFF88A  D0 F9          BNE $FFF885
    # ---
    #  - Now $00 has the tech level

    # --- See if magic has been learned (for showing next unlearned) ---
    # FFF88C  46 02          LSR $02
    # FFF88E  B0 09          BCS $FFF899
    # FFF890  BB             TYX
    # FFF891  A5 00          LDA $00
    # FFF893  DF 51 F9 FF    CMP $FFF951,X
    # FFF897  B0 1F          BCS $FFF8B8

    # --- Add an extra set bit into the techs-learned bitmask (for greyed out)
    # FFF899  A6 00          LDX $00
    # FFF89B  BF BB F9 FF    LDA $FFF9BB,X
    # FFF89F  F0 17          BEQ $FFF8B8
    # FFF8A1  19 00 7F       ORA $7F00,Y
    # FFF8A4  99 00 7F       STA $7F00,Y

    # --- Mark the next tech as unavailable (set bit 0x40)
    # FFF8A7  98             TYA
    # FFF8A8  0A             ASL
    # FFF8A9  0A             ASL
    # FFF8AA  0A             ASL  <--- 8*pc_id
    # FFF8AB  65 00          ADC $00  <-- + tech level
    # FFF8AD  AA             TAX
    # --- Hook here ---
    hook_rom_addr = 0xFFF8AE
    hook_addr = byteops.to_file_ptr(hook_rom_addr)
    # FFF8AE  BD 01 77       LDA $7701,X
    # FFF8B1  29 1E          AND #$1E
    # FFF8B3  09 40          ORA #$40
    # FFF8B5  9D 01 77       STA $7701,X
    # --- Return here ---
    return_rom_addr = 0xFFF8B8
    return_addr = byteops.to_file_ptr(return_rom_addr)
    # FFF8B8  C8             INY
    # FFF8B9  C0 07          CPY #$07
    # FFF8BB  90 C1          BCC $FFF87E

    # A, X, Y all 8-bit
    # X has our offset into the tech properties array
    # Y has pcid.  Will re-use this

    tech_status_abs = 0x7701
    techs_shown_bitmask_abs = 0x7F00
    rt: assemble.ASMList = [
        inst.LDA(0xFF, AM.IMM8),
        inst.STA(techs_shown_bitmask_abs, AM.ABS_Y),
        inst.PHY(),
        inst.LDY(0x00, AM.DIR),  # tech level in Y
        "loop st",
        inst.CPY(0x08, AM.IMM8),
        inst.BCS("out of loop"),
        inst.LDA(tech_status_abs, AM.ABS_X),
        inst.AND(0x1E, AM.IMM8),
        inst.ORA(0x40, AM.IMM8),
        inst.STA(tech_status_abs, AM.ABS_X),
        inst.INX(),
        inst.INY(),
        inst.BRA("loop st"),
        "out of loop",
        inst.PLY(),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, return_addr, 0x410000)


def write_cumulative_tp_in_menu(
        ct_rom: ctrom.CTRom
):
    """Shows the total TP needed to learn a tech in the menu."""
    hook_rom_addr = 0xC2BDF5
    hook_addr = byteops.to_file_ptr(hook_rom_addr)
    # C2BDF5  3C 00 77       BIT $7700,X
    # C2BDF8  50 06          BVC $C2BE00

    tp_return_rom_addr = 0xC2BDFA
    tp_return_addr = byteops.to_file_ptr(tp_return_rom_addr)
    # C2BDFA  A2 26 C0       LDX #$C026
    # C2BDFD  20 31 ED       JSR $ED31

    no_tp_return_rom_addr = 0xC2BE00
    no_tp_return_addr = byteops.to_file_ptr(no_tp_return_rom_addr)
    # C2BE00  60             RTS

    current_tech_id_dir = 0x54
    char_id_abs = 0x9A90
    char_tp_next_abs = char_id_abs + 0x2D
    tp_thresh_rom_st = 0xCC26FA
    tech_level_start_abs = 0x2830

    # 8-bit A
    # 16-bit X/Y
    rt: assemble.ASMList = [
        inst.BIT(0x7700, AM.ABS_X),
        inst.BVC("no_tp_return"),

        inst.PHY(),
        inst.SEP(0x10),
        inst.LDA(char_id_abs, AM.ABS),
        inst.TAY(),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(0x2830, AM.ABS_Y),
        inst.ADC(0x2830, AM.ABS_Y),
        inst.ADC(0x02, AM.IMM8),
        inst.TAX(),
        inst.LDA(0x2830, AM.ABS_Y),
        inst.TAY(),
        inst.REP(0x20),
        inst.LDA(char_tp_next_abs, AM.ABS),
        "loop_start",
        inst.CPY(current_tech_id_dir, AM.DIR),
        inst.BCS("end"),
        inst.ADC(tp_thresh_rom_st, AM.LNG_X),
        inst.INX(),
        inst.INX(),
        inst.INY(),
        inst.BRA("loop_start"),
        "end",
        inst.STA(char_tp_next_abs, AM.ABS),
        inst.SEP(0x20),
        inst.REP(0x10),
        inst.PLY(),
        inst.JMP(tp_return_rom_addr, AM.LNG),
        "no_tp_return",
        inst.JMP(no_tp_return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom)


def show_all_combo_techs_in_menu(ct_rom: ctrom.CTRom):
    """
    Patch the menu to show all combo techs.
    Must be called *after* techs are written in the given ct_rom.
    """

    ct_rom.seek(0x2BBF3+1)
    menu_grp_rom_addr = int.from_bytes(ct_rom.read(3), "little")

    bitmask_dir_addr = 0x01
    cur_tech_dir_addr = 0x03
    menu_style_start_abs_addr = 0x7F40 - 0x39
    # menu_style_start_abs_addr = 0x7700

    tech_id_start_abs_addr = 0x0F00
    group_id_start_abs_addr = 0x0F30

    # C2BD1D  06 01          ASL $01
    # C2BD1F  90 0A          BCC $C2BD2B
    # C2BD21  A5 03          LDA $03
    # C2BD23  99 00 0F       STA $0F00,Y
    # C2BD26  8A             TXA
    # C2BD27  99 30 0F       STA $0F30,Y
    # C2BD2A  C8             INY
    # C2BD2B  E6 03          INC $03
    # C2BD2D  A5 03          LDA $03
    # C2BD2F  C5 02          CMP $02
    # C2BD31  90 EA          BCC $C2BD1D
    # C2BD33  E6 00          INC $00


    hook_rom_addr = 0xC2BD1D
    hook_addr = byteops.to_file_ptr(hook_rom_addr)

    return_rom_addr = 0xC2BD33
    return_addr = byteops.to_file_ptr(return_rom_addr)

    new_loop: assemble.ASMList = [
        inst.LDA(menu_grp_rom_addr, AM.LNG_X),
        inst.ORA(0x29AF, AM.ABS),
        inst.CMP(0x29AF, AM.ABS),
        inst.BNE("end"),
        "loop_st",
        inst.ASL(bitmask_dir_addr, AM.DIR),
        inst.BCC("not_learned"),
        # learned tech, normal text
        inst.LDA(0x00, AM.IMM8),
        inst.BRA("after_tech_status"),
        "not_learned",
        inst.LDA(0x40, AM.IMM8),
        "after_tech_status",
        inst.PHY(),
        inst.LDY(cur_tech_dir_addr, AM.DIR),
        inst.CPY(0x39, AM.IMM8),
        inst.BCC("single_tech"),
        inst.STA(menu_style_start_abs_addr, AM.ABS_Y),
        "single_tech",
        inst.PLY(),
        inst.LDA(cur_tech_dir_addr, AM.DIR),
        inst.STA(tech_id_start_abs_addr, AM.ABS_Y),
        inst.TXA(),
        inst.STA(group_id_start_abs_addr, AM.ABS_Y),
        inst.INY(),
        inst.INC(cur_tech_dir_addr, AM.DIR),
        inst.LDA(cur_tech_dir_addr, AM.DIR),
        inst.CMP(0x02, AM.DIR),
        inst.BCC("loop_st"),
        "end",
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_loop, hook_addr, ct_rom, return_addr, 0x410000)

    # In the routine that loads a tech name, check $7700, Y to see if any other
    # effects should be applied.
    #  - Y holds a tech id
    #  - There is not enough room to accommodate all techs in this range, and I can't
    #    find a contiguous region which can.
    #  - Use $
    # C2BDC0  A2 0C          LDX #$0C
    # Hook: Change the following load conditionally on Y value
    # C2BDC2  B9 00 77       LDA $7700,Y
    # C2BDC5  89 40          BIT #$40
    # After hook
    # C2BDC7  D0 0C          BNE $C2BDD5
    # C2BDC9  A2 00          LDX #$00

    new_rt: assemble.ASMList = [
        inst.CPY(7*8, AM.IMM8),
        inst.BCS("combo"),
        inst.LDA(0x7700, AM.ABS_Y),
        inst.BRA("test"),
        "combo",
        inst.LDA(menu_style_start_abs_addr, AM.ABS_Y),
        "test",
        inst.BIT(0x40, AM.IMM8),
        inst.JMP(0xC2BDC7, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, 0x02BDC2, ct_rom, hint=0x410000)
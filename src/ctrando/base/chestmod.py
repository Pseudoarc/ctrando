"""Allow chests to contain more than items and gold"""

from ctrando.asm import assemble
from ctrando.asm import instructions as inst, assemble
from ctrando.asm.instructions import AddressingMode as AM

from ctrando.common import asmpatcher, byteops, ctenums, ctrom
from ctrando.strings import ctstrings

# Chest Data:
# - 0x8000: has gold
# - if gold flag not set, 0x4000: Is Empty
# - 0x00FF holds item id
# - Bits 0x2F00 are Unused

# Plan:
# - 0x2000 Has Tech Level or character
#   - Use 0x0100 to indicate it's tech level
#   - Use 0x0007 to store the character id
# - 0x0100 Has Flag
#   - Use 0x00FF to store a flag index

# C01E56  C2 20          REP #$20
# C01E58  BF 02 00 F5    LDA $F50002,X
# C01E5C  30 1D          BMI $C01E7B      Has Gold
# C01E5E  89 00 40       BIT #$4000       Is Empty
# C01E61  F0 03          BEQ $C01E66
# C01E63  E2 20          SEP #$20
# C01E65  60             RTS
#                      ----------------


# Setting the flags for drawing a textbox
# C01F0E  85 2A          STA $2A   # String index
# C01F10  A5 97          LDA $97   # Lead PC object (linked to textbox)
# C01F12  85 2E          STA $2E
# C01F14  64 32          STZ $32
# C01F16  A9 01          LDA #$01
# C01F18  85 29          STA $29   # Set Textbox showing status
# C01F1A  64 30          STZ $30
# C01F1C  A9 20          LDA #$20
# C01F1E  04 54          TSB $54
# C01F20  9C A1 02       STZ $02A1
# C01F23  60             RTS
#                      ----------------

_item_strs = [
    "{line break}Got 1 {item}{line break}{itemdesc}{null}",
    "{line break}             Found {value 16}G!{null}",
    "{line break}                   Empty!{null}",
    "{line break}                   Empty!{null}",
]

for char_id in ctenums.CharID:
    name_str = "{" + char_id.name.lower() + "}"
    tech_str = "{line break}" + name_str + "\'s Tech Level Increased!{null}"
    _item_strs.append(tech_str)


def move_treasure_strings(
        ct_rom: ctrom.CTRom,
        new_start: int | None = None
):
    ct_strs: list[ctstrings.CTString] = []
    offsets: list[int] = []
    cur_offset = 0

    for string in _item_strs:
        ct_str = ctstrings.CTString.from_str(string,True)
        offsets.append(cur_offset)
        ct_strs.append(ct_str)
        cur_offset += len(ct_str)

    ptr_len = 2*len(offsets)
    str_len = sum(len(x) for x in ct_strs)
    payload_len = ptr_len + str_len

    ct_rom.space_manager.mark_block(
        (0x1EFF00, 0x1EFF02),
        ctrom.freespace.FSWriteType.MARK_FREE
    )

    new_addr = ct_rom.space_manager.get_free_addr(
        payload_len, hint=0x410000
    )
    new_rom_addr = byteops.to_rom_ptr(new_addr)

    for ind, offset in enumerate(offsets):
        offsets[ind] = offset + ptr_len + (new_rom_addr & 0xFFFF)

    ptr_b = b''.join(x.to_bytes(2, "little") for x in offsets)
    ct_rom.seek(new_addr)
    ct_rom.write(ptr_b, ctrom.freespace.FSWriteType.MARK_USED)

    str_b = b''.join(ct_str for ct_str in ct_strs)
    ct_rom.write(str_b, ctrom.freespace.FSWriteType.MARK_USED)

    # Drawing the textbox
    #                      --------sub start--------
    # C020F2  A5 2A          LDA $2A
    # C020F4  8D 0C 02       STA $020C
    # C020F7  A5 54          LDA $54
    # C020F9  89 20          BIT #$20
    # C020FB  F0 0A          BEQ $C02107
    # C020FD  A2 00 FF       LDX #$FF00  <-- offset
    # C02100  8E 0D 02       STX $020D
    # C02103  A9 DE          LDA #$DE    <-- bank
    # C02105  80 07          BRA $C0210E
    # C02107  A6 2B          LDX $2B
    # C02109  8E 0D 02       STX $020D
    # C0210C  A5 2D          LDA $2D
    # C0210E  8D 0F 02       STA $020F
    # C02111  A2 00 F0       LDX #$F000
    # C02114  8E 10 02       STX $0210
    # C02117  A9 7E          LDA #$7E
    # C02119  8D 12 02       STA $0212
    # C0211C  A9 00          LDA #$00
    # C0211E  8D 14 02       STA $0214
    # C02121  22 03 00 C2    JSL $C20003
    # C02125  60             RTS
    #                      ----------------
    ct_rom.seek(0x0020FE)
    ct_rom.write(int.to_bytes(new_rom_addr & 0xFFFF, 2, "little"))

    ct_rom.seek(0x002104)
    ct_rom.write(int.to_bytes(new_rom_addr >> 16, 1))


def add_new_modes(
        ct_rom: ctrom.CTRom
):
    """Allow treasure chests to contain other rewards"""

    # The add item part - After checking gold 0x8000 and empty 0x4000
    # C01E66  29 FF 01       AND #$01FF     <-- hook here
    # C01E69  8F 00 02 7F    STA $7F0200
    # C01E6D  A8             TAY            <-- return here
    # C01E6E  E2 20          SEP #$20
    # C01E70  A9 01          LDA #$01
    # C01E72  22 03 80 C1    JSL $C18003
    hook_rom_addr = 0xC01E66
    hook_addr = byteops.to_file_ptr(hook_rom_addr)

    tech_level_start = 0x7E2830
    techs_learned_start = tech_level_start + 7
    tp_next_ram_offset = 0x7E262D
    tp_thresh_rom_start = 0xCC26FA
    stat_offset_rom_start = 0xFDA83B

    normal_return_rom_addr = 0xC01F23



    # 16 bit A/X/Y
    # We have the treasure bytes in A.  X/Y seem unimportant.
    # DP is 0x0100
    rt: assemble.ASMList = [
        inst.BIT(0x2000, AM.IMM16),   # Using 0x2000 for alt rewards
        inst.BNE("tech_reward"),
        inst.AND(0x01FF, AM.IMM16),
        inst.STA(0x7F0200, AM.LNG),
        inst.JMP(0xC01E6D, AM.LNG),
        "tech_reward",
        inst.AND(0x0007, AM.IMM16),
        inst.TAX(),
        inst.TXY(),
        inst.SEP(0x20),
        inst.LDA(tech_level_start, AM.LNG_X),
        inst.CMP(0x08, AM.IMM8),
        inst.BEQ("end"),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(tech_level_start, AM.LNG_X),
        inst.CMP(0x08, AM.IMM8),
        inst.BCC("after_setting_max"),
        inst.REP(0x20),
        inst.TYA(),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(stat_offset_rom_start, AM.LNG_X),
        inst.TAX(),
        inst.LDA(0x0000, AM.IMM16),
        inst.SEP(0x20),
        inst.LDA(0x7E0010, AM.LNG_X),
        inst.ORA(0x10, AM.IMM8),
        inst.STA(0x7E0010, AM.LNG_X),
        inst.TYX(),
        inst.LDA(tech_level_start, AM.LNG_X),
        "after_setting_max",
        inst.TAY(),
        inst.LDA(0xFF, AM.IMM8),
        "bitmask_loop_start",
        inst.CPY(0x0008, AM.IMM16),
        inst.BCS("write_bitmask"),
        inst.ASL(mode=AM.NO_ARG),
        inst.INY(mode=AM.NO_ARG),
        inst.BRA("bitmask_loop_start"),
        "write_bitmask",
        inst.STA(techs_learned_start, AM.LNG_X),
        # Write new TP till next
        inst.LDA(tech_level_start, AM.LNG_X),
        inst.CMP(0x08, AM.IMM8),
        inst.BNE("tp_next_not_max"),
        inst.REP(0x20),
        inst.LDA(0xFFFF, AM.IMM16),
        inst.TXY(),
        inst.BRA("write_tp_next"),
        "tp_next_not_max",
        inst.TXA(),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.STA(0x0020, AM.ABS),
        inst.LDA(tech_level_start, AM.LNG_X),
        inst.CLC(),
        inst.ADC(0x0020, AM.ABS),
        inst.ASL(mode=AM.NO_ARG),  # pc_id*16 + 2*tech_level
        inst.TXY(),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(tp_thresh_rom_start, AM.LNG_X),
        "write_tp_next",
        inst.STA(0x0020, AM.ABS),
        inst.TYA(),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(stat_offset_rom_start, AM.LNG_X),
        inst.TAX(),
        inst.LDA(0x0020, AM.ABS),
        inst.STA(0x7E002D, AM.LNG_X),
        "end",
        # Setting the flags for drawing a textbox
        # C01F0E  85 2A          STA $2A   # String index
        # C01F10  A5 97          LDA $97   # Lead PC object (linked to textbox)
        # C01F12  85 2E          STA $2E
        # C01F14  64 32          STZ $32
        # C01F16  A9 01          LDA #$01
        # C01F18  85 29          STA $29   # Set Textbox showing status
        # C01F1A  64 30          STZ $30
        # C01F1C  A9 20          LDA #$20
        # C01F1E  04 54          TSB $54
        # C01F20  9C A1 02       STZ $02A1
        # C01F23  60             RTS
        inst.TYA(),
        inst.SEP(0x20),
        inst.CLC(),
        inst.ADC(0x04, AM.IMM8),  # Index is 4 + pc_id
        inst.STA(0x2A, AM.DIR),
        inst.LDA(0x97, AM.DIR),
        inst.STA(0x2E, AM.DIR),
        inst.LDA(0x01, AM.IMM8),
        inst.STA(0x29, AM.DIR),
        inst.STZ(0x30, AM.DIR),
        inst.LDA(0x20, AM.IMM8),
        inst.TSB(0x54, AM.DIR),
        inst.STZ(0x02A1, AM.ABS),
        inst.JMP(normal_return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, 0x001E6D, 0x410000)
    # ct_rom.seek(0x35F40C)
    # ct_rom.write(b'\x03\x20')
"""
Module to alter treasure chest text boxes to include the item description.

Mainly useful for gear rando, but this also give KI descriptions.
"""
from typing import Optional
from ctrando.asm import instructions as inst, assemble

from ctrando.common import ctrom, byteops, ctenums
from ctrando.items import itemdata
from ctrando.strings.ctstrings import CTNameString


def write_desc_strings(
    ct_rom: ctrom.CTRom,
    item_db: Optional[itemdata.ItemDB] = None,
    max_desc_len: int = 0x28,
) -> int:
    """
    Write the description strings to rom
    """
    if item_db is None:
        item_db = itemdata.ItemDB.from_rom(ct_rom.getbuffer())
        item_db.update_all_descriptions()

    desc_size = max_desc_len
    total_size = 0x100 * desc_size

    # Hint the size to be in the expanded region.
    start = ct_rom.space_manager.get_free_addr(total_size, 0x410000)

    ct_rom.seek(start)

    valid_item_ids = set(x.value for x in ctenums.ItemID)
    for index in range(0x100):
        if index in valid_item_ids:
            item_id = ctenums.ItemID(index)
            desc_str = item_db[item_id].get_desc_as_str()
            desc = CTNameString.from_string(desc_str, length=desc_size)
            if not desc_str:
                desc[0] = 0xFF
        else:
            # print(f'Error: {index:02X}')
            desc = CTNameString.from_string(f"Item 0x{index:02X}", length=desc_size)

        ct_rom.write(desc, ctrom.freespace.FSWriteType.MARK_USED)

    return start


def add_strlen_func(ct_rom: ctrom.CTRom, max_length: int = 0x28) -> int:
    """Add a string length function to the ctrom to help with descs."""
    AM = inst.AddressingMode

    routine: assemble.ASMList = [
        inst.LDY(0x0000, AM.IMM16),
        "START",
        inst.LDA(0x37, AM.DIR_24_Y),
        inst.CMP(0xEF, AM.IMM8),
        inst.BEQ("END"),
        inst.INY(),
        inst.CPY(max_length, AM.IMM16),
        inst.BCC("START"),
        "END",
        inst.TYA(),
        inst.RTL(),
    ]

    routine_b = assemble.assemble(routine)

    space_man = ct_rom.space_manager
    start = space_man.get_free_addr(len(routine_b), 0x410000)

    ct_rom.seek(start)
    ct_rom.write(routine_b, ctrom.freespace.FSWriteType.MARK_USED)

    return start


def get_desc_char_routine(desc_start: int, desc_size: int) -> assemble.ASMSnippet:
    """
    Get an asm fragment that will handle the special description symbol.
    """


def add_get_desc_char(ct_rom: ctrom.CTRom, desc_start: int, desc_size: int = 0x28):
    """
    Add a character to string handling to fetch a description.
    """

    AM = inst.AddressingMode
    SR = inst.SpecialRegister

    strlen_start = add_strlen_func(ct_rom, desc_size)

    rom_start = byteops.to_rom_ptr(desc_start)
    routine: assemble.ASMList = [
        inst.REP(0x20),
        inst.LDA(0x7F0200, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.SEP(0x20),
        inst.STA(SR.WRMPYA, AM.ABS),
        inst.LDA(desc_size, AM.IMM8),
        inst.STA(SR.WRMPYB, AM.ABS),
        inst.NOP(),
        inst.CLC(),
        inst.REP(0x20),
        inst.LDA(SR.RDMPYL, AM.ABS),
        inst.ADC(rom_start & 0x00FFFF, AM.IMM16),
        inst.STA(0x0237, AM.ABS),  # Memory for start of substring addr
        inst.SEP(0x20),
        inst.LDA(rom_start >> 16, AM.IMM8),
        inst.STA(0x0239, AM.ABS),
        inst.JSL(byteops.to_rom_ptr(strlen_start)),
        inst.STA(0x023A, AM.ABS),
        inst.LDA(0x01, AM.IMM8),
        inst.STA(0x30, AM.DIR),  # 0x000230
        # Copying without truly understanding.
        inst.LDA(0x00, AM.IMM8),
        inst.XBA(),
        inst.JMP(0xC25BF5, AM.LNG),
    ]

    # snippet = assemble.ASMSnippet(routine)
    # print(snippet)
    # input()

    routine_b = assemble.assemble(routine)

    new_start = ct_rom.space_manager.get_free_addr(len(routine_b), hint=0x020000)

    # print(f'{new_start:06X}')

    if new_start >> 16 != 0x02:
        raise ValueError

    ct_rom.seek(new_start)
    ct_rom.write(routine_b, ctrom.freespace.FSWriteType.MARK_USED)

    # We are going to alter unused symbol 0x01
    ctstr_jump_table_st = 0x025903
    ct_rom.seek(ctstr_jump_table_st + 2)
    ct_rom.write(int.to_bytes(new_start & 0xFFFF, 2, "little"))


def ugly_hack_chest_str(ct_rom: ctrom.CTRom):
    """
    Just overwrite the default treasure chest string.
    """
    # orig_string = bytes.fromhex(
    #     '06 EF EF EF EF EF EF EF EF EF EF '
    #     'EF EF EF A6 C8 CD EF D5 EF 1F 02 00'
    # )

    new_string = bytes.fromhex(
        # "{linebreak+3}Got 1 {item}!{linebreak+3}{itemdesc}{null}"
        "06 A6 C8 CD EF D5 EF 1F DE 06 01 00"
    )
    ct_rom.seek(0x1EFF0A)
    ct_rom.write(new_string)


def apply_chest_text_hack(ct_rom: ctrom.CTRom, item_db: Optional[itemdata.ItemDB]):
    """
    Make treasure chests display an item's description.
    """

    max_desc_len = 0x28

    start = write_desc_strings(ct_rom, item_db, max_desc_len)
    add_get_desc_char(ct_rom, start, max_desc_len)
    ugly_hack_chest_str(ct_rom)


def update_desc_str_start(ct_rom: ctrom.CTRom, new_desc_start: int):
    """
    Update an already-patched rom with a new description location.
    This is required because we need to write the routine in a bank-specific place.
    But we don't know where the descs will be until the end of generation.
    """

    new_rom_start = byteops.to_rom_ptr(new_desc_start)
    ctstr_jump_table_st = 0x025903
    ct_rom.seek(ctstr_jump_table_st + 2)

    offset = int.from_bytes(ct_rom.read(2), "little")

    # Compute offset of 0x1A from the routine.  Must be updated if routine changes.
    ct_rom.seek(0x020000 + offset + 0x1A)

    opcode = ct_rom.read(1)[0]
    if opcode != inst.ADC(0, inst.AddressingMode.IMM16).opcode:
        raise ValueError(opcode)

    ct_rom.write(int.to_bytes(new_rom_start & 0xFFFF, 2, "little"))

    ct_rom.seek(0x020000 + offset + 0x22)
    opcode = ct_rom.read(1)[0]
    if opcode != inst.LDA(0, inst.AddressingMode.IMM8).opcode:
        raise ValueError(opcode)
    ct_rom.write(bytes([new_rom_start >> 16]))



def main():
    """main"""
    pass


if __name__ == "__main__":
    main()

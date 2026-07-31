"""Allow items to be gained by setting certain memory."""

from ctrando.asm import instructions as inst, assemble
from ctrando.asm.instructions import AddressingMode as AM

from ctrando.common import asmpatcher, byteops, ctenums, ctrom
from ctrando.strings import ctstrings


def patch_remote_items(
        ct_rom: ctrom.CTRom,
        item_count_addr: int,
        buffer_addr: int
):
    """Add the remote item routine in the location game loop"""

    # C000AD  22 87 1F C0    JSL $C01F87

    rt: assemble.ASMList = [
        inst.PHP(),
        inst.SEP(0x20),
        inst.REP(0x10),
        inst.LDA(buffer_addr+1, AM.LNG),
        inst.BEQ("end"),
        # Deliver the thing
        inst.BIT(0x20, AM.IMM8),
        inst.BEQ("clear_buf"),
        inst.LDA(buffer_addr, AM.LNG),
        inst.TAY(),
        inst.LDA(0x01, AM.IMM8),
        inst.JSL(0xC18003),
        "clear_buf",
        inst.REP(0x20),
        inst.LDA(item_count_addr, AM.LNG),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(item_count_addr, AM.LNG),
        inst.LDA(0x0000, AM.IMM16),
        inst.STA(buffer_addr, AM.LNG),
        "end",
        inst.PLP(),
        # old call
        inst.JSL(0xC01F87, AM.LNG),
        inst.RTL()
    ]

    addr = asmpatcher.add_jsl_routine(rt, ct_rom)
    rom_addr = byteops.to_rom_ptr(addr)
    ct_rom.seek(0x0000AD)
    ct_rom.write(inst.JSL(rom_addr, AM.LNG).to_bytearray())
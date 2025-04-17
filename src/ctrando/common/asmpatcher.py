from typing import Optional

from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.common import (byteops, ctrom, freespace)


def apply_jmp_patch(
        patch: assemble.ASMList,
        hook_addr: int,
        ct_rom: ctrom.CTRom,
        return_addr: Optional[int] = None
):
    """Apply patch at position which jumps and jumps back."""

    routine_b = assemble.assemble(patch)
    routine_addr = ct_rom.space_manager.get_free_addr(len(routine_b))

    hook = [
        inst.JMP(byteops.to_rom_ptr(routine_addr), AM.LNG),
    ]
    hook_b = assemble.assemble(hook)

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_b)
    if return_addr is not None:
        nop_len = return_addr - ct_rom.tell()
        payload = bytes.fromhex('EA'*nop_len)
        ct_rom.write(payload)

    ct_rom.seek(routine_addr)
    ct_rom.write(routine_b, freespace.FSWriteType.MARK_USED)


def add_jsl_routine(
        routine: assemble.ASMList,
        ct_rom: ctrom.CTRom,
        hint: int = 0
) -> int:
    """
    Adds a subroutine which should be called with JSL.
    Returns the file address (not rom) of the routine.
    """

    routine_b = assemble.assemble(routine)
    routine_addr = ct_rom.space_manager.get_free_addr(len(routine_b), hint)
    ct_rom.seek(routine_addr)
    ct_rom.write(routine_b, freespace.FSWriteType.MARK_USED)

    return routine_addr
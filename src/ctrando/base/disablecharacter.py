"""Module for disabling a character in battle"""
from ctrando.common import asmpatcher, byteops, ctenums, ctrom, memory

from ctrando.asm import assemble
from ctrando.asm import instructions as inst
from ctrando.asm.instructions import AddressingMode as AM

# FDB26C  BD 80 29       LDA $2980,X
# FDB26F  30 09          BMI $FDB27A
# FDB271  9D FF AE       STA $AEFF,X

def lock_characters(
        ct_rom: ctrom.CTRom,
):
    hook_addr = 0x3Db26C
    remove_return_rom_addr = 0xFDB27A
    normal_return_rom_addr = 0xFDB271

    stat_offset_rom_start = 0xFDA83B
    weapon_offset = 0x0029
    remove_weapon_id = ctenums.ItemID.PACIFIST
    pc_id_copy_addr_abs = memory.Memory.COPY_PC_1 & 0xFFFF
    rt: assemble.ASMList = [
        inst.TDC(),
        inst.LDA(0x2980, AM.ABS_X),
        inst.BMI("missing_char"),
        inst.ASL(mode=AM.NO_ARG),
        inst.PHX(),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(stat_offset_rom_start, AM.LNG_X),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(weapon_offset, AM.ABS_X),
        inst.CMP(remove_weapon_id, AM.IMM8),
        inst.BEQ("remove_jump"),
        inst.PLX(),
        inst.LDA(0x2980, AM.ABS_X),
        inst.STA(pc_id_copy_addr_abs, AM.ABS_X),
        inst.JMP(normal_return_rom_addr, AM.LNG),
        "remove_jump",
        inst.PLX(),
        "missing_char",
        inst.LDA(0x2980, AM.ABS_X),
        inst.ORA(0x80, AM.IMM8),
        inst.STA(pc_id_copy_addr_abs, AM.ABS_X),
        inst.JMP(remove_return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, hint=0x410000)

    # C1FB18  BD 80 29       LDA $2980,X
    # CCE5FB  BD 80 29       LDA $2980,X
    # CCE8D9  BD 80 29       LDA $2980,X
    # CCE980  B9 80 29       LDA $2980,Y
    # CCE986  79 80 29       ADC $2980,Y
    # Maybe not needed
    # C14A40  B9 80 29       LDA $2980,Y
    # C143F4  BD 80 29       LDA $2980,X
    # After Battle
    # CFFC77  BD 80 29       LDA $2980,X
    # C1B446  BD 80 29       LDA $2980,X

    addrs = (
        0x01FB18, 0x0CE5FB, 0x0CE8D9, 0x0CE980, 0x0CE986,
        # Maybe not needed (only after battle active)
        0x014A40, 0x0143F4,
        # After battle
        0x0FFC77,
        0x01B446,  # Seems to only trigger when losing a battle without game over

    )

    for addr in addrs:
        ct_rom.seek(addr+1)
        ct_rom.write(pc_id_copy_addr_abs.to_bytes(2, "little"))
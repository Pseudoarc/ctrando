"""Module for working with Weapon/Armor Effects"""
from collections.abc import Sequence
from io import BytesIO

from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.common import byteops, cttypes as cty, ctrom
from ctrando.common.freespace import FSWriteType


class EffectMod(cty.SizedBinaryData):
    SIZE = 3
    ROM_RW = cty.AbsPointerRW(0x01EB3E) # C1EB3D  BF 05 2A CC    LDA $CC2A05,X

_vanilla_effect_start = 0x0C2A05
_vanilla_effect_count = 0x39
_max_vanilla_routine_index = 0x42

_current_damage_offset = 0xAD89


def gather_vanilla_effects(ct_rom: ctrom.CTRom) -> list[EffectMod]:
    effects = [
        EffectMod.read_from_ctrom(ct_rom, ind) for ind in range(_vanilla_effect_count)
    ]

    return effects


def gather_new_effects_and_rts() -> list[tuple[EffectMod, assemble.ASMList]]:
    routines = [
        get_venus_bow_rt()
    ]

    effects = [
        EffectMod(bytes([_max_vanilla_routine_index+1, 0, 0]))
    ]

    return effects, routines


def expand_effect_mods(
        ct_rom: ctrom.CTRom,
):
    """
    Allow more effects.

    Notes
    -----
    You can't move everything to a new bank because there are too many bank $C1-local
    subroutines.  Effect data itself will move to another spot, but a different
    pointer table (different bank) is used for the new effects.
    """

    effects = gather_vanilla_effects(ct_rom)
    additional_effects, additional_effect_routines = gather_new_effects_and_rts()

    effects += additional_effects


    # 1) If the effects need more space on the rom, write them elsewhere and
    #    update the pointers.
    if len(effects) > _vanilla_effect_count:
        # Can't free old effects until armor references are updated
        # ct_rom.space_manager.mark_block(
        #     (_vanilla_effect_start, _vanilla_effect_start+EffectMod.SIZE*_vanilla_effect_count),
        #     FSWriteType.MARK_FREE
        # )

        new_size = len(effects)*EffectMod.SIZE
        new_start = ct_rom.space_manager.get_free_addr(
            new_size, 0x410000
        )

        payload = b''.join(x for x in effects)
        ct_rom.seek(new_start)
        ct_rom.write(payload, FSWriteType.MARK_USED)

        addr_offset_dict: dict[int, int] = {
            # Weapon effects
            0x01EB2E: 1,
            0x01EB36: 2,
            0x01EB3E: 0,
            # Armor effects -- later
            # 0x3DB608,

        }

        rom_addr = byteops.to_rom_ptr(new_start)
        for addr, offset in addr_offset_dict.items():
            ct_rom.seek(addr)
            ct_rom.write(int.to_bytes(rom_addr+offset, 3, "little"))


    # C1EB3D  BF 05 2A CC    LDA $CC2A05,X
    # ----- Replace these four bytes
    # C1EB41  85 20          STA $20
    # C1EB43  0A             ASL
    # C1EB44  AA             TAX
    # -----
    # C1EB45  FC 61 FA       JSR ($FA61,X)
    # C1EB48  60             RTS
    hook_addr = 0x01EB41

    # 2) Collect the new effect routines
    effect_rts: list[bytes] = [
        assemble.assemble(routine) for routine in additional_effect_routines
    ]

    # 3) Allocate space for new routines
    effect_rt_lens: list[int] = [len(routine_b) for routine_b in effect_rts]

    def make_bank_switch_rt(ptr_table_rom_st: int):
        # Enter with 8-bit A, 16-bit X/Y
        effect_switch_rt: assemble.ASMList = [
            # Replace hook bytes
            inst.STA(0x20, AM.DIR),
            inst.CMP(_max_vanilla_routine_index + 1, AM.IMM8),
            inst.BCS("new_bank"),
            inst.ASL(mode=AM.NO_ARG),
            inst.TAX(),
            inst.JMP(0xC1EB45, AM.LNG),  # Back to vanilla JSR
            "new_bank",
            inst.SEC(),
            inst.SBC(_max_vanilla_routine_index+1, AM.IMM8),
            inst.ASL(mode=AM.NO_ARG),
            inst.TAX(),
            inst.JSR(ptr_table_rom_st & 0xFFFF, AM.ABS_X_16),
            inst.JMP(0xC1EB48, AM.LNG)  # To vanilla RTS
        ]
        return effect_switch_rt

    dummy_rt = make_bank_switch_rt(0)
    bank_switch_rt_size = len(assemble.assemble(dummy_rt))
    total_size = sum(effect_rt_lens) + 2 * len(effect_rts) + bank_switch_rt_size

    payload_addr = ct_rom.space_manager.get_free_addr(total_size, 0x410000)

    # 4) Write out the new routines
    real_bank_switch_rt = make_bank_switch_rt(byteops.to_rom_ptr(payload_addr))
    real_bank_switch_rt_b = assemble.assemble(real_bank_switch_rt)

    if additional_effect_routines:
        first_ptr = (payload_addr + len(additional_effects) * 2) & 0xFFFF
        rt_b = b''.join(rt for rt in effect_rts)
        ptrs = [first_ptr]
        for length in effect_rt_lens[:-1]:
            ptrs.append(ptrs[-1] + length)

        ptr_b = b''.join(int.to_bytes(ptr, 2, "little")
                         for ptr in ptrs)
    else:
        rt_b = ptr_b = b''

    payload = ptr_b + rt_b + real_bank_switch_rt_b
    if len(payload) != total_size:
        print(len(payload), total_size, len(real_bank_switch_rt_b))
        raise ValueError


    bank_switch_addr = payload_addr + len(rt_b) + len(ptr_b)
    bank_switch_addr = byteops.to_rom_ptr(bank_switch_addr)
    hook: assemble.ASMList = [inst.JMP(byteops.to_rom_ptr(bank_switch_addr), AM.LNG)]
    hook_b = assemble.assemble(hook)

    ct_rom.seek(payload_addr)
    ct_rom.write(payload, FSWriteType.MARK_USED)

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_b)


def get_venus_bow_rt() -> assemble.ASMList:
    rt: assemble.ASMList = [
        inst.LDX(777, AM.IMM16),
        inst.STX(_current_damage_offset, AM.ABS),
        inst.RTS()
    ]

    return rt







if __name__ == "__main__":
    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")

    start = EffectMod.ROM_RW.get_data_start_from_ctrom(ct_rom)
    print(f"{start:06X}")
    input()
    for ind in range(_vanilla_effect_count):
        effect = EffectMod.read_from_ctrom(ct_rom, ind)
        print(f"{ind:02X}: {effect}")

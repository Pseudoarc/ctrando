"""
Module for producing assmembly that can compute the desired level of enemies.

- A scaling function is responsible for writing the desired enemy level to
  memory.Memory.SCALING_LEVEL.
- On entry, the scaling function will have:
   - an 8-bit A and 16-bit X and Y,
   - Zero values for A, X, and Y
   - A data bank register of 0x7E,
   - A direct page register of 0x0000
   If these values are changed, they must be restored prior to returning.
- Do not assume that player data is in its usual place for battle.
- The debugger shows that [$34, $45) should be free for temp values.
"""
from typing import Optional

from ctrando.arguments import enemyscaling
from ctrando.asm import assemble
from ctrando.asm import instructions as inst
from ctrando.asm.instructions import AddressingMode as AM, SpecialRegister as SR
from ctrando.common import memory

# Notes:
#  - 0x01FDFB can be called as a long subroutine for the multiplication.
#    - Does not play nicely with X
#  - There is no long call to the division subroutine, but we can add one.

_jsl_mult_addr = 0xC1FDBF


def get_progression_scaler_from_opts(
        scaler_options: enemyscaling.ProgressionScalingData,
        slow_mult_rom_addr: int,
) -> assemble.ASMList:
    return get_progression_scaler(
        scaler_options.levels_per_character,
        scaler_options.levels_per_boss,
        scaler_options.levels_per_quest,
        scaler_options.levels_per_objective,
        scaler_options.levels_per_key_item,
        slow_mult_rom_addr
    )


def get_progression_scaler(
        levels_per_char: float,
        levels_per_boss: float,
        levels_per_quest: float,
        levels_per_objective: float,
        levels_per_key_item: float,
        slow_mult_rom_addr: int
) -> assemble.ASMList:
    """
    Scale based on what the player has done.
    """

    temp_addr = 0x34
    levels_per_char = min(63, levels_per_char)
    levels_per_boss = min(63, levels_per_boss)
    levels_per_quest = min(63, levels_per_quest)
    levels_per_objective = min(63, levels_per_objective)
    levels_per_key_item = min(63, levels_per_key_item)

    def make_value_block(
            levels_per_value_4x: int,
            value_addr: int
    ) -> assemble.ASMList:

        return [
            inst.REP(0x20),
            inst.LDA(levels_per_value_4x, AM.IMM16),
            inst.STA(0x28, AM.DIR),
            inst.LDA(value_addr, AM.LNG),
            inst.AND(0x00FF, AM.IMM16),
            inst.STA(0x2A, AM.DIR),
            inst.JSL(slow_mult_rom_addr, AM.LNG),
            inst.REP(0x20),
            inst.LDA(0x2C, AM.DIR),
            inst.LSR(mode=AM.NO_ARG),
            inst.LSR(mode=AM.NO_ARG),
            inst.CMP(0x00FF, AM.IMM16),
            inst.BCC(f"end_{value_addr}"),
            inst.LDA(0x00FF, AM.IMM16),
            f"end_{value_addr}",
            inst.SEP(0x20)
        ]

        # return [
        #     inst.LDA(levels_per_value_4x, AM.IMM8),
        #     inst.STA(SR.M7A, AM.LNG),
        #     inst.LDA(0x00, AM.IMM8),
        #     inst.STA(SR.M7A, AM.LNG),
        #     inst.LDA(value_addr, AM.LNG),
        #     inst.STA(SR.M7B, AM.LNG),
        #     inst.REP(0x20),
        #     inst.LDA(SR.MPYL, AM.LNG),
        #     inst.LSR(mode=AM.NO_ARG),
        #     inst.LSR(mode=AM.NO_ARG),
        #     inst.CMP(0x00FF, AM.IMM16),
        #     inst.BCC(f"end_{value_addr}"),
        #     inst.LDA(0x00FF, AM.IMM16),
        #     f"end_{value_addr}",
        #     inst.SEP(0x20)
        # ]

    routine: assemble.ASMList = [
        inst.SEP(0x20),
        inst.STZ(temp_addr, AM.DIR)
    ]

    vals = [levels_per_char, levels_per_boss, levels_per_quest,
            levels_per_objective, levels_per_key_item]
    addrs = [memory.Memory.RECRUITS_OBTAINED,
             memory.Memory.BOSSES_DEFEATED,
             memory.Memory.QUESTS_COMPLETED,
             memory.Memory.OBJECTIVES_COMPLETED,
             memory.Memory.KEY_ITEMS_OBTAINED]

    for value, addr in zip(vals, addrs):
        if value <= 0:
            continue

        routine += make_value_block(round(value*4), addr)
        label = f"block_{value}_{addr}"
        routine += [
            inst.CLC(),
            inst.ADC(temp_addr, AM.DIR),
            inst.BCC(label),
            inst.LDA(0x7F, AM.IMM8),
            inst.STA(temp_addr, AM.DIR),
            inst.BRL("end"),
            label,
            inst.STA(temp_addr, AM.DIR)
        ]

    routine += [
        inst.LDA(temp_addr, AM.DIR),
        inst.CMP(0x7F, AM.IMM8),
        inst.BCC("end"),
        inst.LDA(0x7F, AM.IMM8),
        "end",
        inst.STA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS)
    ]

    return routine


def get_max_party_level_scaler() -> assemble.ASMList:
    """
    Returns an ASMList which computes the max pc level and uses that as the
    scale factor.
    """

    level_offset = 0x12
    cur_max_addr = 0x34
    # num_pcs_addr = 0x35

    mult_1_addr = 0x28
    mult_2_addr = 0x2A
    mult_product_addr = 0x2C

    routine = [
        inst.PHX(),
        inst.PHY(),
        inst.STA(cur_max_addr, AM.DIR),
        # inst.STA(num_pcs_addr, AM.DIR),
        "loop_st",
        inst.LDA(memory.Memory.ACTIVE_PC1 & 0xFFFF, AM.ABS_Y),
        inst.BMI("increment_loop"),
        inst.PHA(),
        inst.LDA(0x50, AM.IMM8),
        inst.STA(SR.M7A, AM.LNG),
        inst.TDC(),
        inst.STA(SR.M7A, AM.LNG),
        inst.PLA(),
        inst.STA(SR.M7B, AM.LNG),
        inst.REP(0x20),
        inst.LDA(SR.MPYL, AM.LNG),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(0x2600+level_offset, AM.ABS_X),
        inst.CMP(cur_max_addr, AM.DIR),
        inst.BMI("increment_loop"),
        inst.STA(cur_max_addr, AM.DIR),
        "increment_loop",
        inst.INY(),
        inst.CPY(0x03, AM.IMM16),
        inst.BMI("loop_st"),
        inst.LDA(cur_max_addr, AM.DIR),
        inst.STA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.PLY(),
        inst.PLX(),
    ]

    return routine


def get_affine_scale_values_routine(
        constant_part: int,
        label_prefix: str = ""  # Needed for having multiple of these not conflict
) -> assemble.ASMList:
    """
    Scale using ax+b as a scale function.  Normalized to x+b.
    """
    routine = [
        inst.LDA(memory.Memory.ORIGINAL_LEVEL_TEMP, AM.LNG),
        inst.CLC(),
        inst.ADC(constant_part, AM.IMM8),
        inst.BCC(f"{label_prefix}write1"),
        inst.LDA(0xFF, AM.IMM8),
        f"{label_prefix}write1",
        inst.STA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.CLC(),
        inst.ADC(constant_part, AM.IMM8),
        inst.BCC(f"{label_prefix}write2"),
        inst.LDA(0xFF, AM.IMM8),
        f"{label_prefix}write2",
        inst.STA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
    ]

    assemble.assemble(routine)

    return routine


def get_slow_scale8_routine(
        slow_mult_long_rom_addr: int,
        slow_div_long_rom_addr: int,
        return_long: bool = True
) -> assemble.ASMList:
    """
    Returns a scale8 routine which does not use the special registers.
    This is, unfortunately, necessary for any scaling that happens during a battle
    such as AI commands or reward granting.

    Assumes:
      - Value to scale is in A
      - FROM_SCALE in memory.Memory.FROM_SCALE_TEMP
      - TO_SCALE in memory.Memory.TO_SCALE_TEMP
      - Returns with A*(TO_SCALE)/(FROM_SCALE) in A
    """
    if return_long:
        return_cmd = inst.RTL()
    else:
        return_cmd = inst.RTS()

    # Note: These are low enough that it doesn't matter whether the bank is
    #       00 or 7E.  In either case, absolute addressing will get the right spot
    #       because of mirroring.
    factor1_lo, factor2_lo = 0x28, 0x2A  # 16-bit
    product_lo = 0x2C  # 32-bit
    dividend_lo, divisor_lo = 0x28, 0x2A  # 16-bit
    quotient_lo = 0x2C  # 16-bit
    # remainder_low = 0x32 # 16-bit

    # Not sure if we can rely on direct page.
    routine = assemble.ASMList = [
        inst.PHP(),
        inst.PHA(),
        inst.LDA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.CMP(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.BNE("do_scaling"),
        inst.PLA(),
        inst.PLP(),
        return_cmd,
        "do_scaling",
        inst.STA(factor1_lo, AM.ABS),
        inst.STZ(factor1_lo+1, AM.ABS),
        inst.PLA(),
        inst.STA(factor2_lo, AM.ABS),
        inst.STZ(factor2_lo+1, AM.ABS),
        inst.PHX(),
        inst.JSL(slow_mult_long_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(product_lo, AM.ABS),
        inst.STA(dividend_lo, AM.ABS),
        inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.STA(divisor_lo, AM.ABS),
        inst.JSL(slow_div_long_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(quotient_lo, AM.ABS),
        inst.CMP(0x100, AM.IMM16),
        inst.BCC("s8end"),
        inst.LDA(0x00FF, AM.IMM16),
        "s8end",
        inst.PLX(),
        inst.PLP(),
        return_cmd
    ]

    return routine


def get_scale8_routine(
        return_long: bool = True
) -> assemble.ASMList:
    """
    Scales the value in A by (memory.Memory.SCALING_LEVEL/memory.Memory.FROM_LEVEL_TEMP)
    """

    if return_long:
        return_cmd = inst.RTL()
    else:
        return_cmd = inst.RTS()

    routine: assemble.ASMList = [
        inst.PHP(),
        inst.STA(SR.WRMPYA, AM.LNG),
        inst.PHA(),
        inst.LDA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.CMP(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.BNE("do_scaling"),
        inst.PLA(),
        inst.PLP(),
        return_cmd,
        "do_scaling",
        inst.STA(SR.WRMPYB, AM.LNG),
    ] + [inst.NOP()]*2 + [
        inst.PLA(),
        inst.LDA(SR.RDMPYL, AM.LNG),
        inst.STA(SR.WRDIVL, AM.LNG),
        inst.LDA(SR.RDMPYH, AM.LNG),
        inst.STA(SR.WRDIVH, AM.LNG),
        inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.STA(SR.WRDIVB, AM.LNG)
    ] + [inst.NOP()]*8 + [
        inst.REP(0x20),
        inst.LDA(SR.RDDIVL, AM.LNG),
        inst.CMP(0x100, AM.IMM16),
        inst.BCC("s8end"),
        inst.LDA(0x00FF, AM.IMM16),
        "s8end",
        inst.PLP(),
        return_cmd
    ]

    return routine

# Note:  The slow mult routines assume 16-bit X and will zero out X.
#        So save those values if needed.
def get_slow_scale16_routine(
        slow_mult_long_rom_addr: int,
        slow_div_long_rom_addr: int,
        return_long: bool = True
) -> assemble.ASMList:
    """
    Returns a scale16 routine which does not use the special registers.
    This is, unfortunately, necessary for any scaling that happens during a battle
    such as AI commands or reward granting.

    Assumes:
      - Value to scale is in A (16-bit)
      - FROM_SCALE in memory.Memory.FROM_SCALE_TEMP
      - TO_SCALE in memory.Memory.TO_SCALE_TEMP
      - Returns with A*(TO_SCALE)/(FROM_SCALE) in A
    """
    if return_long:
        return_cmd = inst.RTL()
    else:
        return_cmd = inst.RTS()

    # Note: These are low enough that it doesn't matter whether the bank is
    #       00 or 7E.  In either case, absolute addressing will get the right spot
    #       because of mirroring.
    factor1_lo, factor2_lo = 0x28, 0x2A  # 16-bit
    product_lo = 0x2C  # 32-bit
    dividend_lo, divisor_lo = 0x28, 0x2A  # 16-bit
    quotient_lo = 0x2C  # 16-bit
    remainder_lo = 0x32  # 16-bit

    routine: assemble.ASMList = [
        inst.PHA(),
        inst.SEP(0x20),
        inst.LDA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.CMP(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.BNE("do_scaling"),
        inst.REP(0x20),
        inst.PLA(),
        return_cmd,
        "do_scaling",
        inst.STA(factor1_lo, AM.ABS),
        inst.STZ(factor1_lo+1, AM.ABS),
        inst.REP(0x20),
        inst.PLA(),
        inst.STA(factor2_lo, AM.ABS),
        inst.PHX(),
        inst.JSL(slow_mult_long_rom_addr),
        inst.REP(0x20),
        inst.LDA(product_lo, AM.ABS),
        inst.STA(dividend_lo, AM.ABS),
        inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.STA(divisor_lo, AM.ABS),
        inst.JSL(slow_div_long_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(quotient_lo, AM.ABS),
        ### replacing
        # inst.LDA(product_lo, AM.ABS),
        # inst.AND(0x00FF, AM.IMM16),
        # inst.STA(0x30, AM.ABS),  # Store the lo byte for later.
        # inst.LDA(product_lo+1, AM.ABS),  # Get HH MM
        # inst.STA(dividend_lo, AM.ABS),
        # inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        # inst.AND(0x00FF, AM.IMM16),
        # inst.STA(divisor_lo, AM.ABS),
        # inst.JSL(slow_div_long_rom_addr),  # Compute HHMM/FROM_SCALE
        # inst.REP(0x20),
        # inst.LDA(remainder_lo, AM.ABS),
        # inst.XBA(),
        # inst.CLC(),
        # inst.ADC(0x30, AM.ABS),
        # inst.STA(dividend_lo, AM.ABS),
        # inst.LDA(quotient_lo, AM.ABS),
        # inst.CMP(0x100, AM.IMM16),
        # inst.BCS("max_value"),
        # inst.XBA(),
        # inst.STA(0x30, AM.ABS),
        # inst.JSL(slow_div_long_rom_addr),
        # inst.REP(0x20),
        # inst.LDA(quotient_lo, AM.ABS),
        # inst.CLC(),
        # inst.ADC(0x30, AM.ABS),
        # inst.BCC("end"),
        # "max_value",
        # inst.LDA(0xFFFF, AM.IMM16),
        # "end",
        inst.PLX(),
        return_cmd
    ]

    return routine

def get_scale16_routine(
        return_long: bool = True,
) -> assemble.ASMList:
    """
    With 16-bit A, scale the 16-bit value in A using pre-computed scale factors
    """

    if return_long:
        return_cmd = inst.RTL()
    else:
        return_cmd = inst.RTS()

    temp_addr = 0x28
    routine = [
        inst.PHA(),
        inst.SEP(0x20),
        inst.STA(SR.WRMPYA, AM.LNG),
        inst.LDA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.CMP(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.BNE("do_scaling"),
        inst.REP(0x20),
        inst.PLA(),
        return_cmd,
        "do_scaling",
        inst.STA(SR.WRMPYB, AM.LNG)
    ] + [inst.NOP()]*4 + [
        inst.REP(0x20),
        inst.STZ(temp_addr, AM.DIR),
        inst.STZ(temp_addr+2, AM.DIR),  # These should be enough to avoid NOPs
        inst.LDA(SR.RDMPYL, AM.LNG),
        inst.STA(temp_addr, AM.DIR),
        inst.PLA(),
        inst.SEP(0x20),
        inst.XBA(),
        inst.STA(SR.WRMPYA, AM.LNG),
        inst.LDA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.STA(SR.WRMPYB, AM.LNG)
    ] + [inst.NOP()]*4 + [
        inst.REP(0x20),
        inst.LDA(SR.RDMPYL, AM.LNG),
        inst.CLC(),
        inst.ADC(temp_addr+1, AM.DIR),
        # Now Divide
        inst.STA(SR.WRDIVL, AM.LNG),
        inst.SEP(0x20),
        inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.STA(SR.WRDIVB, AM.LNG),
    ] + [inst.NOP()]*8 + [
        inst.REP(0x20),
        inst.LDA(SR.RDDIVL, AM.LNG),
        inst.BIT(0xFF00, AM.IMM16),
        inst.BNE("max_val"),
        inst.STA(temp_addr+1, AM.DIR),
        inst.LDA(SR.RDMPYL, AM.LNG),  # actually remainder
        inst.XBA(),
        inst.SEP(0x20),
        inst.LDA(temp_addr, AM.DIR),
        inst.REP(0x20),
        inst.STA(SR.WRDIVL, AM.LNG),
        inst.SEP(0x20),
        inst.LDA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.STA(SR.WRDIVB, AM.LNG),
    ] + [inst.NOP()]*8 + [
        inst.STZ(temp_addr, AM.DIR),
        inst.REP(0x20),
        inst.LDA(temp_addr, AM.DIR),
        inst.CLC(),
        inst.ADC(SR.RDDIVL, AM.LNG),
        inst.BCS("max_val"),
        inst.CMP(0xFFFF, AM.IMM16),
        inst.BPL("end"),
        "max_val",
        inst.LDA(0xFFFF, AM.IMM16),
        "end",
        return_cmd
    ]

    return routine


def get_scale_def_routine(
        normal_def_level: int,
        full_def_level: int,
        scale8_rom_addr: int
) -> assemble.ASMList:
    """
    Get a routine that scales defense values.  Almost everyone has a defense
    value of 0x7F (approximately 50% reduction).  This routine is targeted at
    enemies whose defense is so high that they are impossible to damage without
    magic, sometimes specific magic (e.g. Nizbel, Retinite).
    Assumes:
    - Enemy level in memory.Memory.ORIGINAL_LEVEL_TEMP (unused?)
    - Scaling level in memory.Memory.SCALING_LEVEL
    - Unscaled defense value in 8-bit A
    If unscaled defense <= 0x7F, leave the value alone.
    If scaling level <= normal_def_level, set the defense to 0x7F.
    If scaling level >= full_def_level, leave the value in A alone.
    Otherwise, let x = orig def - 0x7F and return 0x7F + x*scaling_lv/full_def_lv
    """

    routine: assemble.ASMList = [
        inst.CMP(0x80, AM.IMM8),
        inst.BCS("def_ge_80"),
        inst.RTL(),
        "def_ge_80",
        inst.PHA(),
        inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.CMP(normal_def_level+1, AM.IMM8),
        inst.BCS("allow_def_gt_7F"),
        inst.PLA(),
        inst.LDA(0x7F, AM.IMM8),
        inst.RTL(),
        "allow_def_gt_7F",
        inst.CMP(full_def_level, AM.IMM8),
        inst.BCC("scale_def"),
        inst.PLA(),
        inst.RTL(),
        "scale_def",
        inst.STA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.LDA(full_def_level, AM.IMM8),
        inst.STA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.PLA(),
        inst.SEC(),
        inst.SBC(0x7F, AM.IMM8),
        inst.JSL(scale8_rom_addr, AM.LNG),
        inst.CLC(),
        inst.ADC(0x7F, AM.IMM8),
        inst.RTL()
    ]

    return routine

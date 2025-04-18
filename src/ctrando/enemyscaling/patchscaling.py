"""Patch a ctrom to use a scaling scheme."""
import typing
from typing import Optional

from ctrando.arguments import enemyscaling
from ctrando.locations import scriptmanager
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.asm import instructions as inst, assemble
from ctrando.asm.instructions import AddressingMode as AM  #, SpecialRegister as SR
from ctrando.common import asmpatcher, byteops, ctenums, ctrom, memory
from ctrando.enemydata.enemystats import EnemyStats
from ctrando.enemyscaling import scalingschemes

_mag_affine_constant = 0
_atk_affine_constant = 2
_hit_affine_constant = 9
_evd_affine_constant = 0x13


def patch_pre_battle_level_setting(
        ct_rom: ctrom.CTRom,
        scaling_scheme: assemble.ASMList,
):
    """
    Insert the scaling scheme into the battle code prior to enemy stat loads.
    """

    # C1FAA3  7B             TDC
    # C1FAA4  AA             TAX
    # C1FAA5  A8             TAY
    # C1FAA6  86 02          STX $02      <-- Hook here (+ next line)
    # C1FAA8  86 04          STX $04
    # C1FAAA  A6 02          LDX $02      <-- Temp variable for enemy slot
    # C1FAAC  22 38 B4 FD    JSL $FDB438  <-- The enemy stat reading routine

    hook_addr = 0x01FAA6
    return_addr = 0x01FAAA

    scale_writer = [
        inst.STX(0x02, AM.DIR),
        inst.STX(0x04, AM.DIR),
    ] + scaling_scheme + [
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(scale_writer, hook_addr, ct_rom, return_addr)


def patch_scaling_inventory(
        ct_rom: ctrom.CTRom,
        script_manager: scriptmanager.ScriptManager,
        set_scale_rom_addr: int,
):
    """
    Update the scaling level in the inventory when the menu is opened
    """

    script = script_manager[ctenums.LocID.LOAD_SCREEN]
    pos = script.get_function_start(1, FID.ACTIVATE)
    script.insert_commands(EC.add_item(ctenums.ItemID.SCALING_LEVEL).to_bytearray(), pos)

    # There's already a routine at 0x029988 that cleans up the inventory.
    # We'll piggyback onto that

    hook_addr = 0x029988
    return_addr = 0x0299B1

    routine: assemble.ASMList = [
        inst.PHP(),
        inst.SEP(0x20),  # Scaling schemes expect 8-bit A and 16-bit index
        inst.REP(0x10),
        inst.JSL(set_scale_rom_addr, AM.LNG),
        # Mostly copy old routine
        inst.SEP(0x30),
        inst.LDX(0x00, AM.IMM8),
        "loop_st",
        inst.LDA(0x2500, AM.ABS_X),
        inst.BEQ("zero"),
        inst.LDA(0x2400, AM.ABS_X),
        inst.BEQ("zero"),
        inst.CMP(ctenums.ItemID.WEAPON_END_5A, AM.IMM8),
        inst.BEQ("zero"),
        inst.CMP(ctenums.ItemID.ARMOR_END_7B, AM.IMM8),
        inst.BEQ("zero"),
        inst.CMP(ctenums.ItemID.HELM_END_94, AM.IMM8),
        inst.BEQ("zero"),
        inst.CMP(0xF2, AM.IMM8),
        inst.BCS("zero"),
        inst.CMP(ctenums.ItemID.SCALING_LEVEL, AM.IMM8),
        inst.BNE("next"),
        inst.LDA(memory.Memory.SCALING_LEVEL & 0x00FFFF, AM.ABS),
        inst.STA(0x2500, AM.ABS_X),
        inst.BRA("next"),
        "zero",
        inst.STZ(0x2400, AM.ABS_X),
        inst.STZ(0x2500, AM.ABS_X),
        "next",
        inst.INX(),
        inst.BNE("loop_st"),
        inst.PLP(),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(routine, hook_addr, ct_rom, return_addr)

def patch_enemy_rewards(
        ct_rom: ctrom.CTRom,
        scaling_exclusion_list: Optional[list[ctenums.EnemyID,]] = None,
        scale_8_addr: Optional[int] = None,
        scale_16_addr: Optional[int] = None
):
    """Interrupt the reward loading routine to do scaling."""

    # Original reward routine.
    # FDABD2  C2 20          REP #$20
    # FDABD4  A6 06          LDX $06
    # FDABD6  BF 00 5E CC    LDA $CC5E00,X
    # FDABDA  18             CLC
    # FDABDB  6D 8C B2       ADC $B28C
    # FDABDE  8D 8C B2       STA $B28C
    # FDABE1  BF 02 5E CC    LDA $CC5E02,X
    # FDABE5  18             CLC
    # FDABE6  6D A5 B2       ADC $B2A5
    # FDABE9  8D A5 B2       STA $B2A5
    # FDABEC  7B             TDC
    # FDABED  E2 20          SEP #$20
    # FDABEF  BF 06 5E CC    LDA $CC5E06,X
    # FDABF3  C2 20          REP #$20
    # FDABF5  18             CLC
    # FDABF6  6D DB B2       ADC $B2DB
    # FDABF9  90 07          BCC $FDAC02
    # FDABFB  E2 20          SEP #$20
    # FDABFD  EE DD B2       INC $B2DD
    # FDAC00  C2 20          REP #$20
    # FDAC02  8D DB B2       STA $B2DB
    # FDAC05  7B             TDC
    # FDAC06  E2 20          SEP #$20
    # FDAC08  BF 04 5E CC    LDA $CC5E04,X

    if scaling_exclusion_list is None:
        scaling_exclusion_list = []

    if scale_16_addr is None:
        scale_16_rt = scalingschemes.get_scale16_routine(True)
        scale_16_rt_b = assemble.assemble(scale_16_rt)

        scale_16_addr = ct_rom.space_manager.get_free_addr(len(scale_16_rt_b))
        ct_rom.seek(scale_16_addr)
        ct_rom.write(scale_16_rt_b, ctrom.freespace.FSWriteType.MARK_USED)

    scale_16_rom_addr = byteops.to_rom_ptr(scale_16_addr)

    if scale_8_addr is None:
        scale_8_rt = scalingschemes.get_scale8_routine(True)
        scale_8_rt_b = assemble.assemble(scale_8_rt)

        scale_8_addr = ct_rom.space_manager.get_free_addr(len(scale_8_rt_b))
        ct_rom.seek(scale_8_addr)
        ct_rom.write(scale_8_rt_b, ctrom.freespace.FSWriteType.MARK_USED)

    scale_8_rom_addr = byteops.to_rom_ptr(scale_8_addr)

    #                      --------sub start--------
    # FDABA2  7B             TDC
    # FDABA3  A6 0E          LDX $0E
    #  - Appears to be enemy slot value.
    # FDABA5  BD 12 AF       LDA $AF12,X
    #  - Not sure about this line.  Since X >= 3 we're targeting 7EAF15 at least
    #    and there's nothing in the DB about these bytes.
    #  - I thought it was related to enemies that spawn mid-battle (bantam imp)
    #    but looks like that's unrelated.
    # FDABA8  89 40          BIT #$40
    # FDABAA  F0 03          BEQ $FDABAF
    # FDABAC  4C 6D AC       JMP $AC6D      # Jumping to RTL
    # FDABAF  BD 0A AF       LDA $AF0A,X    # Loading the enemy's index.
    # FDABB2  C9 FF          CMP #$FF
    # FDABB4  D0 03          BNE $FDABB9
    # FDABB6  4C 6D AC       JMP $AC6D      # Jumping to RTL
    # --- This looks like where I want to jump in ---
    # FDABB9  AA             TAX
    hook_rom_addr = 0xFDABB9
    # We have the enemy's index in A.  We need to load the original level
    # and put that into the temp scaling variables

    stat_rom_start = 0xCC4700
    # 8-bit A, 16-bit X, DB = 0x7E
    store_original_level_rt: assemble.ASMList = [
        inst.LDA(0x0E, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(0xFDA80B, AM.LNG_X),
        inst.TAX(),
        inst.TDC(),
        inst.SEP(0x20),
        inst.LDA(0x0001, AM.ABS_X),
        inst.STA(memory.Memory.ORIGINAL_LEVEL_TEMP & 0xFFFF, AM.ABS),
        # inst.STA(memory.Memory.FROM_SCALE_TEMP & 0xFFFF, AM.ABS),
        # inst.LDA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS),
        # inst.STA(memory.Memory.TO_SCALE_TEMP & 0xFFFF, AM.ABS),
    ]
    store_original_level_rt += scalingschemes.get_affine_scale_values_routine(2, 'rew')

    get_reward_addr_rt: assemble.ASMList = [
        # Original routine copies the slot to $04.  Used later.
        inst.LDA(0x0E, AM.DIR),
        inst.SEC(),
        inst.SBC(0x03, AM.IMM8),
        inst.TAX(),
        inst.STX(0x04, AM.DIR),
        # end copy of original
        inst.LDX(0x0E, AM.DIR),
        inst.LDA(0xAF0A, AM.ABS_X),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.TDC(),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.LDA(0x07, AM.IMM8),  # Length of reward data
        # inst.STA(SR.M7B, AM.LNG),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.LNG),
        # Alternate without Mode 7 registers
        inst.REP(0x20),
        inst.AND(0x00FF, AM.IMM16),
        inst.PHA(),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.SEC(),
        inst.SBC(1, AM.STK),
        # End Alternate
        inst.TAX(),
        inst.PLA(),
    ]

    reward_rom_st = 0xCC5E00
    battle_xp_offset = 0xB28C
    battle_gp_offset = 0xB2A5
    battle_tp_offset = 0xB2DB
    return_rom_addr = 0xFDAC05

    scale_reward_rt: assemble.ASMList = [
        # xp  - A already set to 16-bit
        inst.LDA(reward_rom_st, AM.LNG_X),
        inst.BEQ("no_xp"),
        inst.JSL(scale_16_rom_addr, AM.LNG),
        inst.JSL(scale_16_rom_addr, AM.LNG),
        inst.CLC(),
        inst.ADC(battle_xp_offset, AM.ABS),
        inst.BCC("no_xp_carry"),
        inst.LDA(0xFFFF, AM.IMM16),
        "no_xp_carry",
        inst.STA(battle_xp_offset, AM.ABS),
        "no_xp",
        # gp
        inst.LDA(reward_rom_st+2, AM.LNG_X),
        inst.BEQ("no_gp"),
        inst.JSL(scale_16_rom_addr, AM.LNG),
        inst.CLC(),
        inst.ADC(battle_gp_offset, AM.ABS),
        inst.BCC("no_gp_carry"),
        inst.LDA(0xFFFF, AM.IMM16),
        "no_gp_carry",
        inst.STA(battle_gp_offset, AM.ABS),
        "no_gp",
        # tp
        inst.TDC(),
        inst.SEP(0x20),
        inst.LDA(reward_rom_st+6, AM.LNG_X),
        inst.CMP(1, AM.IMM8),  # Min TP to scale
        inst.BCC("no_scale_tp"),
        ] + scalingschemes.get_affine_scale_values_routine(5, "tp") + [
        inst.LDA(reward_rom_st + 6, AM.LNG_X),
        inst.JSL(scale_8_rom_addr, AM.LNG),
        "no_scale_tp",
        inst.CMP(0, AM.IMM8),
        inst.BNE("nonzero_tp"),
        inst.INC(mode=AM.NO_ARG),
        "nonzero_tp",
        inst.REP(0x20),
        inst.CLC(),
        inst.ADC(battle_tp_offset, AM.ABS),
        inst.BCC("no_tp_carry"),
        inst.SEP(0x20),
        inst.INC(battle_tp_offset+2, AM.ABS),
        inst.REP(0x20),
        "no_tp_carry",
        inst.STA(battle_tp_offset, AM.ABS),
        inst.JMP(return_rom_addr, AM.LNG)
        # Why is tp given an extra byte instead of XP or GP?
    ]

    # FDABBA  86 28          STX $28
    # FDABBC  A2 07 00       LDX #$0007
    # FDABBF  86 2A          STX $2A
    # FDABC1  22 BF FD C1    JSL $C1FDBF
    # FDABC5  A6 2C          LDX $2C
    # FDABC7  86 06          STX $06
    # FDABC9  7B             TDC
    # FDABCA  A5 0E          LDA $0E
    # FDABCC  38             SEC
    # FDABCD  E9 03          SBC #$03
    # FDABCF  AA             TAX
    # FDABD0  86 04          STX $04
    # FDABD2  C2 20          REP #$20
    # FDABD4  A6 06          LDX $06
    new_reward_routine = (
        store_original_level_rt +
        get_reward_addr_rt +
        scale_reward_rt
    )

    asmpatcher.apply_jmp_patch(
        new_reward_routine,
        byteops.to_file_ptr(hook_rom_addr),
        ct_rom,
        byteops.to_file_ptr(return_rom_addr)
    )

def add_scale8_routine(ct_rom: ctrom.CTRom) -> int:
    """Adds a routine to scale 8-bit values.  Returns file addr."""
    scale8_rt = scalingschemes.get_scale8_routine()
    scale8_rt_b = assemble.assemble(scale8_rt)
    scale8_addr = ct_rom.space_manager.get_free_addr(len(scale8_rt_b))

    ct_rom.seek(scale8_addr)
    ct_rom.write(scale8_rt_b, ctrom.freespace.FSWriteType.MARK_USED)

    return scale8_addr

def add_scale16_routine(ct_rom: ctrom.CTRom) -> int:
    """Adds a routine to scale 16-bit values.  Returns file addr."""

    scale16_rt = scalingschemes.get_scale16_routine()
    scale16_rt_b = assemble.assemble(scale16_rt)
    scale_16_addr = ct_rom.space_manager.get_free_addr(len(scale16_rt_b))

    ct_rom.seek(scale_16_addr)
    ct_rom.write(scale16_rt_b, ctrom.freespace.FSWriteType.MARK_USED)

    return scale_16_addr



def patch_enemy_stat_loads(
        ct_rom: ctrom.CTRom,
        scale8_addr: int,
        scale16_addr: int,
        scale_def_addr: int,
        scaling_exclusion_list: list[ctenums.EnemyID],
        true_levels_addr: int
):
    """
    After an enemy's stats are loaded, scale them using the enemy's level and
    The already-computed scaling level.
    """

    # The end of the stat loading:
    # FDB4C0  7A             PLY   <--- Hook here before it messes with Y
    # FDB4C1  7B             TDC
    # FDB4C2  85 00          STA $00
    # FDB4C4  E8             INX
    # FDB4C5  BF 00 47 CC    LDA $CC4700,X
    # FDB4C9  99 C6 5F       STA $5FC6,Y
    # FDB4CC  C8             INY
    # FDB4CD  E6 00          INC $00
    # FDB4CF  A5 00          LDA $00
    # FDB4D1  C9 03          CMP #$03
    # FDB4D3  90 EF          BCC $FDB4C4
    #  - Copy this whole part of the routine.
    #  - Then go back and modify the stats.
    # FDB4D5  6B             RTL

    hook_addr = byteops.to_file_ptr(0xFDB4C0)
    stat_start_rom_addr = 0xCC4700
    return_rom_addr = 0xFDB4D5

    old_rt = [
        inst.PLY(),
        inst.PHY(),  # Adding this to restore Y later.
        inst.TDC(),
        inst.STA(0x00, AM.DIR),
        "loop1_st",
        inst.INX(),
        inst.LDA(stat_start_rom_addr, AM.LNG_X),
        inst.STA(0x5FC6, AM.ABS_Y),
        inst.INY(),
        inst.INC(0x00, AM.DIR),
        inst.LDA(0x00, AM.DIR),
        inst.CMP(0x03, AM.IMM8),
        inst.BCC("loop1_st"),
        inst.PLY()
    ]

    temp_scale_factor_addr = 0

    level_offset = 0x7E5FBF
    hp_offset_lo = 0x7E5FB0

    index_offset = 0x5FAD
    hp_ram_offset = 0x5FB0
    atk_ram_offset = 0x5FEA
    hit_ram_offset = 0x5FE7
    evd_ram_offset = 0x5FE8
    mag_ram_offset = 0x5FE6
    lvl_ram_offset = 0x5FBF
    def_ram_offset = 0x5FEB

    def make_scale_block(
            stat_offset: int,
            value_exclusion: typing.Optional[int] = None
    ) -> assemble.ASMList:
        routine = [
            inst.LDA(stat_offset, AM.ABS_Y)
        ]
        if value_exclusion is not None:
            routine.extend([
                inst.CMP(value_exclusion, AM.IMM8),
                inst.BEQ(f"skip+{stat_offset:04X}")
            ])

        routine.extend([
            inst.JSL(byteops.to_rom_ptr(scale8_addr)),
            inst.STA(stat_offset, AM.ABS_Y),
            f"skip+{stat_offset:04X}"
        ])
        return routine

    scale_part = [
        # ignore scaling for some enemies
        inst.LDA(index_offset, AM.ABS_Y),
    ]

    for enemy_id in scaling_exclusion_list:
        scale_part += [
            inst.CMP(enemy_id, AM.IMM8),
            inst.BEQ("skip_scaling")
        ]

    true_levels_rom_addr = byteops.to_rom_ptr(true_levels_addr)
    scale_part += [
        inst.CMP(0xFF, AM.IMM8),  # placeholder empty enemy
        inst.BNE("scale_enemy"),
        "skip_scaling",
        inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.STA(index_offset+1, AM.ABS_Y),  # Store scaling level as fake orig
        inst.JMP(return_rom_addr, AM.LNG),
        "scale_enemy",
        # Write scaled level in for enemy's level stat
        # Also populate the from/to multipliers for HP scaling.
        inst.LDX(0x0000, AM.IMM16),
        inst.TAX(),
        inst.LDA(true_levels_rom_addr, AM.LNG_X),
        # inst.LDA(lvl_ram_offset, AM.ABS_Y),
        inst.STA(memory.Memory.ORIGINAL_LEVEL_TEMP, AM.LNG),
        inst.STA(index_offset + 1, AM.ABS_Y),  # Store original level after index
        inst.STA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.STA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
        inst.LDA(lvl_ram_offset, AM.ABS_Y),
        inst.JSL(byteops.to_rom_ptr(scale8_addr), AM.LNG),
        inst.STA(lvl_ram_offset, AM.ABS_Y),
        # HP exception for SoS: Subtract 10k, then readd after scaling.
        inst.LDA(index_offset, AM.ABS_Y),
        inst.CMP(ctenums.EnemyID.SON_OF_SUN_EYE, AM.IMM8),
        inst.BNE("normal_load"),
        inst.REP(0x20),
        inst.LDA(hp_ram_offset, AM.ABS_Y),
        inst.SEC(),
        inst.SBC(10000, AM.IMM16),
        inst.BRA("scale_hp"),
        "normal_load",
        inst.REP(0x20),
        inst.LDA(hp_ram_offset, AM.ABS_Y),
        "scale_hp",
        inst.JSL(byteops.to_rom_ptr(scale16_addr)),
        inst.AND(0x7FFF, AM.IMM16),
        inst.BNE("nonzero_hp"),
        inst.INC(mode=AM.NO_ARG),
        "nonzero_hp",
        inst.STA(hp_ram_offset, AM.ABS_Y),
        inst.STA(hp_ram_offset+2, AM.ABS_Y),
        # Check for SoS to re-add the 10k
        inst.SEP(0x20),
        inst.LDA(index_offset, AM.ABS_Y),
        inst.CMP(ctenums.EnemyID.SON_OF_SUN_EYE, AM.IMM8),
        inst.BNE("end_hp"),
        inst.REP(0x20),
        inst.LDA(hp_ram_offset, AM.ABS_Y),
        inst.CLC(),
        inst.ADC(10000, AM.IMM16),
        inst.STA(hp_ram_offset, AM.ABS_Y),
        inst.STA(hp_ram_offset + 2, AM.ABS_Y),
        inst.SEP(0x20),
        "end_hp",
        inst.TDC(),
        # Already set from hp scaling.
        # inst.LDA(memory.Memory.ORIGINAL_LEVEL_TEMP, AM.LNG),
        # inst.STA(memory.Memory.FROM_SCALE_TEMP, AM.LNG),
        # inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        # inst.STA(memory.Memory.TO_SCALE_TEMP, AM.LNG),
    ]
    scale_part.extend(
        make_scale_block(mag_ram_offset)
        + scalingschemes.get_affine_scale_values_routine(2, 'atk')
        +[
            inst.LDA(index_offset, AM.ABS_Y),
            inst.CMP(ctenums.EnemyID.SON_OF_SUN_FLAME, AM.IMM8),
            inst.BEQ("skip_atk_scale")
        ]
        + make_scale_block(atk_ram_offset)
        + ["skip_atk_scale"]
        + scalingschemes.get_affine_scale_values_routine(0x9, "hit_") \
        + make_scale_block(hit_ram_offset, value_exclusion=100) \
        + scalingschemes.get_affine_scale_values_routine(0x13, "evd_") \
        + make_scale_block(evd_ram_offset, value_exclusion=0xFF) \
        + [
            inst.LDA(def_ram_offset, AM.ABS_Y),
            inst.JSL(byteops.to_rom_ptr(scale_def_addr), AM.LNG),
            inst.STA(def_ram_offset, AM.ABS_Y)
        ]
        + [
            "end",
            inst.JMP(return_rom_addr, AM.LNG)
        ]
    )

    scale_routine = old_rt + scale_part

    asmpatcher.apply_jmp_patch(scale_routine, hook_addr, ct_rom,
                               byteops.to_file_ptr(return_rom_addr))


def patch_enemy_tech_power(
        ct_rom: ctrom.CTRom,
        scale8_rom_addr: Optional[int] = None,
):
    """Intercept tech effect loading to scale the tech power."""

    # This loop copies the effect header into [0x7FAEE6, 0x7FAEF2)
    # This is only called for enemy techs (not attacks).

    hook_addr = 0x01D836
    # C1D836  7B             TDC
    # C1D837  A8             TAY
    # C1D838  BF C9 7A CC    LDA $CC7AC9,X
    # C1D83C  99 E6 AE       STA $AEE6,Y
    # C1D83F  E8             INX
    # C1D840  C8             INY
    # C1D841  C0 0C 00       CPY #$000C
    # C1D844  90 F2          BCC $C1D838
    # C1D846  AD C7 B2       LDA $B2C7
    return_addr = 0x01D846

    # What we know about the current state:
    # - Caster's slot is in 0x7EB18B
    # - The tech id is in 0x7EB18C

    # This patch will:
    # 1) Return if the effect type is not damage.
    # 2) Use Caster's slot to find enemy's original level (added during scaling)
    # 3) Write scale factors and scale tech power.

    # 8-bit A, 16-bit X/Y
    eff_st_abs = 0xAEE6
    effect_load_rt: assemble.ASMList = [
        # Copy the original loading routine
        inst.TDC(),
        inst.TAY(),
        "load_loop_st",
        inst.LDA(0xCC7AC9, AM.LNG_X),
        inst.STA(eff_st_abs, AM.ABS_Y),
        inst.INX(),
        inst.INY(),
        inst.CPY(0x000C, AM.IMM16),
        inst.BCC("load_loop_st"),
    ]

    slot_addr_abs = 0x7EB18B & 0xFFFF
    effect_scale_rt = [
        inst.LDA(eff_st_abs, AM.ABS),  # 0th byte is mode
        inst.CMP(0x03, AM.IMM8),  # Damage
        inst.BEQ("scale"),
        inst.CMP(0x08, AM.IMM8),  # Multi-hit -- Do enemies use this?
        inst.BEQ("scale"),
        inst.BRA("no scale"),
        "scale",
        # Let's be lazy and just do the linear scale for now.
        # inst.LDA(0x80, AM.IMM8),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.TDC(),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.LDA(slot_addr_abs, AM.ABS),  # known < 0x80
        # inst.STA(SR.M7B, AM.LNG),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.LNG),
        # inst.TAX(),
        # inst.TDC(),
        # inst.SEP(0x20),
        # inst.LDA(0x5E2D+1, AM.ABS_X),
        # Aternate without mode7 Registers
        inst.LDA(slot_addr_abs, AM.ABS),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(0xFDA80B, AM.LNG_X),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(0x0001, AM.ABS_X),
        # End Alternate
        inst.STA(memory.Memory.ORIGINAL_LEVEL_TEMP & 0xFFFF, AM.ABS),
        inst.STA(memory.Memory.FROM_SCALE_TEMP & 0xFFFF, AM.ABS)
    ] + scalingschemes.get_affine_scale_values_routine(
        0xF, 'techscale'
    ) + [
        # inst.LDA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS),
        # inst.STA(memory.Memory.TO_SCALE_TEMP & 0xFFFF, AM.ABS),
        inst.LDA(eff_st_abs + 0x09, AM.ABS),
        inst.JSL(scale8_rom_addr, AM.LNG),
        inst.STA(eff_st_abs + 0x09, AM.ABS),
        "no scale",
        inst.TDC(),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    scale_routine = effect_load_rt + effect_scale_rt
    asmpatcher.apply_jmp_patch(scale_routine, hook_addr, ct_rom, return_addr)


def patch_enemy_attack_power(
        ct_rom: ctrom.CTRom,
        scale8_rom_addr: Optional[int] = None,
):
    """Intercept attack loading to scale the power."""

    # This is almost identical to tech power.
    hook_addr = 0x01D943
    # --- Jump in here where the effect header is copied ---
    # C1D943  7B             TDC
    # C1D944  A8             TAY
    # C1D945  BF C6 89 CC    LDA $CC89C6,X
    # C1D949  99 E6 AE       STA $AEE6,Y
    # C1D94C  E8             INX
    # C1D94D  C8             INY
    # C1D94E  C0 0C 00       CPY #$000C
    # C1D951  90 F2          BCC $C1D945
    return_addr = 0x01D953
    # --- Return here when it's going to do stuff with the header ---
    # C1D953  AD C7 B2       LDA $B2C7

    copy_eff_rt = [
        inst.TDC(),
        inst.TAY(),
        "copy_loop_st",
        inst.LDA(0xCC89C6, AM.LNG_X),
        inst.STA(0xAEE6, AM.ABS_Y),
        inst.INX(),
        inst.INY(),
        inst.CPY(0x000C, AM.IMM16),
        inst.BCC("copy_loop_st")
    ]

    slot_addr_abs = 0x7EB18B & 0xFFFF
    eff_st_abs = 0xAEE6
    effect_scale_rt = [
        # Let's be lazy and just do the linear scale for now.
        # inst.LDA(0x80, AM.IMM8),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.TDC(),
        # inst.STA(SR.M7A, AM.LNG),
        # inst.LDA(slot_addr_abs, AM.ABS),  # known < 0x80
        # inst.STA(SR.M7B, AM.LNG),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.LNG),
        # inst.TAX(),
        # inst.TDC(),
        # inst.SEP(0x20),
        # inst.LDA(0x5E2D + 1, AM.ABS_X),
        # Alternate without mode7 registers
        inst.LDA(slot_addr_abs, AM.ABS),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.REP(0x20),
        inst.LDA(0xFDA80B, AM.LNG_X),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(0x0001, AM.ABS_X),
        # End Alternate
        inst.STA(memory.Memory.ORIGINAL_LEVEL_TEMP & 0xFFFF, AM.ABS),
        inst.STA(memory.Memory.FROM_SCALE_TEMP & 0xFFFF, AM.ABS)
    ]

    effect_scale_rt += scalingschemes.get_affine_scale_values_routine(
        0xF, 'atkscale'  # TODO: Check this scaler
    )
    effect_scale_rt += [
        # inst.LDA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS),
        # inst.STA(memory.Memory.TO_SCALE_TEMP & 0xFFFF, AM.ABS),
        inst.LDA(eff_st_abs + 0x09, AM.ABS),
        # SoS Flame is a unique attack with power 0xFF that should not be scaled
        inst.CMP(0xFF, AM.IMM8),
        inst.BEQ("no_scale"),
        inst.JSL(scale8_rom_addr, AM.LNG),
        inst.STA(eff_st_abs + 0x09, AM.ABS),
        "no_scale",
        inst.TDC(),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    scale_routine = copy_eff_rt + effect_scale_rt
    asmpatcher.apply_jmp_patch(scale_routine, hook_addr, ct_rom, return_addr)


def get_ai_stat_scale_routine(
        scale8_rom_addr: int,
        scale_def_rom_addr: int
) -> assemble.ASMList:
    """
    Returns an ASMList that scales an 8-bit stat as used in an ai script.
    Ends with a JSL.  Assumes the following conditions on entry:
    - Stat index in $0E (dir)
    - Stat value in A (b-bit)
    - Enemy slot data start offset (0x7E) in Y (16-bit)
    - Current AI command offset (0xCC) in X (16-bit)
    - Original Level/Scaling Level are set correctly.
    """

    magic_stat_offset = 0x39
    evade_stat_offset = 0x3B
    offense_stat_offset = 0x3D
    defense_stat_offset = 0x3E

    scale_rt: assemble.ASMList = [
        inst.PHA(),
        inst.LDA(0x0E, AM.DIR),
        inst.CMP(defense_stat_offset, AM.IMM8),
        inst.BNE("not_def"),
        inst.PLA(),
        inst.JSL(scale_def_rom_addr, AM.LNG),
        inst.RTL(),
        "not_def",
        inst.CMP(magic_stat_offset, AM.IMM8),
        inst.BNE("not_magic"),
        *scalingschemes.get_affine_scale_values_routine(_mag_affine_constant, "mag"),
        inst.BRL("scale"),
        "not_magic",
        inst.CMP(evade_stat_offset, AM.IMM8),
        inst.BNE("not_evade"),
        *scalingschemes.get_affine_scale_values_routine(_evd_affine_constant, "evd"),
        inst.BRL("scale"),
        "not_evade",
        inst.CMP(offense_stat_offset, AM.IMM8),
        inst.BNE("no_scale"),
        *scalingschemes.get_affine_scale_values_routine(_atk_affine_constant, "atk"),
        "scale",
        inst.PLA(),
        inst.JSL(scale8_rom_addr, AM.LNG),
        inst.RTL(),
        "no_scale",
        inst.PLA(),
        inst.RTL()
    ]

    return scale_rt


def patch_ai_tech_02(ct_rom: ctrom.CTRom,
                     obstacle_safety_level: int = 30):
    """
    Make dynamic tech adjustments.  Does not change the other commands which
    perform a tech while doing other actions.
    - Obstacle becomes single target at low levels
    """

    #                      --------sub start--------
    # C19A3D  AD FC B1       LDA $B1FC
    # C19A40  29 FD          AND #$FD
    # C19A42  8D FC B1       STA $B1FC
    # C19A45  AE D2 B1       LDX $B1D2
    # C19A48  E8             INX
    # C19A49  8E D2 B1       STX $B1D2
    # C19A4C  BF 00 00 CC    LDA $CC0000,X  # The tech ID
    hook_addr = 0x019A4C
    # C19A50  85 0E          STA $0E
    return_addr = 0x019A50
    # C19A52  8D E4 AE       STA $AEE4
    # C19A55  8D 8C B1       STA $B18C

    obstacle_id = 0x58
    chaos_breath_id = 0x77

    new_rt: assemble.ASMList = [
        inst.LDA(0xCC0000, AM.LNG_X),
        inst.CMP(obstacle_id, AM.IMM8),
        inst.BNE("done"),
        # We have obstacle, so do a scaling level comparison
        inst.LDA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS),
        inst.CMP(obstacle_safety_level, AM.IMM8),
        inst.BCS("normal obstacle"),
        inst.LDA(chaos_breath_id, AM.IMM8),
        inst.BRA("done"),
        "normal obstacle",
        inst.LDA(obstacle_id, AM.IMM8),
        "done",
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)


def patch_ai_set_stat_0B(ct_rom: ctrom.CTRom,
                         ai_stat_scale_rom_addr: int):
    """
    Patch action 0xB - set single stat (or OR it).
    We only intercept the setting part.
    """

    # The value to set to is in $10 and  the stat offset is in $0E
    hook_addr = 0x019D5D
    # C19D5D  A5 10          LDA $10
    # C19D5F  91 0E          STA ($0E),Y
    return_addr = 0x019D61
    # C19D61  AD C7 B3       LDA $B3C7

    new_rt: assemble.ASMList = [
        inst.LDA(0x10, AM.DIR),
        inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
        inst.STA(0x0E, AM.DIR_16_Y),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)


def patch_ai_stat_math_0C(ct_rom: ctrom.CTRom,
                          ai_stat_scale_rom_addr: int,
                          scale_def_rom_addr: int
):
    """
    Patch action 0x0C - add/sub to stat.
    """

    hook_addr = 0x019D80
    # C19D80  BF 02 00 CC    LDA $CC0002,X <-- magnitute to add/sub
    return_addr = 0x019D84
    # C19D84  AA             TAX
    # C19D85  86 10          STX $10

    new_rt: assemble.ASMList = [
        inst.LDA(0xCC0002, AM.LNG_X),
        inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)

    # C19DBD  AD C7 B3       LDA $B3C7
    # C19DC0  C9 00          CMP #$00
    # C19DC2  F0 04          BEQ $C19DC8
    final_hook = 0x019DBD
    return_addr = 0x019DC2
    stat_offset_addr = 0xB3C7
    def_offset = 0x3E
    rt = [
        inst.LDA(stat_offset_addr, AM.ABS),
        inst.CMP(def_offset, AM.IMM8),
        inst.BNE("skip"),
        inst.LDA(0x5E2D, AM.ABS_X),
        inst.JSL(scale_def_rom_addr, AM.LNG),
        inst.STA(0x5E2D, AM.ABS_X),
        "skip",
        inst.LDA(stat_offset_addr, AM.ABS),
        inst.CMP(0x00, AM.IMM8),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, final_hook, ct_rom, return_addr)

def patch_ai_set_stats_11(ct_rom: ctrom.CTRom,
                          ai_stat_scale_rom_addr: int):
    """
    Patch action 0x11 - scale stats to dynamically scale.
    """

    # Action 0x11 - Multi Stat Set
    # Does this kind of loop four times.
    hook_addr = 0x019F72
    # C19F72  7B             TDC
    # C19F73  E2 20          SEP #$20
    # C19F75  AE D2 B1       LDX $B1D2
    # C19F78  BF 01 00 CC    LDA $CC0001,X
    # C19F7C  AA             TAX
    # C19F7D  86 0E          STX $0E
    # C19F7F  AE D2 B1       LDX $B1D2
    # C19F82  BF 02 00 CC    LDA $CC0002,X
    # C19F86  91 0E          STA ($0E),Y
    # C19F88  AE D2 B1       LDX $B1D2

    return_addr = 0x019FC1
    # C19FC1  AD C7 B3       LDA $B3C7

    new_rt: assemble.ASMList = [
        inst.TDC(),
        inst.SEP(0x20),
    ]

    ai_read_addr = 0xCC0001
    for _ in range(4):
        new_rt += [
            inst.LDX(0xB1D2, AM.ABS),
            inst.LDA(ai_read_addr, AM.LNG_X),
            inst.TAX(),
            inst.STX(0x0E, AM.DIR),
            inst.LDX(0xB1D2, AM.ABS),
            inst.LDA(ai_read_addr + 1, AM.LNG_X),
            inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
            inst.STA(0x0E, AM.DIR_16_Y),
        ]
        ai_read_addr += 2

    new_rt += [
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)


def patch_ai_set_stats_12(
        ct_rom: ctrom.CTRom,
        ai_stat_scale_rom_addr: int):
    """
    Patch action 0x12 - Do tech and set stats.
    """

    # Very similar to 0x11.  Five blocks like:
    # C19FED  AE D2 B1       LDX $B1D2
    # C19FF0  BF 05 00 CC    LDA $CC0005,X
    # C19FF4  AA             TAX
    # C19FF5  86 0E          STX $0E
    # C19FF7  AE D2 B1       LDX $B1D2
    # C19FFA  BF 06 00 CC    LDA $CC0006,X  <-- hook here
    # C19FFE  91 0E          STA ($0E),Y
    # ...
    # C1A00D  BF 08 00 CC    LDA $CC0008,X  <-- hook here
    # ...
    # C1A020  BF 0A 00 CC    LDA $CC000A,X  <-- hook here
    # ...
    # C1A033  BF 0C 00 CC    LDA $CC000C,X  <-- hook here
    # ...
    # C1A046  BF 0E 00 CC    LDA $CC000E,X  <-- hook here
    # Replace each stat load with a load+scale routine.

    hooks = [0x019FFA, 0x01A00D, 0x01A020, 0x01A033, 0x01A046]
    for ind, hook_addr in enumerate(hooks):
        return_addr = hook_addr + 4
        action_offst = 6 + 2*ind
        rt: assemble.ASMList = [
            inst.LDA(0xCC0000+action_offst, AM.LNG_X),
            inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
            inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
        ]
        asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, return_addr)


def patch_ai_multi_stat_math_14(
        ct_rom: ctrom.CTRom,
        ai_stat_scale_rom_addr: int,
        scale_def_rom_addr: int
):
    """
    Patch action 0x14 - Add to multiple stats.
    """

    # C1A1AF  BF 02 00 CC    LDA $CC0002,X
    # C1A1C5  BF 04 00 CC    LDA $CC0004,X
    # C1A1DB  BF 06 00 CC    LDA $CC0006,X
    # C1A1F1  BF 08 00 CC    LDA $CC0008,X
    hooks = [0x01A1AF, 0x01A1C5, 0x01A1DB, 0x01A1F1]
    for ind, hook_addr in enumerate(hooks):
        return_addr = hook_addr + 4
        action_offset = 2 + 2*ind
        rt: assemble.ASMList = [
            inst.LDA(0xCC0000+action_offset, AM.LNG_X),
            inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
            inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
        ]
        asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, return_addr)

    # Immediately after last stat add
    # C1A1FA  AD C7 B3       LDA $B3C7
    # C1A1FD  C9 00          CMP #$00
    # C1A1FF  F0 04          BEQ $C1A205
    final_hook = 0x01A1FA
    return_addr = 0x01A1FF
    def_offset = 0x3E
    rt: assemble.ASMList = [
        inst.LDA(def_offset, AM.ABS_Y),
        inst.JSL(scale_def_rom_addr, AM.LNG),
        inst.STA(def_offset, AM.ABS_Y),
        inst.LDA(0xB3C7, AM.ABS),
        inst.CMP(0x00, AM.IMM8),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(rt, final_hook, ct_rom, return_addr)


def patch_ai_multi_stat_math_15(
        ct_rom: ctrom.CTRom,
        ai_stat_scale_rom_addr: int,
        scale_def_rom_addr: int
):
    """
    Patch action 0x15 - Add to multiple stats and do a tech.
    """

    # C1A233  BF 06 00 CC    LDA $CC0006,X
    # C1A249  BF 08 00 CC    LDA $CC0008,X
    # C1A25F  BF 0A 00 CC    LDA $CC000A,X
    # C1A275  BF 0C 00 CC    LDA $CC000C,X
    # C1A28B  BF 0E 00 CC    LDA $CC000E,X

    hooks = [0x01A233, 0x01A249, 0x01A25F, 0x01A275, 0x01A28B]
    for ind, hook_addr in enumerate(hooks):
        return_addr = hook_addr + 4
        action_offset = 6 + 2*ind
        rt: assemble.ASMList = [
            inst.LDA(0xCC0000+action_offset, AM.LNG_X),
            inst.JSL(ai_stat_scale_rom_addr, AM.LNG),
            inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
        ]
        asmpatcher.apply_jmp_patch(rt, hook_addr, ct_rom, return_addr)

    # Check def after stat math
    # C1A294  AD FC B1       LDA $B1FC
    # C1A297  29 FD          AND #$FD
    # C1A299  8D FC B1       STA $B1FC
    # C1A29C  AE D2 B1       LDX $B1D2
    # Y has stat offset
    final_hook = 0x01A294
    return_addr = 0x01A299
    def_offset = 0x3E

    rt: assemble.ASMList = [
        inst.LDA(def_offset, AM.ABS_Y),
        inst.JSL(scale_def_rom_addr, AM.LNG),
        inst.STA(def_offset, AM.ABS_Y),
        inst.LDA(0xB1FC, AM.ABS),
        inst.AND(0xFD, AM.IMM8),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(rt, final_hook, ct_rom, return_addr)


def patch_ai_cond_hp_lte_08(
        ct_rom: ctrom.CTRom,
        scale16_rom_addr: int
):
    """
    Patch ai condition 0x08 - Check if enemy HP <= target
    """

    # C190CA  8E D2 B1       STX $B1D2
    # Separately read lo and hi bytes of HP Value and store in $08
    # C190CD  BF 00 00 CC    LDA $CC0000,X
    # C190D1  85 08          STA $08
    # C190D3  BF 01 00 CC    LDA $CC0001,X
    # C190D7  85 09          STA $09
    # C190D9  7B             TDC
    # C190DA  AA             TAX

    # Later read HP value from ram and compare.
    # C190E9  BF 0B A8 FD    LDA $FDA80B,X
    # C190ED  AA             TAX
    hook_addr = 0x0190EE
    # C190EE  BD 03 00       LDA $0003,X
    # C190F1  C5 08          CMP $08
    return_addr = 0x0190F3
    # C190F3  F0 02          BEQ $C190F7
    # C190F5  B0 0E          BCS $C19105

    orig_level_offset = 0x01
    new_rt: assemble.ASMList = [
        inst.SEP(0x20),
        inst.LDA(0x0000, AM.ABS_X),
        inst.CMP(ctenums.EnemyID.SON_OF_SUN_EYE, AM.IMM8),
        inst.BNE("normal_scaling"),
        inst.REP(0x20),
        inst.BRA("skip_scale"),
        inst.LDA(0x08, AM.DIR),
        "normal_scaling",
        inst.LDA(orig_level_offset, AM.ABS_X),
        # inst.STA(memory.Memory.ORIGINAL_LEVEL_TEMP & 0xFFFF, AM.ABS),
        # inst.LDA(memory.Memory.FROM_SCALE_TEMP & 0xFFFF, AM.ABS),
        # inst.STA(memory.Memory.TO_SCALE_TEMP & 0xFFFF, AM.ABS),
        inst.STA(memory.Memory.FROM_SCALE_TEMP & 0xFFFF, AM.ABS),
        inst.LDA(memory.Memory.SCALING_LEVEL & 0xFFFF, AM.ABS),
        inst.STA(memory.Memory.TO_SCALE_TEMP & 0xFFFF, AM.ABS),
        inst.REP(0x20),
        inst.LDA(0x08, AM.DIR),
        inst.JSL(scale16_rom_addr, AM.LNG),
        inst.STA(0x08, AM.DIR),
        "skip_scale",
        inst.LDA(0x0003, AM.ABS_X),
        inst.CMP(0x08, AM.DIR),
        inst.JMP(byteops.to_rom_ptr(return_addr), AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(new_rt, hook_addr, ct_rom, return_addr)


def patch_ai_scripts(
        ct_rom: ctrom.CTRom,
        scale8_rom_addr: int,
        scale16_rom_addr: int,
        scale_def_rom_addr: int,
):
    """
    Some AI scripts set stats.  We need to apply scaling routines to this.
    """

    ai_stat_scale_rt = get_ai_stat_scale_routine(scale8_rom_addr, scale_def_rom_addr)
    ai_stat_scale_rt_b = assemble.assemble(ai_stat_scale_rt)

    ai_stat_scale_addr = ct_rom.space_manager.get_free_addr(len(ai_stat_scale_rt_b))
    ct_rom.seek(ai_stat_scale_addr)
    ct_rom.write(ai_stat_scale_rt_b, ctrom.freespace.FSWriteType.MARK_USED)
    ai_stat_scale_rom_addr = byteops.to_rom_ptr(ai_stat_scale_addr)

    patch_ai_tech_02(ct_rom)
    patch_ai_set_stat_0B(ct_rom, ai_stat_scale_rom_addr)
    patch_ai_stat_math_0C(ct_rom, ai_stat_scale_rom_addr, scale_def_rom_addr)
    patch_ai_set_stats_11(ct_rom, ai_stat_scale_rom_addr)
    patch_ai_set_stats_12(ct_rom, ai_stat_scale_rom_addr)
    patch_ai_multi_stat_math_14(ct_rom, ai_stat_scale_rom_addr, scale_def_rom_addr)
    patch_ai_multi_stat_math_15(ct_rom, ai_stat_scale_rom_addr, scale_def_rom_addr)

    patch_ai_cond_hp_lte_08(ct_rom, scale16_rom_addr)


def get_scaling_scheme(
        scaling_scheme: enemyscaling.DynamicScalingScheme,
        scaling_scheme_options: enemyscaling.DyanamicScaleSchemeOptions,
        slow_mult_rom_addr: int,
) -> assemble.ASMList:
    if scaling_scheme == enemyscaling.DynamicScalingScheme.NONE:
        return []

    if scaling_scheme == enemyscaling.DynamicScalingScheme.PROGRESSION:
        if isinstance(scaling_scheme_options, enemyscaling.ProgressionScalingData):
            return scalingschemes.get_progression_scaler_from_opts(scaling_scheme_options, slow_mult_rom_addr)
        else:
            raise TypeError

    raise ValueError


def apply_full_scaling_patch(
        ct_rom: ctrom.CTRom,
        scaling_general_options: enemyscaling.DynamicScalingOptions,
        scaling_scheme_type: enemyscaling.DynamicScalingScheme,
        scaling_scheme_options: enemyscaling.DyanamicScaleSchemeOptions,
        script_manager: scriptmanager.ScriptManager,
        enemy_stat_dict: dict[ctenums.EnemyID, EnemyStats],
):
    if scaling_scheme_type == enemyscaling.DynamicScalingScheme.NONE:
        return

    # Slow Mult/Div versions
    # (0x01FDD3, 0x01FFFF),  # junk, Reserved for Bank C1 required (div)
    slow_div_rt: assemble.ASMList = [
        inst.JSR(0xC92A, AM.ABS),
        inst.RTL()
    ]
    slow_div_rt_addr = 0x01FDD3
    ct_rom.seek(slow_div_rt_addr)
    ct_rom.write(assemble.assemble(slow_div_rt))
    slow_div_rt_rom_addr = byteops.to_rom_ptr(slow_div_rt_addr)
    slow_mult_rt_rom_addr = 0xC1FDBF

    scaling_scheme = get_scaling_scheme(
        scaling_scheme_type, scaling_scheme_options, slow_mult_rt_rom_addr
    )
    scaling_scheme += [
        inst.LDA(memory.Memory.SCALING_LEVEL, AM.LNG),
        inst.CMP(scaling_general_options.max_scaling_level, AM.IMM8),
        inst.BCC("end_scaling"),
        inst.LDA(scaling_general_options.max_scaling_level, AM.IMM8),
        inst.STA(memory.Memory.SCALING_LEVEL, AM.LNG),
        "end_scaling",
    ]

    scaling_exclusion_list = [
        ctenums.EnemyID.NU, ctenums.EnemyID.NU_2,
        ctenums.EnemyID.UNKNOWN_BF,  # Weird Motherbrain object
        ctenums.EnemyID.UNUSED_FF,  # Placeholder enemy
    ]

    if not scaling_general_options.dynamic_scale_lavos:
        scaling_exclusion_list += [
            ctenums.EnemyID.LAVOS_2_LEFT, ctenums.EnemyID.LAVOS_2_RIGHT,
            ctenums.EnemyID.LAVOS_2_HEAD,
            ctenums.EnemyID.LAVOS_3_CORE, ctenums.EnemyID.LAVOS_3_LEFT,
            ctenums.EnemyID.LAVOS_3_RIGHT,
            ctenums.EnemyID.LAVOS_1,
            ctenums.EnemyID.LAVOS_OCEAN_PALACE,
        ]

    scale8_addr = add_scale8_routine(ct_rom)
    scale16_addr = add_scale16_routine(ct_rom)
    slow_scale8_addr = asmpatcher.add_jsl_routine(
        scalingschemes.get_slow_scale8_routine(slow_mult_rt_rom_addr, slow_div_rt_rom_addr),
        ct_rom
    )
    slow_scale16_addr = asmpatcher.add_jsl_routine(
        scalingschemes.get_slow_scale16_routine(slow_mult_rt_rom_addr, slow_div_rt_rom_addr),
        ct_rom
    )

    scale_def_addr = asmpatcher.add_jsl_routine(
        scalingschemes.get_scale_def_routine(
            10, 20,
            byteops.to_rom_ptr(slow_scale8_addr)
        ), ct_rom
    )

    set_scale_addr = asmpatcher.add_jsl_routine(
        scaling_scheme + [inst.RTL()], ct_rom
    )

    true_levels: bytearray = bytearray(
        [enemy_stat_dict.get(ctenums.EnemyID(ind), EnemyStats()).level
         for ind in range(0x100)]
    )
    true_levels[ctenums.EnemyID.ZEAL_2_RIGHT] = 0x30
    true_levels[ctenums.EnemyID.SAVE_POINT_ENEMY] = 20
    true_levels[ctenums.EnemyID.TURRET] = 35
    true_levels[ctenums.EnemyID.LAVOS_1] = 50
    true_levels[ctenums.EnemyID.LAVOS_OCEAN_PALACE] = 50
    true_levels[ctenums.EnemyID.R_SERIES] = 5
    true_levels[ctenums.EnemyID.MOTHERBRAIN] = 0x26
    true_levels[ctenums.EnemyID.DALTON_PLUS] = 20

    true_level_addr = ct_rom.space_manager.get_free_addr(
        len(true_levels), 0x410000
    )
    ct_rom.seek(true_level_addr)
    ct_rom.write(true_levels, ctrom.freespace.FSWriteType.MARK_USED)

    patch_scaling_inventory(ct_rom, script_manager, byteops.to_rom_ptr(set_scale_addr))
    patch_pre_battle_level_setting(ct_rom, scaling_scheme)
    patch_enemy_stat_loads(ct_rom, slow_scale8_addr, slow_scale16_addr, scale_def_addr, scaling_exclusion_list, true_level_addr)
    patch_enemy_rewards(ct_rom, scaling_exclusion_list, slow_scale8_addr, slow_scale16_addr)
    patch_enemy_tech_power(ct_rom, byteops.to_rom_ptr(slow_scale8_addr))
    patch_enemy_attack_power(ct_rom, byteops.to_rom_ptr(slow_scale8_addr))
    patch_ai_scripts(ct_rom, byteops.to_rom_ptr(slow_scale8_addr),
                     byteops.to_rom_ptr(slow_scale16_addr),
                     byteops.to_rom_ptr(scale_def_addr))



"""Apply base modifications to items"""
from ctrando.asm import assemble, instructions as inst
from ctrando.asm.instructions import AddressingMode as AM

from ctrando.common import asmpatcher, ctenums, ctrom
from ctrando.items import itemdata
from ctrando.items.gearrando import BoostID


def add_ds_accessories(
        item_man: itemdata.ItemDB
):
    """Add Dragon Tear and Valor Crest"""
    dragon_tear_stats = itemdata.AccessoryStats()
    dragon_tear_stats.has_critical_bonus = True
    dragon_tear_stats.critical_bonus = 20
    dragon_tear_secondary_stats = itemdata.AccessorySecondaryStats()
    dragon_tear_secondary_stats.set_equipable_by(list(ctenums.CharID))
    dragon_tear_secondary_stats.is_key_item = False
    dragon_tear_secondary_stats.price = 50000
    dragon_tear_secondary_stats.ngplus_carryover = True
    dragon_tear_secondary_stats.is_unsellable = True

    item_man[ctenums.ItemID.DRAGON_TEAR].stats = dragon_tear_stats
    item_man[ctenums.ItemID.DRAGON_TEAR].secondary_stats = dragon_tear_secondary_stats
    item_man[ctenums.ItemID.DRAGON_TEAR].set_name_from_str("{acc}DragonTear")
    item_man[ctenums.ItemID.DRAGON_TEAR].set_desc_from_str("Crit+20%")

    crest_stats = itemdata.AccessoryStats()
    crest_stats.has_critical_bonus = True
    crest_stats.critical_bonus = 20
    crest_stats.has_counter_effect = True
    crest_stats.counter_rate = 50
    crest_stats.has_normal_counter_mode = True

    crest_secondary = itemdata.AccessorySecondaryStats()
    crest_secondary.set_equipable_by([ctenums.CharID.AYLA]),
    crest_secondary.is_key_item = False
    crest_secondary.price = 65000
    crest_secondary.ngplus_carryover = True
    crest_secondary.is_unsellable = True

    item_man[ctenums.ItemID.VALOR_CREST].stats = crest_stats
    item_man[ctenums.ItemID.VALOR_CREST].secondary_stats = crest_secondary
    item_man[ctenums.ItemID.VALOR_CREST].set_name_from_str("{acc}ValorCrest")
    item_man[ctenums.ItemID.VALOR_CREST].set_desc_from_str("Crit+20, 50% counter")


def update_boosts(item_db: itemdata.ItemDB):
    """
    Add New boosts to DB: +10 Mag,
    Add Regal Plate +10Mdef/Stm.  Shadowplume 20 MDEF
    """
    mag_10 = itemdata.StatBoost()
    mag_10.stats_boosted = [itemdata.StatBit.MAGIC]
    mag_10.magnitude = 10
    item_db.stat_boosts.append(mag_10)

    pow_10 = itemdata.StatBoost()
    pow_10.stats_boosted = [itemdata.StatBit.POWER]
    pow_10.magnitude = 10
    item_db.stat_boosts.append(pow_10)

    spd_pow_3 = itemdata.StatBoost()
    spd_pow_3.stats_boosted = [itemdata.StatBit.POWER, itemdata.StatBit.SPEED]
    spd_pow_3.magnitude = 3
    item_db.stat_boosts.append(spd_pow_3)

    pow_5 = itemdata.StatBoost()
    pow_5.stats_boosted = [itemdata.StatBit.POWER]
    pow_5.magnitude = 5
    item_db.stat_boosts.append(pow_5)

    mag_5 = itemdata.StatBoost()
    mag_5.stats_boosted = [itemdata.StatBit.MAGIC]
    mag_5.magnitude = 5
    item_db.stat_boosts.append(mag_5)

    boost = item_db.stat_boosts[BoostID.MDEF_STAMINA_10]
    boost.stats_boosted = [itemdata.StatBit.MDEF, itemdata.StatBit.STAMINA]
    boost.magnitude = 10

    boost = item_db.stat_boosts[BoostID.MDEF_20]
    boost.magnitude = 20




def modify_item_stats(
        item_man: itemdata.ItemDB
):
    """
    Modify various stats.  These will not change functionality but are
    modifications needed to interact properly with the new item handling code.
    - Modify how HP accessories store their hp% mod
    - Modify how MP accessories store their mp% mod
    - Give Dark Mail the standard mdef+5 boost, note a duplicate ID
    """

    item_man[ctenums.ItemID.SILVERERNG].stats.hp_mod = 25
    item_man[ctenums.ItemID.GOLD_ERNG].stats.hp_mod = 50
    item_man[ctenums.ItemID.SILVERSTUD].stats.mp_mod = 50
    item_man[ctenums.ItemID.GOLD_STUD].stats.mp_mod = 75

    item_man[ctenums.ItemID.DARK_MAIL].secondary_stats.stat_boost_index = BoostID.MDEF_5


def add_crit_accessories(ct_rom: ctrom.CTRom):
    """
    Add +crit accessories to the rom.

    Notes
    -----
    - Byte0 & 0x10 for having +Crit
    - Byte1 & 0x0F holds +crit amount /5 (max +80 crit)
    """

    acc_st_offset = 0x5E78
    crit_bit = 0x10

    weapon_st_offset = 0x5E70
    crit_rate_offset = weapon_st_offset + 2
    # FDB37B  E2 20          SEP #$20
    hook_addr = 0x3DB37D
    # ----- Hook here before battle buff check
    # FDB37D  BD 79 5E       LDA $5E79,X
    # FDB380  89 80          BIT #$80
    # -----
    return_addr = 0x3DB382
    return_rom_addr = 0xFDB382
    # FDB382  F0 1D          BEQ $FDB3A1  <--- Return point
    # FDB384  7B             TDC
    # FDB385  BD 7B 5E       LDA $5E7B,X

    crit_rt: assemble.ASMList = [

        inst.LDA(acc_st_offset, AM.ABS_X),
        inst.BIT(crit_bit, AM.IMM8),
        inst.BEQ("end"),
        inst.LDA(acc_st_offset+1, AM.ABS_X),
        inst.AND(0x0F, AM.IMM8),
        inst.STA(0x00, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(0x00, AM.DIR),  # Total, x5
        inst.ADC(crit_rate_offset, AM.ABS_X),
        inst.CMP(100, AM.IMM8),
        inst.BCC("store"),
        inst.LDA(100, AM.IMM8),
        "store",
        inst.STA(crit_rate_offset, AM.ABS_X),
        "end",
        # Repeat overwritten hook code
        inst.LDA(acc_st_offset+1, AM.ABS_X),
        inst.BIT(0x80, AM.IMM8),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(crit_rt, hook_addr, ct_rom)


def normalize_hp_accessories(ct_rom: ctrom.CTRom):
    """Actually read accessory data instead of hardcoded item_ids"""

    # HP modifying accessories do not use the accessory data.
    # The game does a check for certain item IDs and has a hardcoded HP mod.

    # Location 1: Before battle:
    # FDB3AA  BD 57 5E       LDA $5E57,X   # Load Accessory ID
    # FDB3AD  C9 A0          CMP #$A0
    # FDB3AF  D0 18          BNE $FDB3C9   # If SilverErng
    # FDB3B1  C2 20          REP #$20
    # FDB3B3  BD 32 5E       LDA $5E32,X
    # FDB3B6  4A             LSR
    # FDB3B7  4A             LSR
    # FDB3B8  18             CLC
    # FDB3B9  7D 32 5E       ADC $5E32,X
    # FDB3BC  C9 E7 03       CMP #$03E7
    # FDB3BF  90 03          BCC $FDB3C4
    # FDB3C1  A9 E7 03       LDA #$03E7
    # FDB3C4  9D 32 5E       STA $5E32,X
    # FDB3C7  80 1E          BRA $FDB3E7   # Add 25% HP and check for cap
    # FDB3C9  E2 20          SEP #$20
    # FDB3CB  BD 57 5E       LDA $5E57,X   # Load Accessory ID
    # FDB3CE  C9 A1          CMP #$A1
    # FDB3D0  D0 15          BNE $FDB3E7   # If GoldErng
    # FDB3D2  C2 20          REP #$20
    # FDB3D4  BD 32 5E       LDA $5E32,X
    # FDB3D7  4A             LSR
    # FDB3D8  18             CLC
    # FDB3D9  7D 32 5E       ADC $5E32,X
    # FDB3DC  C9 E7 03       CMP #$03E7
    # FDB3DF  90 03          BCC $FDB3E4
    # FDB3E1  A9 E7 03       LDA #$03E7
    # FDB3E4  9D 32 5E       STA $5E32,X  # Add 50% HP and check for cap
    # FDB3E7  7B             TDC          # End

    # 8-bit A, 16-bit X,Y
    slow_div_rom_addr = 0xC1FDD3  # Put this somewhere good
    slow_mult_rom_addr = 0xC1FDBF
    battle_max_hp_addr = 0x5E32
    # During battle, accessory data is stored in [$5E78, X, $5E7C, X)
    acc_base = 0x5E78
    new_rt: assemble.ASMList = [
        inst.LDA(acc_base + 1, AM.ABS_X),
        inst.AND(0x10, AM.IMM8),
        inst.BEQ("skip_hp"),
        # inst.LDA(acc_base + 2, AM.ABS_X),
        # Mod
        inst.LDA(acc_base + 3, AM.ABS_X),
        # inst.AND(0xF0, AM.IMM8),
        inst.REP(0x20),
        inst.AND(0x00F0, AM.IMM16),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(0x28, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(0x28, AM.DIR),
        inst.STA(0x28, AM.DIR),
        # End Mod
        # inst.REP(0x20),
        # inst.AND(0x00FF, AM.IMM16),
        inst.STA(0x28, AM.DIR),
        inst.LDA(battle_max_hp_addr, AM.ABS_X),
        inst.STA(0x2A, AM.DIR),
        inst.PHX(),
        inst.JSL(slow_mult_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(0x2C, AM.DIR),
        inst.STA(0x28, AM.DIR),
        inst.LDA(100, AM.IMM16),
        inst.STA(0x2A, AM.DIR),
        inst.JSL(slow_div_rom_addr, AM.LNG),
        inst.LDA(0x2C, AM.DIR),
        inst.CLC(),
        inst.REP(0x10),
        inst.PLX(),
        inst.ADC(battle_max_hp_addr, AM.ABS_X),
        inst.CMP(999, AM.IMM16),
        inst.BCC("do_store"),
        inst.LDA(999, AM.IMM16),
        "do_store",
        inst.STA(battle_max_hp_addr, AM.ABS_X),
        "skip_hp",
        inst.SEP(0x20),
        inst.JMP(0xFDB3E7, AM.LNG)
    ]
    new_rt_bytes = assemble.assemble(new_rt)

    old_rt_len = 0xFDB3E7+2-0xFDB3AA
    new_rt_len = len(new_rt_bytes)

    if new_rt_len <= old_rt_len:
        ct_rom.seek(0x3DB3AA)
        ct_rom.write(new_rt_bytes)
    else:
        asmpatcher.apply_jmp_patch(new_rt, 0x3DB3AA,
                                   ct_rom, 0x3DB3E7)


    # Location 2: When opening a menu
    # C29295  C2 20          REP #$20
    # C29297  AE BA 9A       LDX $9ABA
    # C2929A  AD 95 9A       LDA $9A95
    # C2929D  E0 A1          CPX #$A1
    # C2929F  F0 08          BEQ $C292A9
    # C292A1  E0 A0          CPX #$A0
    # C292A3  F0 03          BEQ $C292A8
    # C292A5  A9 00 00       LDA #$0000
    # C292A8  4A             LSR
    # C292A9  4A             LSR
    # C292AA  18             CLC
    # C292AB  6D 95 9A       ADC $9A95
    # C292AE  C9 E7 03       CMP #$03E7
    # C292B1  90 03          BCC $C292B6
    # C292B3  A9 E7 03       LDA #$03E7
    # C292B6  8D 25 9B       STA $9B25
    # C292B9  CD 93 9A       CMP $9A93
    # C292BC  B0 03          BCS $C292C1
    # C292BE  8D 93 9A       STA $9A93
    # C292C1  08             PHP  # <--- Return here
    # There's more after for I'm not sure what.

    acc_id_addr = 0x9ABA
    max_hp_addr = 0x9A95
    alt_max_hp_addr = 0x9B25  # Not sure why this is used too
    cur_hp_addr = 0x9A93
    acc_data_start_rom_addr = 0xCC052C

    # Comes in with 8-bit A and X,Y
    new_rt: assemble.ASMList = [
        inst.LDX(acc_id_addr, AM.ABS),
        inst.PHX(),
        inst.TXA(),
        inst.SEC(),
        inst.SBC(ctenums.ItemID.HELM_END_94, AM.IMM8),
        inst.REP(0x30),
        inst.AND(0x00FF, AM.IMM16),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(acc_data_start_rom_addr, AM.LNG_X),
        inst.AND(0x1000, AM.IMM16),
        inst.BNE("do_scale"),
        inst.LDA(0x0000, AM.IMM16),
        inst.BRA("do_add"),
        "do_scale",
        inst.LDA(acc_data_start_rom_addr+3, AM.LNG_X),
        # inst.AND(0x00F0, AM.IMM16),
        # inst.STA(0x28, AM.DIR),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.LSR(mode=AM.NO_ARG),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(0x28, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(0x28, AM.DIR),
        inst.STA(0x28, AM.DIR),
        inst.LDA(max_hp_addr, AM.ABS),
        inst.STA(0x2A, AM.DIR),
        inst.JSL(slow_mult_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(0x2C, AM.DIR),
        inst.STA(0x28, AM.DIR),
        inst.LDA(100, AM.IMM16),
        inst.STA(0x2A, AM.DIR),
        inst.JSL(slow_div_rom_addr, AM.LNG),
        inst.LDA(0x2C, AM.DIR),
        "do_add",
        inst.CLC(),
        inst.ADC(max_hp_addr, AM.ABS),
        inst.CMP(999, AM.IMM16),
        inst.BCC("do_store"),
        inst.LDA(999, AM.IMM16),
        "do_store",
        # inst.STA(max_hp_addr, AM.ABS),
        inst.STA(alt_max_hp_addr, AM.ABS),
        inst.CMP(cur_hp_addr, AM.ABS),
        inst.BCS("done"),
        inst.STA(cur_hp_addr, AM.ABS),
        "done",
        inst.SEP(0x10),
        inst.PLX(),
        inst.JMP(0xC292C1, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        new_rt, 0x029295, ct_rom, 0x0292C1
    )


def normalize_mp_accessories(ct_rom: ctrom.CTRom):
    """Allow any accessory to set flags for mp reduction"""

    # In battle:
    # - MP value comes in through Y
    # - 8-bit A, 16-bit X,Y (used, so push first)
    #                      --------sub start--------
    # C1CBF6  C9 A2          CMP #$A2
    # C1CBF8  D0 04          BNE $C1CBFE
    # C1CBFA  98             TYA
    # C1CBFB  4A             LSR
    # C1CBFC  80 09          BRA $C1CC07
    # C1CBFE  C9 A3          CMP #$A3
    # C1CC00  D0 08          BNE $C1CC0A
    # C1CC02  98             TYA
    # C1CC03  4A             LSR
    # C1CC04  69 00          ADC #$00
    # C1CC06  4A             LSR
    # C1CC07  69 00          ADC #$00
    # C1CC09  A8             TAY
    # C1CC0A  60             RTS
    #                      ----------------
    hook_addr = 0x01CBF6
    return_addr = 0x01CC0A
    return_rom_addr = return_addr + 0xC00000
    acc_data_start_rom_addr = 0xCC052C

    battle_rt: assemble.ASMList = [
        inst.SEC(),
        inst.SBC(ctenums.ItemID.HELM_END_94, AM.IMM8),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.PHX(),
        inst.TAX(),
        inst.LDA(acc_data_start_rom_addr, AM.LNG_X),
        inst.AND(0x20, AM.IMM8),
        inst.BEQ("end"),
        inst.LDA(acc_data_start_rom_addr+3, AM.LNG_X),
        inst.AND(0x0F, AM.IMM8),
        inst.CMP(2, AM.IMM8),
        inst.BEQ("50perc"),
        inst.TYA(),
        inst.LSR(mode=AM.NO_ARG),
        inst.BRA("final_adc"),
        "50perc",
        inst.TYA(),
        inst.LSR(mode=AM.NO_ARG),
        inst.ADC(0x00, AM.IMM8),
        inst.LSR(mode=AM.NO_ARG),
        "final_adc",
        inst.ADC(0x00, AM.IMM8),
        inst.TAY(),
        "end",
        inst.PLX(),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(battle_rt, hook_addr,
                               ct_rom, return_addr)

    # In Menu:
    # - MP comes in A
    # - 8 bit A, 16 bit X,Y (but does  PHP. PLP anyway)
    # Accessory gets stored in Y, so that's free.  X seems in use.

    #                      --------sub start--------
    # C2BC59  08             PHP
    # C2BC5A  E2 30          SEP #$30
    # C2BC5C  AC BA 9A       LDY $9ABA
    # C2BC5F  C0 A2          CPY #$A2
    # C2BC61  F0 07          BEQ $C2BC6A
    # C2BC63  C0 A3          CPY #$A3
    # C2BC65  D0 06          BNE $C2BC6D
    # C2BC67  4A             LSR
    # C2BC68  69 00          ADC #$00
    # C2BC6A  4A             LSR
    # C2BC6B  69 00          ADC #$00
    # C2BC6D  28             PLP
    # C2BC6E  60             RTS
    #                      ----------------

    hook_addr = 0x02BC59
    return_addr = 0x02BC6E
    acc_addr = 0x9ABA
    return_rom_addr = return_addr + 0xC00000

    menu_rt: assemble.ASMList = [
        inst.PHX(),
        inst.PHP(),
        inst.SEP(0x30),
        inst.TAY(),
        inst.LDA(acc_addr, AM.ABS),
        inst.SEC(),
        inst.SBC(ctenums.ItemID.HELM_END_94, AM.IMM8),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(acc_data_start_rom_addr, AM.LNG_X),
        inst.AND(0x20, AM.IMM8),
        inst.BNE("do_scale"),
        inst.TYA(),
        inst.BRA("end"),
        "do_scale",
        inst.LDA(acc_data_start_rom_addr+3, AM.LNG_X),
        inst.AND(0x0F, AM.IMM8),
        inst.CMP(2, AM.IMM8),
        inst.BEQ("50perc"),
        inst.TYA(),
        inst.LSR(mode=AM.NO_ARG),
        inst.BRA("final_adc"),
        "50perc",
        inst.TYA(),
        inst.LSR(mode=AM.NO_ARG),
        inst.ADC(0x00, AM.IMM8),
        inst.LSR(mode=AM.NO_ARG),
        "final_adc",
        inst.ADC(0x00, AM.IMM8),
        "end",
        inst.PLP(),
        inst.PLX(),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(menu_rt, hook_addr, ct_rom, return_addr)

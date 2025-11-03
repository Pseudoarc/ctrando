"""Module to turn a vanilla CT Rom into an open world one"""
import io
import itertools
from typing import Optional

from ctrando.attacks import pctech
from ctrando.asm import assemble
from ctrando.asm import instructions as inst, assemble
from ctrando.characters import ctpcstats
from ctrando.common import byteops, ctrom, freespace, memory, ctenums, randostate, asmpatcher
from ctrando.base import apply_openworld, apply_openworld_ow, chesttext, modifyitems
from ctrando.base import decompressed_graphics

def apply_tf_compressed_enemy_gfx_hack(ct_rom: ctrom.CTRom):
    '''
    By default, CT forces compressed graphics for enemies with id > 0xF8.
    This hack instead looks at the graphics packet id to determine whether to decompress.
    '''

    # Original code: @ $C04775 (0x004775)
    #   LDX $6D       - Load (2*) the object number
    #   LDA $1101,X   - Look up the enemy_id of that object
    #   CMP #$F8      - Compare the enemy_id to 0xF8
    #   BCC $C04781   - If < 0xF8 jump to the compressed gfx routine
    #   BRL $C04845   - If >= 0xF8 jump to the uncompressed gfx routine

    # Upon entering the above code A holds the graphics packet id.  Only graphics packets
    # 0 through 6 (PCs) are compressed, so jump to the routines based on that.

    # @ $C04775
    #   CMP #$07      - Compare the graphics packet id to 7
    #   BCS $C04781   - If >= 7 jump to the compressed gfx routine
    #   BRA $C0477E   - If < 7 jump to the BRL

    AM = inst.AddressingMode
    routine: assemble.ASMList = [
        inst.CMP(0x07, AM.IMM8),
        inst.BCS(0x08, AM.REL_8),
        inst.BRA(0x03, AM.REL_8)
    ]

    routine_b = assemble.assemble(routine)

    ct_rom.seek(0x004775)
    ct_rom.write(routine_b)


def apply_mauron_enemy_tech_patch(
    ct_rom: ctrom.CTRom,
    # local_ptr_addr: int,
    bank_table_addr: Optional[int] = None,
):
    """
    Apply Mauron's patch to allow enemy tech animation scripts to be in any
    bank.

    param ct_rom:  The CTRom to apply the patch to.
    param bank_table_addr: If not none, the lookup table for the bank table
                           will be placed at this (file) address in the rom.
    """
    FSW = ctrom.freespace.FSWriteType

    if bank_table_addr is None:
        space_man = ct_rom.space_manager
        bank_table_addr = space_man.get_free_addr(0x100)

    bank_table_b = b"\xCD" * 0x100
    ct_rom.seek(bank_table_addr)
    ct_rom.write(bank_table_b, FSW.MARK_USED)

    # This is Mauron's patch which fetches the tech script address using the
    # bank table.  I'm not disassembling it except to show the bank load.
    rt = bytearray.fromhex(
        "A8 0A AA BF F0 61 CD 85 40 BB"
        "BF C6 DD CC"  # LDA $CCDDC6, X loads from the bank table
        "8542E2207BA8AAB7409581C8B7409580C8BBC00400D0F098C221654085407BA8"
        "C2200680901FADB3A0D016A9010099AC5D5A980A0AA8A74099BD5DA54299BF5D7"
        "AE640E640C8C01000D0D57BE220ADB3A0F0099CB3A0A482848080C2"
    )

    # Overwrite the bank location
    bank_table_addr_b = int.to_bytes(byteops.to_rom_ptr(bank_table_addr), 3, "little")
    rt[11:14] = bank_table_addr_b

    ct_rom.seek(0x0146ED)
    ct_rom.write(rt, FSW.NO_MARK)  # Should already be marked used.


def apply_mauron_enemy_attack_patch(
    ct_rom: ctrom.CTRom,
    # local_ptr_addr: int,
    bank_table_addr: Optional[int] = None,
):
    """
    Apply Mauron's patch to allow enemy attack animation scripts to be in any
    bank.

    param ct_rom:  The CTRom to apply the patch to.
    param bank_table_addr: If not none, the lookup table for the bank table
                           will be placed at this (file) address in the rom.
    """

    FSW = ctrom.freespace.FSWriteType

    if bank_table_addr is None:
        space_man = ct_rom.space_manager
        bank_table_addr = space_man.get_free_addr(0x100)

    bank_table_b = b"\xCD" * 0x100
    ct_rom.seek(bank_table_addr)
    ct_rom.write(bank_table_b, FSW.MARK_USED)

    # This is Mauron's patch which fetches the tech script address using the
    # bank table.  I'm not disassembling it except to show the bank load.
    rt = bytearray.fromhex(
        "A8 0A AA BF F0 5F CD 85 40 BB"  # 9 bytes
        "BF B2 FE C1"  # LDA $C1FEB2, X
        "8542E2207BA8AAB7409581C8B7409580C8BBC00400D0F098C221654085407BA8C220"
        "0680901FADB3A0D016A9010099AC5D5A980A0AA8A74099BD5DA54299BF5D7AE6"
        "40E640C8C01000D0D57BE220ADB3A0F0099CB3A0A482848080C2"
    )

    bank_table_addr_b = int.to_bytes(byteops.to_rom_ptr(bank_table_addr), 3, "little")
    rt[11:14] = bank_table_addr_b

    ct_rom.seek(0x014533)
    ct_rom.write(rt, FSW.NO_MARK)  # Should already be marked used.


def apply_mauron_player_tech_patch(
    ct_rom: ctrom.CTRom,
    local_ptr_addr: Optional[int] = None,
    bank_table_addr: Optional[int] = None,
):
    """
    Apply Mauron's patch to allow player tech animation scripts to be in any
    bank.  Also expand the tech pointers to allow 0xFF techs.  The id 0xFF is
    reserved for some menu functions.

    param ct_rom:  The CTRom to apply the patch to.
    param bank_table_addr: If not none, the lookup table for the bank table
                           will be placed at this (file) address in the rom.
    """
    FSW = freespace.FSWriteType

    space_man = ct_rom.space_manager
    if local_ptr_addr is None:
        # Allocate 2 bytes per tech for local pointers
        # We really only need 0x1FE bytes because tech 0xFF isn't allowed.
        local_ptr_addr = space_man.get_free_addr(0x200)

    ct_rom.seek(0x0D5EF0)
    script_local_ptrs = ct_rom.read(0x80 * 2)
    script_local_ptrs += b"\x00\x00" * 0x80

    ct_rom.seek(local_ptr_addr)
    ct_rom.write(script_local_ptrs, FSW.MARK_USED)

    if bank_table_addr is None:
        # Allocate 1 byte per tech for banks.
        # We really only need 0xFF bytes because tech 0xFF isn't allowed.
        bank_table_addr = space_man.get_free_addr(0x100)

    bank_table_b = (b"\xCE" * 0x80) + (b"\x00" * 0x80)
    ct_rom.seek(bank_table_addr)
    ct_rom.write(bank_table_b, FSW.MARK_USED)

    local_ptr_addr_hex = int.to_bytes(
        byteops.to_rom_ptr(local_ptr_addr), 3, "little"
    ).hex()
    bank_table_addr_hex = int.to_bytes(
        byteops.to_rom_ptr(bank_table_addr), 3, "little"
    ).hex()

    mauron_tech_patch = bytearray.fromhex(
        "a8 0a aa bf"
        + local_ptr_addr_hex
        + "85 40 bb bf"
        + bank_table_addr_hex
        + "85 42 e2 20 7b"
        "a8 aa b7 40 95 81 c8 b7 40 95 80 c8 bb c0 04 00"
        "d0 f0 98 c2 21 65 40 85 40 7b a8 c2 20 06 80 90"
        "1f ad b3 a0 d0 16 a9 01 00 99 ac 5d 5a 98 0a 0a"
        "a8 a7 40 99 bd 5d a5 42 99 bf 5d 7a e6 40 e6 40"
        "c8 c0 10 00 d0 d5 7b e2"
        "20 ad b3 a0 f0 09 9c b3 a0 a4 82 84 80 80 c2"
    )

    ct_rom.seek(0x014615)
    ct_rom.write(mauron_tech_patch, FSW.NO_MARK)


def apply_mauron_patches(ct_rom: ctrom.CTRom):
    apply_mauron_enemy_attack_patch(ct_rom)
    apply_mauron_enemy_tech_patch(ct_rom)
    apply_mauron_player_tech_patch(ct_rom)


# Unused EventIDs:
#     04B, 04C, 04D, 04E, 04F, 050, 051, 066
#     067, 068, 069, 06A, 06B, 06C, 06D, 06E
# Locations w/ EventID 0x18:
#     1F0, 1F1, 1F2, 1F3, 1F4, 1F5, 1F6, 1F7,
#     1F8, 1F9, 1FA, 1FB, 1FC, 1FD, 1FE, 1FF


def mark_initial_free_space(vanilla_rom: ctrom.CTRom):
    """
    Marks free space as per the DB's Offsets guide.

    DB is from Geiger with contributions from many on CC forums.
    """

    free_blocks = (
        # (0x00F2F0, 0x00F300),  Reserved for eventcommands
        # (0x01FDD3, 0x01FFFF),  # junk, Reserved for Bank C1 required (div)
        (0x027DE4, 0x028000),
        (0x02FE0C, 0x030000),  # junk
        (0x03FF0A, 0x040000),
        (0x05F365, 0x060000),
        (0x061E71, 0x062000),
        (0x06DD05, 0x06E000),
        (0x06FC51, 0x06FD00),
        (0x0BF164, 0x0C0000),  # junk + unused
        # (0x0C0424, 0x0C047E),  # Reserved for Stat Boosts
        (0x0C066C, 0x0C06A4),
        (0x0C36F4, 0x0C3A09),  # Unused + Junk
        (0x0C43AF, 0x0C4700),
        (0x0CFC2C, 0x0D0000),  # Junk + Unused
        (0x0D3FE4, 0x0D3FFF),  # 0x0DFA00 to 0x0E0000 is all FFs
        (0x0EDC1B, 0x0EE000),
        (0x0FFE85, 0x0FFFFC),
        (0x10DEC0, 0x10E000),
        (0x10FD60, 0x110000),
        (0x11FEF4, 0x120000),
        (0x12FF94, 0x130000),
        (0x13FFD8, 0x140000),
        (0x14FF73, 0x150000),
        (0x16F9F8, 0x170000),
        (0x17FEEE, 0x180000),
        (0x18CF68, 0x18D000),
        (0x19FC5B, 0x1A0000),
        (0x1AFC29, 0x1B0000),
        (0x1B7FF5, 0x1C0000),
        (0x1CDF98, 0x1D0000),
        (0x1DFD48, 0x1E0000),
        (0x1EBF90, 0x1EC000),
        # TODO: (0x1EFF51, 0x1F0000) empty space after default treasure text
        (0x1FFF75, 0x200000),
        (0x20332C, 0x2034E2),  # junk
        (0x20FD93, 0x210000),  # junk + unused
        (0x21DDB2, 0x21DE00),
        (0x21DE2C, 0x21DE80),
        (0x21DF80, 0x21E000),
        (0x21F518, 0x220000),
        (0x22FE46, 0x230000),
        (0x23F8C0, 0x240000),
        (0x2417B8, 0x242000),
        (0x2422E8, 0x242300),
        (0x2425B5, 0x242600),
        (0x242784, 0x242800),
        (0x242BFA, 0x243000),
        (0x24A600, 0x24A800),
        (0x24CC60, 0x24F000),
        (0x24F523, 0x24F600),
        (0x251A44, 0x252000),
        (0x25FBA0, 0x260000),
        (0x26FEF9, 0x270000),
        (0x27FF09, 0x280000),
        (0x28FF03, 0x290000),
        (0x29FFD3, 0x2A0000),
        (0x2AFF4A, 0x2B0000),
        (0x2BFEF4, 0x2C0000),
        # TF says this is junk but writing to it in the wrong way can cause
        # TF to crash.  The actual game works I think, but TF is unhappy.
        # (0x2FB168, 0x2FC000),
        (0x2CFEB1, 0x2D0000),
        (0x2DFF4C, 0x2E0000),
        (0x2EFF8C, 0x2F0000),
        (0x2FFF18, 0x300000),
        (0x30F5E7, 0x310000),
        (0x31FE2A, 0x320000),
        (0x32FE64, 0x330000),
        (0x33FDFB, 0x340000),
        (0x34FDEE, 0x350000),
        (0x35F7E6, 0x360000),  # Junk + Unused
        (0x366DC2, 0x367380),
        (0x369FE9, 0x36A000),  # Junk
        #  (0x3748B8, 0x374900),  # Junk, moved to dialogue freeing
        (0x37FFD1, 0x380000),
        (0x384639, 0x384650),
        #  (0x38AA94, 0x38B170),  # Junk, moved to dialogue freeing
        (0x38FFF4, 0x390000),
        # (0x39AFE9, 0x39B000),  # moved to dialogue freeing
        # (0x39FA76, 0x3A0000),  # Junk,  moved to dialogue freeing
        (0x3AFAA0, 0x3B0000),  # Junk
        (0x3BFFD0, 0x3C0000),  # Junk
        (0x3D6693, 0x3D6800),
        (0x3D8E64, 0x3D9000),
        (0x3DBB67, 0x3DC000),
        (0x3F8C03, 0x3F8C60),  # junk
        (0x3D9FEB, 0x3DA000),
    )

    MARK_FREE = ctrom.freespace.FSWriteType.MARK_FREE

    for block in free_blocks:
        vanilla_rom.space_manager.mark_block(block, MARK_FREE)


def mark_vanilla_dialogue_free(vanilla_rom: ctrom.CTRom):
    """
    Mark all ranges corresponding to vanilla CT dialogue/dialogue pointers
    free.

    Based on DB from Geiger.
    """

    dialogue_blocks = (
        (0x18D000, 0x190000),  # ptrs and dialogue.
        (0x1EC000, 0x1EFA00),  # ptrs and dialogue.
        (0x36A000, 0x36B350),  # ptrs and dialogue.
        (0x370000, 0x37F980),  # ptrs and dialogue and junk.
        (0x384650, 0x38B170),  # ptrs and dialogue and junk.
        (0x39AFE9, 0x3A0000),  # ptrs and dialogue and junk.
        (0x3CB9E8, 0x3CF9F0),  # ptrs and dialogue
        (0x3F4460, 0x3F8C60),  # ptrs and dialogue and junk.
    )

    MARK_FREE = ctrom.freespace.FSWriteType.MARK_FREE

    for block in dialogue_blocks:
        vanilla_rom.space_manager.mark_block(block, MARK_FREE)


def add_key_item_count(
        ct_rom: ctrom.CTRom,
        key_item_list: Optional[list[ctenums.ItemID]] = None
):
    """
    Increment the key item count when a key item is received.
    """

    if key_item_list is None:
        ItemID = ctenums.ItemID
        key_item_list = [
            ItemID.C_TRIGGER, ItemID.CLONE,
            ItemID.PENDANT, ItemID.PENDANT_CHARGE, ItemID.DREAMSTONE,
            ItemID.RUBY_KNIFE, ItemID.JETSOFTIME,
            ItemID.TOOLS, ItemID.RAINBOW_SHELL,
            ItemID.PRISMSHARD, ItemID.JERKY, ItemID.JERKY,
            ItemID.BENT_HILT, ItemID.BENT_SWORD,
            ItemID.HERO_MEDAL, ItemID.MASAMUNE_1, ItemID.MASAMUNE_2,
            ItemID.TOMAS_POP, ItemID.MOON_STONE, ItemID.SUN_STONE,
            ItemID.BIKE_KEY, ItemID.SEED, ItemID.GATE_KEY
        ]

    key_item_b = bytes(key_item_list)
    key_item_addr = ct_rom.space_manager.get_free_addr(len(key_item_b))
    ct_rom.seek(key_item_addr)
    ct_rom.write(key_item_b, freespace.FSWriteType.MARK_USED)

    # Warning!  The add_item routine has (possibly) been modified by
    #   the progressive items bit.  So we're jumping after that to right
    #   before the item is actually added.

    hook_rom_addr = 0xC1D00D
    # C1D00D  A2 00 00       LDX #$0000
    # C1D010  8E F9 AE       STX $AEF9
    # C1D013  9C FB AE       STZ $AEFB
    return_rom_addr = 0xC1D016
    # C1D016  BD 00 24       LDA $2400,X  <-- Start of read inventory loop

    gained_item_addr = 0xAEF7

    AM = inst.AddressingMode
    new_rt = [
        inst.LDX(0x0000, AM.IMM16),
        "loop_st",
        inst.LDA(byteops.to_rom_ptr(key_item_addr), AM.LNG_X),
        inst.CMP(gained_item_addr, AM.ABS),
        inst.BEQ("increment"),
        inst.INX(),
        inst.CPX(len(key_item_b), AM.IMM16),
        inst.BCC("loop_st"),
        inst.BRA("end"),
        "increment",
        inst.LDA(memory.Memory.KEY_ITEMS_OBTAINED, AM.LNG),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(memory.Memory.KEY_ITEMS_OBTAINED, AM.LNG),
        # Old stuff
        "end",
        inst.LDX(0x0000, AM.IMM16),
        inst.STZ(0xAEF9, AM.ABS),
        inst.STZ(0xAEFB, AM.ABS),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        new_rt,
        byteops.to_file_ptr(hook_rom_addr),
        ct_rom,
        byteops.to_file_ptr(return_rom_addr)
    )

def patch_progressive_items(ct_rom: ctrom.CTRom):
    """
    Add progression:
    - Pendant -> Charged Pendant
    - Masamune -> Grandleon
    """

    progression = [
        [ctenums.ItemID.PENDANT, ctenums.ItemID.PENDANT_CHARGE],
        [ctenums.ItemID.MASAMUNE_1, ctenums.ItemID.MASAMUNE_2],
        [ctenums.ItemID.RAINBOW_SHELL, ctenums.ItemID.PRISMSHARD],
        [ctenums.ItemID.C_TRIGGER, ctenums.ItemID.CLONE]
    ]
    # original addresses
    gained_item_id_addr = 0xAEF7
    empty_item_index_addr = 0xAEF9
    found_empty_item_index_addr = 0xAEFB

    # What we're adding.
    gained_item_index_addr = 0xAEF8
    found_gained_item_addr = 0xAEFA

    has_item_rt_addr = 0xCFE9  # 0xC1CFE9, but we only need the low bytes

    AM = inst.AddressingMode
    # (0x01FDD3, 0x01FFFF),  # junk, Reserved for Bank C1 required (div)
    # [0x01FDD3, 0x01FDD7) used for long div call
    # New: [0x01FDD7, 0x01FDDB) used for long has_item call.
    long_has_item_rt = assemble.ASMList = [
        inst.JSR(has_item_rt_addr, AM.ABS),
        inst.RTL()
    ]
    ct_rom.seek(0x01FDD7)
    ct_rom.write(assemble.assemble(long_has_item_rt))
    long_has_item_rom_addr = 0xC1FDD7

    # 16 bit X and Y.  8 bit A
    rt_list: assemble.ASMList = []
    for ind, route in enumerate(progression):
        item_reroute: assemble.ASMList = []
        if ind != 0:
            item_reroute.extend([f"block_{ind}"])

        if ind == len(progression) - 1:
            next_block_label = "add_item"
        else:
            next_block_label = f"block_{ind+1}"

        next_item_label = f"next_item_{ind}"
        item_reroute.extend(
            [
                inst.CPY(route[0], AM.IMM16),
                inst.BNE(next_block_label),
                inst.TYA(),
            ]
        )
        for item_ind, item in enumerate(route[:-1]):
            equip_checks = [
                [
                    inst.LDA(0x2629+0x50*ind, AM.ABS),
                    inst.CMP(item, AM.IMM8),
                    # inst.BEQ("next_item")
                    inst.BEQ(next_item_label)
                ] for ind in range(7)
            ]
            equip_check = [cmd for check in equip_checks for cmd in check]

            item_reroute.extend(
                equip_check +
                [
                    inst.JSL(long_has_item_rom_addr, AM.LNG),
                    inst.CMP(item, AM.IMM8),
                    # inst.BEQ("next_item"),
                    inst.BEQ(next_item_label),
                    inst.BRL("add_item"),
                    # inst.BNE("add_item"),
                    next_item_label,
                    inst.LDY(route[item_ind + 1], AM.IMM16),
                    inst.TYA(),
                    inst.STA(0x7F0200, AM.LNG),
                ]
            )
        item_reroute.append(inst.BRL("add_item"))
        rt_list.extend(item_reroute)

    rt_list.extend(
        [
            "add_item",
            inst.STY(gained_item_id_addr, AM.ABS),
            inst.CPY(0, AM.IMM16),
            inst.JMP(0xC1D00B, AM.LNG),
        ]
    )
    new_rt_bytes = assemble.assemble(rt_list)
    # new_rt_bytes = assemble.assemble(
    #     [
    #         inst.CPY(ctenums.ItemID.PENDANT, AM.IMM16),
    #         inst.BNE("add_item"),
    #         inst.TYA(),
    #         inst.JSR(has_item_rt_addr, AM.ABS),
    #         inst.CMP(ctenums.ItemID.PENDANT, AM.IMM8),
    #         inst.BNE("add_item"),
    #         inst.LDY(ctenums.ItemID.PENDANT_CHARGE, AM.IMM16),
    #         inst.TYA(),
    #         inst.STA(0x7F0200, AM.LNG),
    #         "add_item",
    #         inst.STY(gained_item_id_addr, AM.ABS),
    #         inst.CPY(0, AM.IMM16),
    #         inst.JMP(0xC1D00B, AM.LNG),
    #     ]
    # )

    rt_addr = ct_rom.space_manager.get_free_addr(len(new_rt_bytes))
    rt_rom_addr = byteops.to_rom_ptr(rt_addr)
    hook_bytes = inst.JMP(rt_rom_addr, AM.LNG).to_bytearray()
    hook_addr = 0x01D005

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_bytes)

    ct_rom.seek(rt_addr)
    ct_rom.write(new_rt_bytes, ctrom.freespace.FSWriteType.MARK_USED)


def patch_timegauge_alt(ct_rom: ctrom.CTRom):
    """
    Patch the time gauge to allow flags to gate time periods.  Also allow
    switching between the two dark ages versions if both are unlocked.
    """
    AM = inst.AddressingMode
    rt = assemble.ASMSnippet(
        [
            inst.REP(0x20),
            inst.LDA(1, AM.IMM16),
            inst.PHY(),
            "shift_loop",
            inst.CPY(0, AM.IMM16),
            inst.BEQ("after_shift_loop"),
            inst.ASL(mode=AM.NO_ARG),
            inst.DEY(),
            inst.DEY(),
            inst.BRA("shift_loop"),
            "after_shift_loop",
            inst.PLY(),
            inst.AND(memory.Memory.TIME_GAUGE_FLAGS, AM.LNG),
            inst.BEQ("skip_era"),
            inst.CPY(0xA, AM.IMM16),  # Y-value for Dark Ages
            inst.BNE("after_da_check"),
            inst.LDA(0x100, AM.ABS),
            inst.CMP(ctenums.LocID.OW_DARK_AGES, AM.IMM16),
            inst.BEQ("zeal_check"),
            inst.CMP(ctenums.LocID.OW_LAST_VILLAGE, AM.IMM16),
            inst.BEQ("zeal_check"),
            inst.BRA("after_da_check"),
            "zeal_check",
            inst.LDA(memory.Flags.HAS_ALGETTY_PORTAL.value.address, AM.LNG),
            inst.AND(memory.Flags.HAS_ALGETTY_PORTAL.value.bit, AM.IMM16),
            inst.BEQ("skip_era"),
            "after_da_check",
            inst.LDA(0x10, AM.DIR_24_Y),
            inst.RTL(),
            "skip_era",
            inst.LDA(0x0100, AM.ABS),
            inst.RTL(),
        ]
    )
    rt_bytes = rt.to_bytes()
    rt_addr = ct_rom.space_manager.get_free_addr(len(rt_bytes))

    rt_rom_addr = byteops.to_rom_ptr(rt_addr)
    hook = inst.JSL(rt_rom_addr, AM.LNG)
    hook_addr = 0x027475

    ct_rom.seek(hook_addr)
    ct_rom.write(hook.to_bytearray())

    ct_rom.seek(rt_addr)
    ct_rom.write(rt_bytes, ctrom.freespace.FSWriteType.MARK_USED)

    # Also patch the check for loading normal DA or Last Village.
    # When on the normal DA map, make travel to LV possible.
    map_check_bytes = assemble.assemble(
        [
            inst.LDA(0x100, AM.ABS),
            inst.CMP(0xF4, AM.IMM8),
            inst.BNE(3),
        ]
    )

    ct_rom.seek(0x027460)
    ct_rom.write(map_check_bytes)

    # The other check for the dark ages is slightly different
    map_check_bytes2 = assemble.assemble(
        [
            inst.LDA(0x100, AM.ABS),
            inst.CMP(0xF6, AM.IMM8),
            inst.BNE(3),
        ]
    )

    ct_rom.seek(0x027480)
    ct_rom.write(map_check_bytes2)


def patch_timegauge(ct_rom: ctrom.CTRom):
    """
    Change the time gauge's behavior to read available time periods from
    $7E2881 - $7E288D.
    """
    FSW = ctrom.freespace.FSWriteType

    rt = bytes.fromhex(
        "DA"  # PHX
        "A2 00 00"  # LDX #$0000
        "C2 20"  # REP #$20
        "B7 10"  # LDA [$10], Y
        "DF 81 28 7E"  # CMP $7E2881, X
        "D0 02"  # BNE #$02
        "FA"  # PLX
        "6B"  # RTL
        "E8"  # INX
        "E8"  # INX
        "E0 0E 00"  # CPX #$000E
        "90 F1"  # BCC #$F1  [-0x0F]
        "AF 00 01 7E"  # LDA $7E0100  [Should hold current location]
        "FA"  # PLX
        "6B"  # RTL
    )

    rt_addr = ct_rom.space_manager.get_free_addr(len(rt))
    ct_rom.seek(rt_addr)
    ct_rom.write(rt, FSW.MARK_USED)

    rt_addr = byteops.to_rom_ptr(rt_addr)
    rt_addr_b = rt_addr.to_bytes(3, "little")
    hook = bytes.fromhex("22" + rt_addr_b.hex())
    ct_rom.seek(0x027475)
    ct_rom.write(hook)


def apply_misc_patches(ct_rom: ctrom.CTRom):
    """
    Apply short patches which require no JSL/freespace allocation

    List of patches:
    - Double HP on Greendream.
    - Remove Grandleon restriction on GranddDream (Gold Rock tech)
    - Remove Active/Wait screen from some rename screens
    """

    # Double the HP given to a PC revived by Greendream
    ct_rom.seek(0x01B324)
    ct_rom.write(b"\x0A")  # Change from 5

    # Remove Grandleon restriction on GrandDream (Gold Rock tech)
    # Overwrite CMP #$42, BNE XX with NOP NOP NOP NOP.
    # 0x42 is the Grandleon's item id.
    ct_rom.seek(0x010FED)
    ct_rom.write(b"\xEA" * 4)

    # Remove (some) Active/Wait screens
    # I'm not sure whether this is needed or not.  After the first name screen,
    # 0x7E299F should stay nonzero, and the ORA that this overwrites only makes
    # it more nonzero...
    ct_rom.seek(0x02E1ED)
    ct_rom.write(b"\xEA\xEA")  # Overwrites ORA $71


def set_storyline_thresholds(ct_rom: ctrom.CTRom):
    """
    Change storyline values which allow certain actions to be taken.
    """

    # 001994	001994	DATA	N
    # Storyline value for location party exchange
    # Jets changes 0x49 to 0x01
    ct_rom.seek(0x001994)
    ct_rom.write(b"\x01")

    # 022D96	022D96	DATA	N
    # Storyline value for Black Omen on overworld map
    # Change from 0xD4 to 0x01 (still gated by flags)
    ct_rom.seek(0x022D96)
    ct_rom.write(b"\x01")

    # 02360C	02360C	DATA	N
    # Storyline value for overworld party exchange menu
    # Change from 0x49 to 0x00
    ct_rom.seek(0x02360C)
    ct_rom.write(b"\x00")

    # 3FF81D	3FF81D	DATA	N
    # Storyline value for equip menu scroll bar	2006.12.20
    ct_rom.seek(0x3FF81D)
    ct_rom.write(b"\00")

    # Now handled by new time gauge patch
    # 027464	027464	DATA	N
    # Storyline value for Epoch time gauge 1F4->1F6 overworld map change
    # (Check 1)
    # Change from 0xCC to 0x10
    # ct_rom.seek(0x027464)
    # ct_rom.write(b"\x10")

    # 027484	027484	DATA	N
    # Storyline value for Epoch time gauge 1F4->1F6 overworld map change
    # (Check 2)	2007.01.15
    # Also changes 0xCC to 0x10
    # ct_rom.seek(0x027484)
    # ct_rom.write(b"\x10")


def alter_event_or_operation(ct_rom: ctrom.CTRom):
    """
    Change the useless val | mem != 0 to val & mem == 0.
    This allows us to quickly check if flags are NOT set.
    """
    ct_rom.seek(0x0064C9)
    ct_rom.write(b"\x25")
    ct_rom.seek(1, 1)
    ct_rom.write(b"\xF0")


def patch_blackbird(ct_rom: ctrom.CTRom):
    """
    Update the game so that any character can be disabled in battle during the
    Blackbird sequence.
    - Patch the pre-battle code that disables a character.
    - Patch the menu code that re-enables a character when a weapon is equipped.
    """

    # Pre-battle code @ 0x0FFBC3.
    # [CCFBC3]  LDY  # $0002
    # *************************************************
    #   [CCFBC6]  LDA $2980,Y
    #   [CCFBC9]  AND #$07
    #     This is assuming no 0x80 missing characters
    #   [CCFBCB]  TAX
    #   [CCFBCC]  LDA $7F00B4,X
    # *************************************************
    # Replacing this region.  0xA bytes with a 6 byte hook (JSL + BRA).  So we have
    # to do a four byte jump after.
    #   [CCFBD0]  STA $A09B,Y
    #   [CCFBD3]  DEY
    #     This loop just sets $A09B, Y
    # [CCFBD4]  BPL $CFFBC6
    # [CCFBD6]  LDA $7F00BA
    # [CCFBDA]  AND #$02
    # [CCFBDC]  EOR #$02
    # [CCFBDE]  STA $A0A7

    AM = inst.AddressingMode
    routine: assemble.ASMList = [
        inst.LDA(0x2980, AM.ABS_Y),
        inst.BMI("END"),
        inst.AND(7, AM.IMM8),
        inst.TAX(),
        inst.LDA(0xCCF9FB, AM.LNG_X),
        inst.AND(memory.Memory.BLACKBIRD_GEAR_STATUS, AM.LNG),
        "END",
        inst.RTL(),
    ]
    routine_b = assemble.assemble(routine)

    routine_addr = ct_rom.space_manager.get_free_addr(len(routine_b), 0x410000)

    hook_addr = 0x0FFBC6
    hook: assemble.ASMList = [
        inst.JSL(byteops.to_rom_ptr(byteops.to_rom_ptr(routine_addr))),
        inst.BRA("END"),
        inst.NOP(),
        inst.NOP(),
        inst.NOP(),
        inst.NOP(),
        "END",
    ]
    hook_b = assemble.assemble(hook)

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_b)

    ct_rom.seek(routine_addr)
    ct_rom.write(routine_b, ctrom.freespace.FSWriteType.MARK_USED)

    # Now handle the code that re-enables a character if they equip a weapon.
    #   PHP
    #   SEP #$30
    #   LDA $0077
    #   BNE $C29D15
    #   LDX $0412
    #   LDA $0D5F,X   <--- This ends up loading PC-index
    #   *********** @ 0x029D0A below
    #   CMP #$06
    #     The comparison to 6 is needed to avoid setting $7F00B4 + 6 = 0x7F00BA.
    #     We don't have to worry about it.
    #   BCS $C29D15  [To: END]
    #   TAX
    #   LDA #$00
    #   STA $7F00B4,X
    #   *********** @0x029D15 below (0xB bytes routine)
    #   PLP  [END]
    #   RTS
    hook_addr, hook_end = 0x029D0A, 0x029D15
    block_len = hook_end - hook_addr

    routine = [
        inst.TAX(),
        inst.LDA(0xCCF9FB, AM.LNG_X),
        inst.EOR(0xFF, AM.IMM8),
        inst.AND(memory.Memory.BLACKBIRD_GEAR_STATUS, AM.LNG),
        inst.STA(memory.Memory.BLACKBIRD_GEAR_STATUS, AM.LNG),
        inst.RTL(),
    ]
    routine_b = assemble.assemble(routine)
    routine_addr = ct_rom.space_manager.get_free_addr(len(routine_b), 0x410000)
    ct_rom.seek(routine_addr)
    ct_rom.write(routine_b, ctrom.freespace.FSWriteType.MARK_USED)

    hook: assemble.ASMList = [
        inst.JSL(byteops.to_rom_ptr(byteops.to_rom_ptr(routine_addr))),
        inst.BRA("END"),
    ]
    num_nops = block_len - 6
    hook = hook + num_nops * [inst.NOP()] + ["END"]
    hook_b = assemble.assemble(hook)

    if len(hook_b) != block_len:
        raise ValueError

    ct_rom.seek(hook_addr)
    ct_rom.write(hook_b)


def apply_fast_ow_movement(ct_rom: ctrom.CTRom,
                           autorun: bool = False,
                           epoch_autorun: bool = False):
    """
    Apply fast overworld movement.
    """

    ct_rom = ct_rom
    space_man = ct_rom.space_manager

    # Subtracting 1 from Y-coord when up is pressed.
    # C23619  A9 FF FF       LDA #$FFFF      # The # pixels to change per frame
    # C2361C  9D 20 00       STA $0020,X
    # C2361F  9E 1C 00       STZ $001C,X     # Zero out a counter for storing movement
    # C23622  E2 20          SEP #$20

    hooks = [0x023619, 0x023636, 0x023653, 0x023670]
    is_pos_list = [False, True, False, True]
    is_y_list = [True, True, False, False]

    controller_1_button_addr = 0x7E00F2 & 0x00FFFF
    dash_button_mask_addr = 0x7E2996
    y_counter_addr = 0x0020
    x_counter_addr = 0x001C

    AM = inst.AddressingMode

    for hook_addr, is_pos, is_y in zip(hooks, is_pos_list, is_y_list):
        if is_pos:
            fast_move, slow_move = 2, 1
        else:
            fast_move, slow_move = 0xFFFE, 0xFFFF

        if is_y:
            zero_addr, store_addr = x_counter_addr, y_counter_addr
        else:
            zero_addr, store_addr = y_counter_addr, x_counter_addr

        if autorun:
            branch_cmd = inst.BNE("slow_move")
        else:
            branch_cmd = inst.BEQ("slow_move")

        routine = [
            inst.LDA(dash_button_mask_addr, AM.LNG),
            inst.AND(0x00FF, AM.IMM16),
            inst.BIT(controller_1_button_addr, AM.ABS),
            branch_cmd,
            inst.LDA(fast_move, AM.IMM16),
            inst.BRA("end"),
            "slow_move",
            inst.LDA(slow_move, AM.IMM16),
            "end",
            inst.STA(store_addr, AM.ABS_X),
            inst.STZ(zero_addr, AM.ABS_X),
            inst.JMP(byteops.to_rom_ptr(hook_addr+9), AM.LNG)
        ]

        routine_b = assemble.assemble(routine)
        routine_addr = space_man.get_free_addr(len(routine_b))

        hook = [
            inst.JMP(byteops.to_rom_ptr(routine_addr), AM.LNG),
        ] + [inst.NOP()]*5
        hook_b = assemble.assemble(hook)

        ct_rom.seek(hook_addr)
        ct_rom.write(hook_b)

        ct_rom.seek(routine_addr)
        ct_rom.write(routine_b, freespace.FSWriteType.MARK_USED)

    npc_x_hook_addr = 0x024148
    npc_x_return_addr = 0x024151
    npc_x_routine = [
        inst.LDA(dash_button_mask_addr, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.BIT(controller_1_button_addr, AM.ABS),
        inst.BNE("end") if autorun else inst.BEQ("end"),
        inst.ASL(0x1C, AM.ABS_X),
        "end",
        inst.STZ(0x1A, AM.ABS_X),
        inst.STZ(0x20, AM.ABS_X),
        inst.STZ(0x1E, AM.ABS_X),
        inst.JMP(byteops.to_rom_ptr(npc_x_return_addr), AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(npc_x_routine, npc_x_hook_addr, ct_rom, npc_x_return_addr)

    npc_y_hook_addr = 0x024162
    npc_y_return_addr = 0x02416B
    npc_y_routine = [
        inst.LDA(dash_button_mask_addr, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.BIT(controller_1_button_addr, AM.ABS),
        inst.BNE("end") if autorun else inst.BEQ("end"),
        inst.ASL(0x20, AM.ABS_X),
        "end",
        inst.STZ(0x1E, AM.ABS_X),
        inst.STZ(0x1C, AM.ABS_X),
        inst.STZ(0x1A, AM.ABS_X),
        inst.JMP(byteops.to_rom_ptr(npc_y_return_addr), AM.LNG)
    ]
    asmpatcher.apply_jmp_patch(npc_y_routine, npc_y_hook_addr, ct_rom, npc_y_return_addr)

    epoch_hook_addr = 0x024628
    x_coord_load_addr = 0xC24899
    y_coord_load_addr = x_coord_load_addr+2
    return_addr = 0xC24636

    if epoch_autorun:
        branch_cmd = inst.BNE("slow_move")
    else:
        branch_cmd = inst.BEQ("slow_move")

    epoch_routine = [
        inst.LDA(dash_button_mask_addr, AM.LNG),
        inst.AND(0x00FF, AM.IMM16),
        inst.BIT(controller_1_button_addr, AM.ABS),
        branch_cmd,
        inst.LDA(x_coord_load_addr, AM.LNG_X),
        inst.ASL(mode=AM.NO_ARG),
        inst.STA(x_counter_addr, AM.ABS_Y),
        inst.LDA(y_coord_load_addr, AM.LNG_X),
        inst.ASL(mode=AM.NO_ARG),
        inst.STA(y_counter_addr, AM.ABS_Y),
        inst.BRA("end"),
        "slow_move",
        inst.LDA(x_coord_load_addr, AM.LNG_X),
        inst.STA(x_counter_addr, AM.ABS_Y),
        inst.LDA(y_coord_load_addr, AM.LNG_X),
        inst.STA(y_counter_addr, AM.ABS_Y),
        inst.BRA("end"),
        "end",
        inst.JMP(return_addr, AM.LNG)
    ]

    epoch_routine_b = assemble.assemble(epoch_routine)
    epoch_routine_addr = ct_rom.space_manager.get_free_addr(len(epoch_routine_b))

    epoch_hook = [
        inst.JMP(byteops.to_rom_ptr(epoch_routine_addr), AM.LNG),
    ] + [inst.NOP()] * 10
    epoch_hook_b = assemble.assemble(epoch_hook)

    ct_rom.seek(epoch_hook_addr)
    ct_rom.write(epoch_hook_b)

    ct_rom.seek(epoch_routine_addr)
    ct_rom.write(epoch_routine_b, freespace.FSWriteType.MARK_USED)

    # When getting off of Epoch/Dactyl or first loading a map, there
    # is block of code that sets following PC's coordinates to PC1's.
    # If PC1 moves 1 px and then starts running, the other PCs get off
    # The tile grid and don't get back on it because they're moving 2 px at
    # a time.


    # C23C03  C2 20          REP #$20
    hook_rom_addr = 0xC23C05
    # C23C05  AD 83 02       LDA $0283
    # C23C08  9D 14 00       STA $0014,X
    return_rom_addr = 0xC23C0B
    # C23C0B  9E 12 00       STZ $0012,X

    round_rt = [
        inst.LDA(0x0283, AM.ABS),
        inst.STA(0x0014, AM.ABS_X),
        inst.AND(0x0007, AM.IMM16),
        inst.CMP(0x04, AM.IMM16),
        inst.BCS("round_up"),
        inst.LDA(0x0283, AM.ABS),
        inst.AND(0xFFF8, AM.IMM16),
        inst.BRA("end"),
        "round_up",
        inst.LDA(0x0283, AM.ABS),
        inst.AND(0xFFF8, AM.IMM16),
        inst.CLC(),
        inst.ADC(0x0008, AM.IMM16),
        "end",
        inst.STA(0x0014, AM.ABS_X),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        round_rt, byteops.to_file_ptr(hook_rom_addr),
        ct_rom, byteops.to_file_ptr(return_rom_addr)
    )

    # Same for y-coord
    hook_rom_addr = 0xC23C0E
    # C23C0E  AD 85 02       LDA $0285
    # C23C11  9D 18 00       STA $0018,X
    return_rom_addr = 0xC23C14
    # C23C14  9E 16 00       STZ $0016,X

    round_rt = [
        inst.LDA(0x0285, AM.ABS),
        inst.STA(0x0018, AM.ABS_X),
        inst.AND(0x0007, AM.IMM16),
        inst.CMP(0x04, AM.IMM16),
        inst.BCS("round_up"),
        inst.LDA(0x0285, AM.ABS),
        inst.AND(0xFFF8, AM.IMM16),
        inst.BRA("end"),
        "round_up",
        inst.LDA(0x0285, AM.ABS),
        inst.AND(0xFFF8, AM.IMM16),
        inst.CLC(),
        inst.ADC(0x0008, AM.IMM16),
        "end",
        inst.STA(0x0018, AM.ABS_X),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        round_rt, byteops.to_file_ptr(hook_rom_addr),
        ct_rom, byteops.to_file_ptr(return_rom_addr)
    )

def add_boss_counter_to_rewards(
        ct_rom: ctrom.CTRom,
        boss_list: Optional[list[ctenums.EnemyID]] = None
):
    """
    When an enemy is defeated, increment the boss count.
    """

    if boss_list is None:
        EID = ctenums.EnemyID
        boss_list = [
            # EID.ATROPOS_XR,
            EID.BLACKTYRANO, EID.DALTON_PLUS,
            EID.TANK_HEAD, EID.ELDER_SPAWN_HEAD, EID.FLEA,
            EID.MASA_MUNE,
            # EID.FLEA_PLUS,
            EID.MEGA_MUTANT_HEAD,
            EID.GIGA_GAIA_HEAD, EID.GIGA_MUTANT_HEAD, EID.HECKRAN,
            EID.LAVOS_SPAWN_HEAD, EID.MAGUS, EID.MOTHERBRAIN,
            EID.MUD_IMP, EID.NIZBEL, EID.NIZBEL_II, EID.RETINITE_BOTTOM,
            # EID.R_SERIES,
            EID.RUST_TYRANO, EID.SLASH_SWORD,
            EID.SON_OF_SUN_EYE,
            # EID.SUPER_SLASH,
            EID.TERRA_MUTANT_HEAD, EID.GOLEM, EID.GOLEM_BOSS,
            EID.YAKRA, EID.YAKRA_XIII, EID.ZOMBOR_BOTTOM,
            EID.GREAT_OZZIE, EID.ZEAL, EID.GUARDIAN,
            EID.MAGUS_NORTH_CAPE
        ]

    boss_list_b = bytes(boss_list)
    boss_list_addr = ct_rom.space_manager.get_free_addr(len(boss_list_b))
    ct_rom.seek(boss_list_addr)
    ct_rom.write(boss_list_b, freespace.FSWriteType.MARK_USED)


    # This part of the routine loads the enemy's id and compares to FF to
    # skip rewards.  We will hook here an compare the id to the boss list.
    hook_rom_addr = 0xFDABAF
    # FDABAF  BD 0A AF       LDA $AF0A,X
    # FDABB2  C9 FF          CMP #$FF
    return_rom_addr = 0xFDABB4
    # FDABB4  D0 03          BNE $FDABB9

    AM = inst.AddressingMode
    new_rt: assemble.ASMList = [
        inst.LDA(0xAF0A, AM.ABS_X),
        inst.LDX(0x0000, AM.IMM16),
        "loop_st",
        inst.CMP(byteops.to_rom_ptr(boss_list_addr), AM.LNG_X),
        inst.BEQ("found_boss"),
        inst.INX(),
        inst.CPX(len(boss_list_b), AM.IMM16),
        inst.BCC("loop_st"),
        inst.BRA("end"),
        "found_boss",
        inst.TAX(),
        inst.LDA(memory.Memory.BOSSES_DEFEATED, AM.LNG),
        inst.INC(mode=AM.NO_ARG),
        inst.STA(memory.Memory.BOSSES_DEFEATED, AM.LNG),
        inst.TXA(),
        "end",
        inst.CMP(0xFF, AM.IMM8),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        new_rt,
        byteops.to_file_ptr(hook_rom_addr),
        ct_rom,
        byteops.to_file_ptr(return_rom_addr)
    )


def base_patch_ct_rom(ct_rom: ctrom.CTRom):
    """Just patch the ct_rom.  No Scripts or anything."""
    ct_rom.make_exhirom()

    mark_initial_free_space(ct_rom)
    decompressed_graphics.apply_full_patch(ct_rom)
    # apply_fast_ow_movement(ct_rom)  # Moved -- Uses settings for autorun
    patch_blackbird(ct_rom)
    patch_timegauge_alt(ct_rom)
    patch_progressive_items(ct_rom)
    patch_division(ct_rom)
    add_key_item_count(ct_rom)
    alter_event_or_operation(ct_rom)
    set_storyline_thresholds(ct_rom)
    add_boss_counter_to_rewards(ct_rom)
    chesttext.add_get_desc_char(ct_rom, 0)
    modifyitems.normalize_hp_accessories(ct_rom)
    modifyitems.normalize_mp_accessories(ct_rom)
    modifyitems.add_crit_accessories(ct_rom)

    apply_mauron_player_tech_patch(ct_rom)
    patch_max_tech_count(ct_rom)
    expand_eventcommands(ct_rom)

    # Debug
    ct_rom.seek(0x01FFFF)
    ct_rom.write(b"\x01")

    ct_rom.seek(0x02E1F0)  # Always active/wait on first name
    ct_rom.write(b"\xEA\xEA")

    # Out of Party XP
    nop_st = 0x01FA26
    # nop_end = 0x01FA41
    nop_end = 0x1FA4A

    nop_opcode = inst.NOP().opcode
    payload = nop_opcode.to_bytes() * (nop_end - nop_st)
    ct_rom.seek(nop_st)
    ct_rom.write(payload)

    AM = inst.AddressingMode
    new_level_rt: assemble.ASMList = [
        inst.LDX(0xB285, AM.ABS),
        inst.JSR(0xF90B, AM.ABS),
        "levelup",
        inst.JSR(0xF623, AM.ABS),
        inst.LDA(0xB28B, AM.ABS),
        inst.BEQ("levelup"),
    ]
    payload = assemble.assemble(new_level_rt)
    ct_rom.seek(nop_end - len(payload))
    ct_rom.write(payload)

    # Zombor dance party
    ct_rom.seek(0x0DC087)
    ct_rom.write(b'\x10')  # Straight line to coords command


def patch_max_tech_count(ct_rom: ctrom.CTRom):
    """Allow more than 0x7F techs on the rom."""

    # One issue is when building the battle menu.  The game wants to test if
    # a value is 0xFF but instead checks if a value is negative so it catches
    # 0x80 and up.

    # $CC/E75B BF 95 F3 CC LDA $CCF395,x
    # $CC/E75F 85 80       STA $80
    # $CC/E761 BF 96 F3 CC LDA $CCF396,x
    # $CC/E765 85 81       STA $81
    # $CC/E767 A6 80       LDX $80
    # $CC/E769 BD C6 1A    LDA $1AC6,x
    # $CC/E76C 30 05       BMI $05    [$E773]
    # $CC/E76E A9 01       LDA #$01
    # $CC/E770 99 25 9F    STA $9F25,y
    # $CC/E773 BD FE 1A    LDA $1AFE,x  # Trip tech spot of menu
    # $CC/E776 30 05       BMI $05      # should be CMP #$FF, BEQ
    # $CC/E778 A9 01       LDA #$01
    # $CC/E77A 99 28 9F    STA $9F28,y
    # $CC/E77D 88          DEY          # Should return here

    hook_pos = 0x0CE75B
    return_pos = 0x0CE77D
    return_rom_pos = byteops.to_rom_ptr(return_pos)

    AM = inst.AddressingMode
    rt = [
        inst.LDA(0xCCF395, AM.LNG_X),
        inst.STA(0x80, AM.DIR),
        inst.LDA(0xCCF396, AM.LNG_X),
        inst.STA(0x81, AM.DIR),
        inst.LDX(0x80, AM.DIR),
        inst.LDA(0x1AC6, AM.ABS_X),
        inst.BMI("triple"),
        inst.LDA(0x01, AM.IMM8),
        inst.STA(0x9F25, AM.ABS_Y),
        "triple",
        inst.LDA(0x1AFE, AM.ABS_X),
        inst.CMP(0xFF, AM.IMM8),
        inst.BEQ("end"),
        inst.LDA(0x01, AM.IMM8),
        inst.STA(0x9F28, AM.ABS_Y),
        "end",
        inst.JMP(0xCCE77D, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(rt, hook_pos, ct_rom, hint=0x410000)

    # Same story as above
    #     $CC/E887 BF 95 F3 CC LDA $CCF395,x
    #     $CC/E88B 85 84       STA $84
    #     $CC/E88D BF 96 F3 CC LDA $CCF396,x
    #     $CC/E891 85 85       STA $85
    #     $CC/E893 A6 84       LDX $84
    #     $CC/E895 BD FE 1A    LDA $1AFE,x
    #     $CC/E898 99 D0 94    STA $94D0,y
    #     $CC/E89B 30 05       BMI $05    [$E8A2]
    #     $CC/E89D A9 12       LDA #$12
    #     $CC/E89F 99 51 95    STA $9551,y
    #     $CC/E8A2 E6 83       INC $83

    hook_addr = 0x0CE887
    return_rom_addr = 0xCCE8A2
    return_addr = byteops.to_file_ptr(return_rom_addr)
    rt2 = [
        inst.LDA(0xCCF395, AM.LNG_X),
        inst.STA(0x84, AM.DIR),
        inst.LDA(0xCCF396, AM.LNG_X),
        inst.STA(0x85, AM.DIR),
        inst.LDX(0x84, AM.DIR),
        inst.LDA(0x1AFE, AM.ABS_X),
        inst.STA(0x94D0, AM.ABS_Y),
        inst.CMP(0xFF, AM.IMM8),
        inst.BEQ("end"),
        inst.LDA(0x12, AM.IMM8),
        inst.STA(0x9551, AM.ABS_Y),
        "end",
        inst.JMP(return_rom_addr, AM.LNG)
    ]



    asmpatcher.apply_jmp_patch(rt2, hook_addr, ct_rom, return_addr, hint=0x410000)

    # $C2/BD9A E2 20       SEP #$20
    # $C2/BD9C AD 4C 0F    LDA $0F4C
    # $C2/BD9F 30 05       BMI $05    [$BDA6]  <-- change to BEQ
    hook_addr = 0x02BD9A
    return_rom_addr = 0xC2BD9F
    return_addr = byteops.to_file_ptr(return_rom_addr)
    rt3 = [
        inst.SEP(0x20),
        inst.LDA(0x0F4C, AM.ABS),
        inst.CMP(0xFF, AM.IMM8),
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    ct_rom.getbuffer()[return_addr] = inst.BEQ(5, AM.REL_8).opcode
    asmpatcher.apply_jmp_patch(rt3, hook_addr, ct_rom, return_addr)

    # There's a very weird bug where if there are too many techs the menu
    # reqs will write over graphics pointers in memory.  We are going to
    # expand the list and shift it backwards.
    #
    # Set the start of the menu reqs 7*0x40 back.  Somehow this is all free
    # at the time we need it to be.

    rom = ct_rom.getbuffer()
    # $FF/F8C1 A9 40 16    LDA #$1640
    rom[0x3FF8C2:0x3FF8C2 + 2] = int.to_bytes(0x1480, 2, "little")

    # Originally pc-id was obtained as 0xID00 and then LSR'd twice to
    # get an index into the 0x40 byte range for each PC.  We're doubling it
    # so remove one LSR.
    # $FF/F8E9 4A          LSR A
    rom[0x3FF8E9] = 0xEA  # NOP

    # $FF/F8DE 4A          LSR A
    rom[0x3FF8DE] = 0xEA

    # $FF/F941 4A          LSR A
    rom[0x3FF941] = 0xEA

    # Now when reading.
    # $C2/BC3A 4A          LSR A
    rom[0x02BC3A] = 0xEA  # NOP

    # $C2/BC46 BD 07 16    LDA $1607,x[$7E:1640]   A:0000 X:0039 Y:0001
    # Note X has an absolute tech_id in it, so we need to go 0x39 spots
    # before the new start (0x1480)
    rom[0x02BC47:0x02BC47 + 2] = int.to_bytes(0x1480 - 0x39, 2, "little")

    # Last random thing:  Junk data in the range that could be used for learning techs
    # C29583  A2 00 00       LDX #$0000
    # C29586  A0 00 26       LDY #$2600
    # C29589  A9 7F 02       LDA #$027F
    # C2958C  54 7E CC       MVN $CC,$7E
    # C2958F  9C 53 2C       STZ $2C53

    # We really only need the first 7*50 + 0xE bytes (next tech level, techs learned)
    # The rest are already zeroed out
    # There's some writing to this range during attract mode.
    # There may be a better way, but we're just going to copy an extra 0x10 bytes
    rom[0x02958A:0x02958A+2] = int.to_bytes(7*0x50 + 0x0D + 0x10, 2, "little")


# Notes on making eventcommands
# Upon entering the command's code we have:
# - Y (16-bit) has the offset (+0x7F2000) to the current command
# - X (16-bit) has no worthwhile data (pointer for a JSR)
# - A (8-bit) has no worthwhile data
# - DBR is set to 0x00
# - DP is set to 0x0100 (no TDCs to clear A)
# Upon returning, the command should
# - Put the offset to the next command in X (even though it comes in through Y)
# - Set the carry if execution should continue to the next command
# - Clear the carry to move on to the next object
# It looks like $CD, $CE, $CF are valid as temporary values (used by assignment).
# Also, $C7 is used as a temp value for if_is_recruited.
# The Geiger DB indicates that $D9 is also for temporary values

def get_set_techlevel_event_cmd_asm() -> assemble.ASMList:
    """
    Returns assembly for a eventcommand that sets a PC's techlevel.
    - Command ID is TBD
    - Call format is XX pc_id tech_level
    """
    tech_level_start = 0x7E2830
    techs_learned_start = tech_level_start + 7
    tp_next_ram_offset = 0x7E262D
    tp_thresh_rom_start = 0xCC26FA
    temp_tp_req = 0xCD
    temp_tech_level = 0xCF
    temp_pc_id = 0xD9

    slow_mult_rom_addr = 0xC1FDBF

    AM = inst.AddressingMode
    SR = inst.SpecialRegister
    rt: assemble.ASMList = [
        inst.INY(),
        inst.TYX(),
        inst.LDA(0x7F2001, AM.LNG_X),  # pc_id
        inst.AND(0x07, AM.IMM8),
        inst.STA(temp_pc_id, AM.DIR),
        inst.INY(),
        inst.LDA(0x7F2001, AM.LNG_X),
        inst.BIT(0x80, AM.IMM8),
        inst.BEQ("not_from_mem"),
        inst.LDA(0x00, AM.IMM8), inst.XBA(),
        inst.LDA(0x7F2002, AM.LNG_X),
        inst.REP(0x20),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(0x7F0200, AM.LNG_X),
        inst.BRA("test_max_tech_level"),
        "not_from_mem",
        inst.LDA(0x7F2002, AM.LNG_X),
        "test_max_tech_level",
        inst.INY(),
        inst.CMP(0x08, AM.IMM8),
        inst.BCC("skip_max"),
        inst.LDA(0x08, AM.IMM8),
        inst.STA(temp_tech_level, AM.DIR),
        inst.REP(0x20),
        inst.LDA(0xFFFF, AM.IMM16),
        inst.STA(temp_tp_req, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.BRA("after_tp_next"),
        "skip_max",
        inst.STA(temp_tech_level, AM.DIR),
        inst.LDA(temp_pc_id, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.CLC(),
        inst.ADC(temp_tech_level, AM.DIR),  # 0x10*pc_id + tech_lv
        inst.ADC(temp_tech_level, AM.DIR),  # 0x10*pc_id + 2*tech_lv
        inst.REP(0x20),
        inst.AND(0x00FF, AM.IMM16),
        inst.TAX(),
        # inst.REP(0x20),
        inst.LDA(tp_thresh_rom_start, AM.LNG_X),
        inst.STA(temp_tp_req, AM.DIR),
        "after_tp_next",
        inst.LDA(temp_pc_id, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.STA(0x28, AM.ABS),  # DP is weird here
        inst.LDA(0x0050, AM.IMM16),
        inst.STA(0x2A, AM.ABS),
        inst.PHD(),
        inst.PEA(0x0000, AM.IMM16),
        inst.PLD(),
        inst.JSL(slow_mult_rom_addr),
        inst.PLD(),
        inst.REP(0x20),
        inst.LDA(0x2C, AM.ABS),
        # inst.SEP(0x20),
        # inst.LDA(temp_pc_id, AM.DIR),
        # inst.STA(SR.M7A, AM.ABS),
        # inst.STZ(SR.M7A, AM.ABS),
        # inst.LDA(0x50, AM.IMM8),
        # inst.STA(SR.M7B, AM.ABS),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.ABS),
        inst.TAX(),
        inst.LDA(temp_tp_req, AM.DIR),
        inst.STA(tp_next_ram_offset, AM.LNG_X),
        inst.LDA(temp_pc_id, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(temp_tech_level, AM.DIR),
        inst.STA(tech_level_start, AM.LNG_X),
        inst.SEC(),
        inst.LDA(0x08, AM.IMM8),
        inst.SBC(temp_tech_level, AM.DIR),
        inst.STA(temp_tech_level, AM.DIR),
        inst.BEQ("max_level"),
        inst.LDA(0xFF, AM.IMM8),
        "loop_st",
        inst.ASL(mode=AM.NO_ARG),
        inst.DEC(temp_tech_level, AM.DIR),
        inst.BNE("loop_st"),
        inst.BRA("end"),
        "max_level",
        inst.LDA(0xFF, AM.IMM8),
        "end",
        inst.STA(techs_learned_start, AM.LNG_X),
        inst.SEC(),
        inst.TYX(),
        inst.RTL()
    ]

    return rt


def get_set_level_event_cmd_asm(
        hp_table_rom_start: int,
        mp_table_rom_start: int
) -> assemble.ASMList:
    """
    Gets aasembly for an event command which sets a PC's level.
    - Set current/max HP.  Requires knowing Lv1 HP
    - Set current/max MP.  Requires knowing Lv1 MP
    - Set current stats (Pow, Stm, Mag, Hit, Evd, Mdf, Lev)
    Command format is XX PC_ID NEW_LEVEL
    """

    temp_pc_id_addr = 0xCF
    temp_addr = 0xCD  # Will also use 0xCE
    temp_target_level = 0xD9

    cur_hp_offset = 3
    max_hp_offset = 5
    cur_mp_offset = 7
    max_mp_offset = 9
    level_offset = 0x12
    xp_next_offset = 0x2B

    stat_offset_rom_start = 0xFDA83B
    xp_next_rom_start = 0xCC2632
    slow_mult_rom_addr = 0xC1FDBF

    AM = inst.AddressingMode
    SR = inst.SpecialRegister
    store_args_rt = [
        inst.INY(),
        inst.TYX(),
        inst.LDA(0x7F2001, AM.LNG_X),
        inst.AND(0x7F, AM.IMM8),
        inst.STA(temp_pc_id_addr, AM.DIR),
        inst.INY(),
        inst.LDA(0x7F2001, AM.LNG_X),
        inst.BIT(0x80, AM.IMM8),
        inst.BEQ("not_from_mem"),
        inst.LDA(0x00, AM.IMM8), inst.XBA(),
        inst.LDA(0x7F2002, AM.LNG_X),
        inst.REP(0x20),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.SEP(0x20),
        inst.LDA(0x7F0200, AM.LNG_X),
        inst.BRA("store_level"),
        "not_from_mem",
        inst.LDA(0x7F2002, AM.LNG_X),
        "store_level",  # Maybe check for max level?
        inst.INY(),
        inst.STA(temp_target_level, AM.DIR),
        inst.STZ(temp_target_level+1, AM.DIR)
    ]

    set_hp_rt = [
        # Get the HP value from the table
        inst.REP(0x20),
        inst.LDA(temp_pc_id_addr, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.PHD(),
        inst.PEA(0x0000, AM.IMM16),
        inst.PLD(),
        inst.STA(0x2A, AM.DIR),
        inst.LDA(200, AM.IMM16),
        inst.STA(0x28, AM.DIR),
        inst.JSL(slow_mult_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(0x2C, AM.DIR),
        inst.PLD(),
        # inst.LDA(200, AM.IMM8),
        # inst.STA(SR.M7A, AM.ABS),
        # inst.STZ(SR.M7A, AM.ABS),
        # inst.LDA(temp_pc_id_addr, AM.DIR),
        # inst.STA(SR.M7B, AM.ABS),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.ABS),
        inst.CLC(),
        inst.ADC(temp_target_level, AM.DIR),
        inst.ADC(temp_target_level, AM.DIR),
        inst.TAX(),
        inst.LDA(hp_table_rom_start, AM.LNG_X),
        inst.STA(temp_addr, AM.DIR),
        # Put the HP value into stat memory.
        inst.LDA(temp_pc_id_addr, AM.DIR),  # Get the start of the PC's stats.
        inst.AND(0x00FF, AM.IMM16),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(stat_offset_rom_start, AM.LNG_X),
        inst.TAX(),
        inst.LDA(temp_addr, AM.DIR),
        inst.STA(0x7E0000+cur_hp_offset, AM.LNG_X),
        inst.STA(0x7E0000+max_hp_offset, AM.LNG_X)
    ]

    set_mp_rt = [
        # Get the MP value from the table
        # inst.SEP(0x20),
        # inst.LDA(100, AM.IMM8),
        # inst.STA(SR.M7A, AM.ABS),
        # inst.STZ(SR.M7A, AM.ABS),
        # inst.LDA(temp_pc_id_addr, AM.DIR),
        # inst.STA(SR.M7B, AM.ABS),
        # inst.REP(0x20),
        # inst.LDA(SR.MPYL, AM.ABS),
        inst.REP(0x20),
        inst.LDA(temp_pc_id_addr, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.PHD(),
        inst.PEA(0x0000, AM.IMM16),
        inst.PLD(),
        inst.STA(0x2A, AM.DIR),
        inst.LDA(100, AM.IMM16),
        inst.STA(0x28, AM.DIR),
        inst.JSL(slow_mult_rom_addr, AM.LNG),
        inst.REP(0x20),
        inst.LDA(0x2C, AM.DIR),
        inst.PLD(),
        inst.CLC(),
        inst.ADC(temp_target_level, AM.DIR),
        inst.TAX(),
        inst.LDA(mp_table_rom_start, AM.LNG_X),
        inst.AND(0x00FF, AM.IMM16),
        inst.STA(temp_addr, AM.DIR),
        # Put the MP value into stat memory.
        inst.LDA(temp_pc_id_addr, AM.DIR),  # Get the start of the PC's stats.
        inst.AND(0x00FF, AM.IMM16),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(stat_offset_rom_start, AM.LNG_X),
        inst.TAX(),
        inst.LDA(temp_addr, AM.DIR),
        inst.STA(0x7E0000 + cur_mp_offset, AM.LNG_X),
        inst.STA(0x7E0000 + max_mp_offset, AM.LNG_X),
        inst.STX(temp_addr, AM.DIR),
        inst.LDA(temp_target_level, AM.DIR),
        inst.AND(0x00FF, AM.IMM16),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.LDA(xp_next_rom_start, AM.LNG_X),
        inst.LDX(temp_addr, AM.DIR),
        inst.STA(0x7E0000 + xp_next_offset, AM.LNG_X),
    ]

    growth_offset_dict = ctpcstats.StatGrowth.get_offset_dict()
    base_stat_offset_dict = ctpcstats.StatBlock.get_base_stat_offset_dict()
    cur_stat_offset_dict = ctpcstats.StatBlock.get_cur_stat_offset_dict()

    stat_growth_start = 0xCC25FA
    Stat = ctpcstats.PCStat

    set_stats_init = [
        inst.LDA(0x0000, AM.IMM16),
        inst.SEP(0x20),
        # Convenient to set the target's level here too.
        inst.LDA(temp_target_level, AM.DIR),
        inst.STA(0x7E0000+level_offset, AM.LNG_X),
        inst.LDA(temp_pc_id_addr, AM.DIR),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.ASL(mode=AM.NO_ARG),
        inst.SEC(),
        inst.SBC(temp_pc_id_addr, AM.DIR),  # 7*pc_id
        inst.TAX(),
        inst.PHX(),
    ]

    ret_rt = store_args_rt + set_hp_rt + set_mp_rt + set_stats_init

    def make_stat_set_block(
            stat: ctpcstats.PCStat,
            pull_x: bool = True,  # No pull on first
            push_x: bool = True,  # No push on first, last
    ) -> assemble.ASMList:
        """Make a bit of asm to set a stat to the level this command has read"""
        init = []
        if pull_x:
            init.append(inst.PLX())
        if push_x:
            init.append(inst.PHX())

        slow_mult_rom_addr = 0xC1FDBF

        postlabel = str(stat)
        ret_block = init + [
            inst.LDA(stat_growth_start + growth_offset_dict[stat], AM.LNG_X),
            inst.REP(0x20),
            inst.AND(0x00FF, AM.IMM16),
            inst.STA(0x28, AM.ABS),
            inst.LDA(temp_target_level, AM.DIR),
            inst.AND(0x00FF, AM.IMM16),
            inst.DEC(mode=AM.NO_ARG),
            inst.STA(0x2A, AM.ABS),
            inst.PHD(),
            inst.PEA(0x0000, AM.IMM16),
            inst.PLD(),
            inst.JSL(slow_mult_rom_addr, AM.LNG),
            inst.PLD(),
            inst.REP(0x20),
            inst.LDA(0x2C, AM.ABS),
            # inst.STA(SR.M7A, AM.ABS),
            # inst.STZ(SR.M7A, AM.ABS),
            # inst.LDA(temp_target_level, AM.DIR),
            # inst.DEC(mode=AM.NO_ARG),
            # inst.STA(SR.M7B, AM.ABS),
            # inst.REP(0x20),
            # inst.LDA(SR.MPYL, AM.ABS),
            inst.STA(SR.WRDIVL, AM.ABS),
            inst.SEP(0x20),
            inst.LDA(100, AM.IMM8),
            inst.STA(SR.WRDIVB, AM.ABS)
        ] + [inst.NOP()]*8 + [
            inst.LDA(SR.RDDIVL, AM.ABS),
            inst.CMP(100, AM.IMM8),
            inst.BCS("max"+postlabel),
            inst.LDX(temp_addr, AM.DIR),
            inst.CLC(),
            inst.ADC(0x7E0000+base_stat_offset_dict[stat], AM.LNG_X),
            inst.CMP(100, AM.IMM8),
            inst.BCS("max"+postlabel),
            inst.STA(0x7E0000+cur_stat_offset_dict[stat], AM.LNG_X),
            inst.BRA("no_max"+postlabel),
            "max"+postlabel,
            inst.LDA(99, AM.IMM8),
            inst.STA(0x7E0000+cur_stat_offset_dict[stat], AM.LNG_X),
            "no_max"+postlabel
        ]
        return ret_block

    for ind, stat in enumerate((
            Stat.POWER, Stat.MAGIC, Stat.EVADE, Stat.MAGIC_DEFENSE,
            Stat.STAMINA, Stat.HIT,
    )):
        push_x, pull_x = True, True
        if ind == 0:
            push_x = False
            pull_x = False
        if ind == 5:
            push_x = False

        ret_rt += make_stat_set_block(stat, pull_x, push_x)

    ret_rt += [
        # Normal ending stuff.
        inst.SEC(),
        inst.TYX(),
        inst.RTL()
    ]

    return ret_rt


def add_set_level_command(
        ct_rom: ctrom.CTRom,
        pc_stats: ctpcstats.PCStatsManager  # for hp/mp values
):
    hp_table = bytearray(7*100*2)
    hp_io = io.BytesIO(hp_table)
    mp_table = bytearray(7*100)
    mp_io = io.BytesIO(mp_table)

    for pc_id in ctenums.CharID:
        hp_growth = pc_stats.pc_stat_dict[pc_id].hp_growth
        max_hp = pc_stats.pc_stat_dict[pc_id].stat_block.max_hp
        mp_growth = pc_stats.pc_stat_dict[pc_id].mp_growth
        max_mp = pc_stats.pc_stat_dict[pc_id].stat_block.max_mp

        cur_level = pc_stats.get_level(pc_id)
        cur_hp = max_hp - hp_growth.cumulative_growth_at_level(cur_level)
        cur_mp = max_mp - mp_growth.cumulative_growth_at_level(cur_level)

        for level in range(100):
            if cur_hp < 999:
                cur_hp += hp_growth.growth_at_level(level)
                cur_hp = min(cur_hp, 999)
            hp_io.write(cur_hp.to_bytes(2, "little"))

            if cur_mp < 99:
                cur_mp += mp_growth.growth_at_level(level)
                cur_mp = min(cur_mp, 99)
            mp_io.write(cur_mp.to_bytes(1, "little"))

    hp_table_addr = ct_rom.space_manager.get_free_addr(len(hp_io.getbuffer()), 0x410000)
    ct_rom.seek(hp_table_addr)
    ct_rom.write(hp_io.getbuffer(), freespace.FSWriteType.MARK_USED)

    mp_table_addr = ct_rom.space_manager.get_free_addr(len(mp_io.getbuffer()), 0x410000)
    ct_rom.seek(mp_table_addr)
    ct_rom.write(mp_io.getbuffer(), freespace.FSWriteType.MARK_USED)

    rt_asm = get_set_level_event_cmd_asm(
        byteops.to_rom_ptr(hp_table_addr),
        byteops.to_rom_ptr(mp_table_addr)
    )

    add_event_command(ct_rom, rt_asm, 0xFC)


def add_event_command(
        ct_rom: ctrom.CTRom,
        routine: assemble.ASMList,
        new_command_id: int
):
    new_command_bytes = assemble.assemble(routine)

    rt_addr = ct_rom.space_manager.get_free_addr(len(new_command_bytes))
    ct_rom.seek(rt_addr)
    ct_rom.write(new_command_bytes, freespace.FSWriteType.MARK_USED)

    hook_b = assemble.assemble(
        [
            inst.JSL(byteops.to_rom_ptr(rt_addr), inst.AddressingMode.LNG),
            inst.RTS()
        ]
    )

    cmd_st = ct_rom.space_manager.get_free_addr(0, len(hook_b))
    if cmd_st & 0xFF0000 != 0:
        raise freespace.FreeSpaceError
    ct_rom.seek(cmd_st)
    ct_rom.write(hook_b, freespace.FSWriteType.MARK_USED)

    ct_rom.seek(0x5D6E + 2*new_command_id)
    ct_rom.write(cmd_st.to_bytes(2, "little"))


def expand_eventcommands(ct_rom: ctrom.CTRom):
    """
    Adds space for more eventcommands:
    - Set Level (0xTBD)
    - Set Tech Level (0xTBD)
    - Multiworld item gather command?
    """

    # There is *very* little space in bank 0x00.
    ct_rom.space_manager.mark_block(
        (0x00F2F0, 0x00F300), freespace.FSWriteType.MARK_FREE
    )

    # Each eventcommand needs 5 bytes (4 JSL + 1 RTS).
    # We can fit 3 new commands for now, but any more will require more sophistication.
    set_tp_rt = get_set_techlevel_event_cmd_asm()

    add_event_command(ct_rom, set_tp_rt, 0xFD)
    # set_tp_rt_b = assemble.assemble(set_tp_rt)
    #
    # set_tp_cmd_addr = ct_rom.space_manager.get_free_addr(len(set_tp_rt_b))
    # set_tp_cmd_rom_addr = byteops.to_rom_ptr(set_tp_cmd_addr)
    #
    # ct_rom.seek(set_tp_cmd_addr)
    # ct_rom.write(set_tp_rt_b, freespace.FSWriteType.MARK_USED)
    #
    # hook_b = assemble.assemble(
    #     [
    #         inst.JSL(set_tp_cmd_rom_addr, inst.AddressingMode.LNG),
    #         inst.RTS()
    #     ]
    # )
    #
    # cmd_st = 0x00F2F0
    # ct_rom.seek(cmd_st)
    # ct_rom.write(hook_b, freespace.FSWriteType.MARK_USED)
    #
    # new_cmd_id = 0xFD
    # ct_rom.seek(0x5D6E + 2*new_cmd_id)
    # ct_rom.write(cmd_st.to_bytes(2, "little"))


def patch_division(ct_rom: ctrom.CTRom):
    """
    The division routine works with a 24-bit dividend but returns
    0 if the low 16 bits are 0.  Change this.
    """

    hook_addr = 0x01C92B
    return_addr = 0x01C933
    return_rom_addr = return_addr + 0xC00000
    AM = inst.AddressingMode

    routine: assemble.ASMList = [
        inst.REP(0x30),
        inst.STZ(0x2C, AM.ABS),
        inst.STZ(0x32, AM.ABS),
        inst.LDA(0x28, AM.ABS),
        inst.BNE("end"),
        inst.LDA(0x2E, AM.ABS),
        "end",
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        routine, hook_addr, ct_rom, return_addr
    )


def apply_ow_warp_patch(
        ct_rom: ctrom.CTRom,
        epoch_loc_id: ctenums.LocID = ctenums.LocID.OW_PRESENT,
):
    """Make start+select return to Crono's house"""

    # Code for when select is pressed:
    # C235FC  E2 20          SEP #$20
    # C235FE  A9 06          LDA #$06
    # C23600  8D 7C 02       STA $027C
    # C23603  80 AE          BRA $C235B3

    hook_addr = 0x0235FC
    return_addr = 0x023600
    return_rom_addr = byteops.to_rom_ptr(return_addr)

    buttons_addr_abs = 0x00F2
    start_mask = 0x01
    ow_status_addr_abs = 0x027C

    AM = inst.AddressingMode
    routine: assemble.ASMList = [
        inst.LDA(buttons_addr_abs, AM.ABS),
        inst.BIT(start_mask, AM.IMM16),
        inst.BEQ("normal_map"),
        inst.LDA(ctenums.LocID.CRONOS_KITCHEN, AM.IMM16),
        inst.STA(0x0100, AM.ABS),
        inst.LDA(0x0B0A, AM.IMM16),  # coords
        inst.STA(0x0102, AM.ABS),
        inst.LDA(memory.Flags.EPOCH_OBTAINED_LOC.value.address, AM.LNG),
        inst.BIT(memory.Flags.EPOCH_OBTAINED_LOC.value.bit, AM.IMM16),
        inst.BEQ("skip_epoch_move"),
        inst.LDA(epoch_loc_id, AM.IMM16),
        inst.STA(memory.Memory.EPOCH_MAP_LO & 0xFFFF, AM.ABS),
        inst.LDA(0x270, AM.IMM16),
        inst.STA(memory.Memory.EPOCH_X_COORD_LO & 0xFFFF, AM.ABS),
        inst.LDA(0x258, AM.IMM16),
        inst.STA(memory.Memory.EPOCH_Y_COORD_LO & 0xFFFF, AM.ABS),
        "skip_epoch_move",
        inst.LDA(0x0218, AM.IMM16),
        inst.STA(memory.Memory.DACTYL_X_COORD_LO & 0xFFFF, AM.ABS),
        inst.LDA(0x0128, AM.IMM16),
        inst.STA(memory.Memory.DACTYL_Y_COORD_LO & 0xFFFF, AM.ABS),
        inst.SEP(0x20),
        inst.LDA(0x01, AM.IMM8),
        inst.STA(0x0105, AM.ABS),
        inst.LDA(0x02, AM.IMM8),

        # inst.STA(ow_status_addr_abs, AM.ABS),
        inst.BRA("end"),
        "normal_map",
        inst.SEP(0x20),
        inst.LDA(0x06, AM.IMM8),
        # inst.STA
        "end",
        inst.JMP(return_rom_addr, AM.LNG)
    ]

    asmpatcher.apply_jmp_patch(
        routine, hook_addr, ct_rom, return_addr
    )


def main():
    pass


if __name__ == "__main__":
    main()

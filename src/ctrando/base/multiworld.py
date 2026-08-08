"""Allow items to be gained by setting certain memory."""

from typing import Optional

from ctrando.asm import assemble
from ctrando.asm import instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.base.openworldutils import CommandNotFoundException
from ctrando.base import chestmod
from ctrando.common import (
    asmpatcher,
    byteops,
    ctenums,
    ctrom,
    freespace,
    memory,
)
from ctrando.locations.eventcommand import EventCommand
from ctrando.locations.scriptmanager import ScriptManager

ROM_VALIDATION_ADDR = 0x3F8C03

TECH_LEVEL_MODE = 0x40
ITEM_MODE = 0x20

def _patch_remote_items(
        ct_rom: ctrom.CTRom,
        item_count_addr: int,
        buffer_addr: int
):
    """Add the remote item routine in the location game loop"""

    # C000AD  22 87 1F C0    JSL $C01F87

    tech_level_rt = chestmod.get_add_techlevel_block()
    tech_level_jsl = tech_level_rt + [inst.RTL()]
    tech_level_addr = asmpatcher.add_jsl_routine(tech_level_jsl, ct_rom,
                                                 0x410000)
    tech_level_rom_addr = byteops.to_rom_ptr(tech_level_addr)

    base_rt: assemble.ASMList = [
        inst.PHX(),
        inst.PHY(),
        inst.PHP(),
        inst.SEP(0x20),
        inst.REP(0x10),
        inst.LDA(buffer_addr+1, AM.LNG),
        inst.BEQ("end"),
        # Deliver the thing
        inst.BIT(0x40, AM.IMM8),
        inst.BEQ("try_item"),
        # Tech level
        inst.REP(0x20),
        inst.LDA(buffer_addr, AM.LNG),
        inst.JSL(tech_level_rom_addr),
        inst.BRA("clear_buf"),
        "try_item",
        inst.BIT(0x20, AM.IMM8),
        inst.BEQ("clear_buf"),
        # Item
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
        inst.PLY(),
        inst.PLX(),
    ]

    loc_rt = base_rt + [
        # old call
        inst.JSL(0xC01F87, AM.LNG),
        inst.RTL()
    ]

    ow_rt = base_rt + [
        inst.TDC(),
        inst.SEP(0x20),
        inst.LDA(0x027C, AM.ABS),
        inst.ASL(mode=AM.NO_ARG),
        inst.TAX(),
        inst.RTL()
    ]

    loc_addr = asmpatcher.add_jsl_routine(loc_rt, ct_rom)
    loc_rom_addr = byteops.to_rom_ptr(loc_addr)
    ct_rom.seek(0x0000AD)
    ct_rom.write(inst.JSL(loc_rom_addr, AM.LNG).to_bytearray())

    ow_addr = asmpatcher.add_jsl_routine(ow_rt, ct_rom)
    ow_rom_addr = byteops.to_rom_ptr(ow_addr)
    ct_rom.seek(0x0223D2)
    ct_rom.write(inst.JSL(ow_rom_addr, AM.LNG).to_bytearray() + bytearray([0xEA, 0xEA]))

def _add_victory_flag(ct_rom: ctrom.CTRom, script_manager: ScriptManager):
    """
    Add a victory flag to the ending selector scene so that the AP client
    can detect when the player finishes the game.
    """
    script = script_manager[ctenums.LocID.ENDING_SELECTOR_052]

    # Add our flag to the beginning of the ending selector startup
    cmd = EventCommand.set_explore_mode(False)
    pos = script.find_exact_command(cmd)

    if pos is None:
        raise CommandNotFoundException

    pos = pos + len(cmd)
    victory_flag = memory.Flags.VICTORY_FLAG
    victory_flag_cmd = EventCommand.set_bit(victory_flag.value.address, victory_flag.value.bit)
    script.insert_commands(victory_flag_cmd.to_bytearray(), pos)


def write_player_validation_data(ct_rom: ctrom.CTRom, encoded_name: bytes):
    """Write the player validation data to the ROM"""
    ct_rom.seek(ROM_VALIDATION_ADDR)
    ct_rom.write(b"APRDI" + encoded_name)

def apply_multiworld_patches(ct_rom: ctrom.CTRom, script_manager: ScriptManager):
    """Apply the  multiworld related patches and changes"""

    # Reserve memory for player validation
    block = (ROM_VALIDATION_ADDR, ROM_VALIDATION_ADDR + 0x20)
    MARK_FREE = ctrom.freespace.FSWriteType.MARK_FREE
    ct_rom.space_manager.mark_block(block, MARK_FREE)
    #if not ct_rom.space_manager.is_block_free(block):
    #    raise freespace.FreeSpaceError(f"Multiworld validation block already in use: {block}")

    ct_rom.space_manager.mark_block(block, freespace.FSWriteType.MARK_USED)

    _patch_remote_items(ct_rom, 0x7F003B, 0x7F0039)
    _add_victory_flag(ct_rom, script_manager)

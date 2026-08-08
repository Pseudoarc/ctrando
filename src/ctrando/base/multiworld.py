"""Allow items to be gained by setting certain memory."""

from typing import Optional

from ctrando.asm import assemble
from ctrando.asm import instructions as inst
from ctrando.asm.instructions import AddressingMode as AM
from ctrando.base.openworldutils import CommandNotFoundException
from ctrando.common import (
    asmpatcher,
    byteops,
    ctenums,
    ctrom,
    freespace,
    memory,
    randostate,
)
from ctrando.locations.eventcommand import EventCommand

ROM_VALIDATION_ADDR = 0x3F8C03

def _patch_remote_items(
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

def _add_victory_flag(ct_rom: ctrom.CTRom, script_manager: randostate.ScriptManager):
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

def apply_multiworld_patches(ct_rom: ctrom.CTRom, script_manager: randostate.ScriptManager):
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

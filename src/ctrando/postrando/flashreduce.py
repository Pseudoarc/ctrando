"""Remove some flashing effects from the game"""

import enum
from typing import Optional

from ctrando.asm import instructions as inst, assemble
from ctrando.asm.instructions import AddressingMode as AM

from ctrando.common import byteops, ctenums, ctrom
from ctrando.common.freespace import FSWriteType as FSW
from ctrando.locations.locationevent import LocationEvent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.scriptmanager import ScriptManager

from ctrando.overworlds.owmanager import OWManager
from ctrando.overworlds import oweventcommand as owc


def remove_effect_script_flashes(ct_rom: ctrom.CTRom):
    """
    Manually edit effect scripts to remove flashes.
    """

    # Ideally, we would have a parser for these effects, but since they are
    # unlikely to move around on the rom, we're going to edit them in-place
    # manually.


    # Twister
    twister_locs = (
        0x117826,
    )

    spire_locs = (
        0x1177D0, 0x1177CD, 0x1177D4, 0x1177D8, 0x1177DC, 0x1177E0, 0x1177E4,
        0x1177E8, 0x1177EC, 0x1177F0, 0x1177F4, 0x1177F8
    )

    triple_raid_locs = (
        0x1178E9, 0x1178EE, 0x116FB3, 0x116FBE, 0x116FC6, 0x116FC9,
    )

    total_locs = twister_locs + spire_locs + triple_raid_locs

    for loc in total_locs:
        ct_rom.seek(loc)
        ct_rom.write(b'\xE0\x00')


def remove_effect_cmd_E8_flashes(ct_rom: ctrom.CTRom):
    """
    Disable some modes of command 0x8E which are used to flash the screen.
    """

    rt = bytearray.fromhex(
        '9D 54 05'         # STA $0554, X  # Leftover from orig rt.
        'BD 50 05'         # LDA $0550, X
        'C9 40'            # CMP #$40
        'D0 06'            # BNE CLEANUP
        '9E 57 05'         # STZ $0557, X
        '9E 58 05'         # STZ $0558, X
        'C2 21'            # REP #$21 [CLEANUP]  # Leftover from orig rt.
        '5C 37 2A CD'      # JMP $CD2A37  # to original rt
    )

    # This routine does not have bank-specific instructions, so we want to
    # avoid using the free space that we claimed in bank $CD
    pos = ct_rom.space_manager.get_free_addr(len(rt), hint=0x410000)
    pos_b = int.to_bytes(byteops.to_rom_ptr(pos), 3, 'little')

    hook = b'\x5C' + pos_b
    ct_rom.seek(0x0D2A32)
    ct_rom.write(hook)

    ct_rom.seek(pos)
    ct_rom.write(rt, FSW.MARK_USED)


def remove_effect_cmd_80_flashes(ct_rom: ctrom.CTRom):
    """
    Disable flashes caused by effect command 0x80.

    This command is a general collection of effects subroutines.
      - Subroutine 0x1A instantaneously makes many palettes pure white.
        Code begins at 0x11E899.
    """

    ct_rom.seek(0x11E899)
    ct_rom.write(b'\x6B')

    # Free the rest of the routine.
    ct_rom.space_manager.mark_block((0x11E89A, 0x11E8C1), FSW.MARK_FREE)


def remove_anim_cmd_80_flashes(ct_rom: ctrom.CTRom):
    """
    Remove mode 0x40 flashes from animation command 0x80.
    """

    # If the routine would do a mode 0x50 (color add), instruct it to always
    # use a setting which resets the palette to default.

    # This could be redone with the asm module, but too much work.
    rt = bytearray.fromhex(
        'A5 54'        # LDA $54
        '29 40'        # AND #$40
        'D0 04'        # BNE #$04
        'A9 20'        # LDA #$20  # This mode will reset the palettes
        '80 04'        # BRA [OLD_START]
        'A5 53'        # LDA $53
        '29 F0'        # AND #$F0
        'AA'           # TAX [OLD_START]
        '7B'           # TDC
        'A8'           # TAY
        '5C 54 F7 D1'  # JMP $D1F754
    )

    rt_pos = ct_rom.space_manager.get_free_addr(len(rt), hint=0x410000)

    ct_rom.seek(0x11F74D)
    rt_pos_b = int.to_bytes(byteops.to_rom_ptr(rt_pos), 3, 'little')
    hook = b'\x5C' + rt_pos_b
    ct_rom.write(hook)

    ct_rom.seek(rt_pos)
    ct_rom.write(rt, ctrom.freespace.FSWriteType.MARK_USED)


def disable_ow_color_math(
        ct_rom: ctrom.CTRom,
        ow_manager: OWManager
):
    """
    Disable color math (mostly used for flashing) from the overworld.
    """

    future = ow_manager.overworld_dict[ctenums.OverWorldID.FUTURE]
    future_event = future.event

    # This byte is setting the colormath settings for the OW.  We're setting
    # it to 0x3C because (1) this is a unique value, and (2) it has layer3
    # colormath turned on so that the snow looks normal.
    ind = future_event.find_next_exact_command(
        owc.AssignByte7E(offset=0x0046, value=0x3F)
    )
    future_event.replace_commands(
        ind, ind+1, owc.AssignByte7E(offset=0x0046, value=0x3C)
    )

    # Next we're editing the routine where the ppu registers are written.
    # On a value of 0x3C, we'll write 0xE0 (no addition).  Otherwise, we'll
    # use the original routine.

    # The original routine reads the B, G, and R components from $47-$49 and
    # writes them to the color data register.
    # We add a jump back to where the original routine would have ended.
    orig_rt = bytearray.fromhex(
        'A5 47'        # LDA $47
        '09 80'        # ORA #$80
        '8D 32 21'     # STA $2132
        'A5 49'        # LDA $49
        '09 40'        # ORA #40
        '8D 32 21'     # STA $2132
        'A5 48'        # LDA $48
        '09 20'        # ORA #$20
        '8D 32 21'     # STA $2132
        '5C B0 02 C2'  # JMP $C202B0
    )

    # get space to relocate this.
    pos = ct_rom.space_manager.get_free_addr(len(orig_rt))
    ct_rom.seek(pos)
    ct_rom.write(orig_rt, FSW.MARK_USED)

    pos_b = int.to_bytes(byteops.to_rom_ptr(pos), 3, 'little')
    jump_cmd = b'\x5C' + pos_b

    hook = bytearray.fromhex(
        'C9 3C'        # CMP #$3C
        'F0 04'        # BEQ #$04
        + jump_cmd.hex() +
        'A9 E0'        # LDA #$E0
        '8D 32 21'     # STA $2132
        '80 06'        # BRA [$C202B0]
    )

    ct_rom.seek(0x02029B)
    ct_rom.write(hook)


def disable_epoch_flash(ct_rom: ctrom.CTRom):
    """
    Edit an overworld subroutine to change flash to fade (?)
    """

    # OW Command 0x04 has format 04 XX YY ZZ AA BB
    # XX YY ZZ is the address to load a palette from
    # AA is the palette number to altered
    # BB is a mode parameter.  00 means set, 01 means fade into (?)

    # When the epoch flies off, all 16 palettes are flashed to white
    # We are going to change the mode of these commands from 00 to 01.
    # We are lucky.  This is in a SR on ROM instead of part of the compressed
    # event.

    ct_rom.seek(0x024B0E)
    for _ in range(15):  # Alters all palette but 1 (epoch?)
        ct_rom.write(b'\x01')
        ct_rom.seek(5, 1)


def remove_event_script_flashes(script_manager: ScriptManager):

    def remove_script_flashes(script: LocationEvent):
        pos: Optional[int] = script.get_function_start(0, 0)

        # Any instantaneous flash is replaced with a return to no addition.
        # This is represented by 'F1 E0 00'
        while True:
            pos, cmd = script.find_command_opt([0xF1], pos)
            if pos is None:
                break

            if script.data[pos+2] & 0x7F == 0:  # instantaneous
                script.data[pos+1] = 0xE0  # Reset color.

            pos += len(cmd)

    # Be delicate with these because they sometimes have other color additions
    # that are not actually a problem.
    loc_ids = (ctenums.LocID.BLACK_OMEN_1F_DEFENSE_CORRIDOR,
               ctenums.LocID.BLACK_OMEN_98F_OMEGA_DEFENSE,
               ctenums.LocID.BLACK_OMEN_TERRA_MUTANT)

    flash_cmd = EC.generic_two_arg(0xF1, 0xF8, 0x00)

    for loc in loc_ids:
        script = script_manager[loc]

        pos: Optional[int] = script.get_function_start(0, 0)
        while True:
            pos = script.find_exact_command_opt(flash_cmd, pos)
            if pos is None:
                break

            script.data[pos+1] = 0xE0

    generic_loc_ids = (
        ctenums.LocID.HECKRAN_CAVE_PASSAGEWAYS,
        ctenums.LocID.HECKRAN_CAVE_BOSS,
        ctenums.LocID.NORTHERN_RUINS_HEROS_GRAVE
    )

    for loc_id in generic_loc_ids:
        script = script_manager[loc_id]
        remove_script_flashes(script)


def apply_all_flash_hacks(
        script_manager: ScriptManager,
        ow_manager: OWManager,
        ct_rom: ctrom.CTRom
):
    # remove_effect_cmd_C9_flashes(ct_rom)
    remove_effect_cmd_E8_flashes(ct_rom)
    remove_effect_cmd_80_flashes(ct_rom)
    remove_anim_cmd_80_flashes(ct_rom)

    disable_epoch_flash(ct_rom)
    disable_ow_color_math(ct_rom, ow_manager)

    remove_event_script_flashes(script_manager)
    remove_effect_script_flashes(ct_rom)

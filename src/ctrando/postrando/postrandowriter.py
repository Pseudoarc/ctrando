"""Write Post-Randomization options to rom data"""
from ctrando.arguments import postrandooptions
from ctrando.base.basepatch import apply_fast_ow_movement
from ctrando.common import ctrom
from ctrando.postrando import gameoptions

def set_auto_run(ct_rom: ctrom.CTRom):
    # Each direction (up, down, left, right, + 4 diags) has a block for
    # setting run or not.  We follow an old Mauron post
    # https://gamefaqs.gamespot.com/boards/563538-chrono-trigger/ \
    #   75569957?page=5
    # and reverse BEQs to BNEs.  Note that the post is missing the down/left
    # jump location.
    jump_command_addrs = [
        0x00892A, 0x008949, 0x008968, 0x008987, 0x008A41,
        0x008A0C, 0x0089A6, 0x0089D7
    ]

    jump_cmds = bytes.fromhex('ADF8008902F0')
    # rom = ct_rom.getbuffer()

    for addr in jump_command_addrs:
        end = addr + 1
        st = end - len(jump_cmds)
        ct_rom.seek(st)
        existing_jump = ct_rom.read(len(jump_cmds))

        if existing_jump != jump_cmds:
            raise ValueError(f'Did not find a jump at {addr:06X}')

        ct_rom.seek(addr)
        ct_rom.write(b'\xD0') # BNE instead of the 0xF0 BEQ


def write_post_rando_options(
        post_rando_options: postrandooptions.PostRandoOptions,
        ct_rom: ctrom.CTRom
):
    """Implement settings from PostRandoOptions object."""

    if post_rando_options.default_fast_loc_movement:
        set_auto_run(ct_rom)

    apply_fast_ow_movement(
        ct_rom,
        post_rando_options.default_fast_ow_movement,
        post_rando_options.default_fast_epoch_movement
    )

    default_opts = gameoptions.Options.read_from_ctrom(ct_rom)
    default_opts.save_battle_cursor = post_rando_options.battle_memory_cursor
    default_opts.save_menu_cursor = post_rando_options.menu_memory_cursor
    default_opts.battle_speed = post_rando_options.battle_speed - 1
    default_opts.message_speed = post_rando_options.message_speed - 1

    default_opts.write_to_ctrom(ct_rom)
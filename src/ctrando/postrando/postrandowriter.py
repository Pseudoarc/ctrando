"""Write Post-Randomization options to rom data"""
from collections.abc import Callable

from ctrando.arguments import postrandooptions
from ctrando.base.basepatch import apply_fast_ow_movement
from ctrando.common import ctrom
from ctrando.postrando import gameoptions, palettes


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


def write_palettes(
        ct_rom: ctrom.CTRom,
        post_rando_options: postrandooptions.PostRandoOptions
):
    char_palettes = [
        post_rando_options.crono_palette, post_rando_options.marle_palette,
        post_rando_options.lucca_palette, post_rando_options.robo_palette,
        post_rando_options.frog_palette, post_rando_options.ayla_palette,
        post_rando_options.magus_palette
    ]

    for ind, palette in enumerate(char_palettes):
        palette.write_to_ctrom(ct_rom, ind)

    ow_pc_palettes = palettes.OWPallete.read_from_ct_rom(ct_rom, 0)
    # from ctrando.common import byteops
    # byteops.print_bytes(ow_pc_palettes.to_bytes(), 0x10)
    # input()


    defaults = postrandooptions.PostRandoOptions()
    default_palettes = [
        defaults.crono_palette, defaults.marle_palette, defaults.lucca_palette,
        defaults.robo_palette, defaults.frog_palette, defaults.ayla_palette,
        defaults.magus_palette
    ]

    ow_palette_builders: list[Callable[[palettes.SNESPalette], palettes.SinglePCOWPalette]] = [
        palettes.build_crono_ow_palette, palettes.build_marle_ow_palette,
        palettes.build_lucca_ow_palette, palettes.build_robo_ow_palette,
        palettes.build_frog_ow_palette, palettes.build_ayla_ow_palette,
        palettes.build_magus_ow_palette,
    ]

    portrait_palette_builders: list[Callable[[palettes.SNESPalette], palettes.PortraitPallete]] = [
        palettes.build_crono_portrait_palette, palettes.build_marle_portrait_palette,
        palettes.build_lucca_portrait_palette, palettes.build_robo_portrait_palette,
        palettes.build_frog_portrait_palette, palettes.build_ayla_portrait_palette,
        palettes.build_magus_portrait_palette,
    ]

    portait_ids = [3, 6, 5, 1, 2, 4, 0]

    for ind, (
            new_palette, default_palette, ow_palette_builder,
            portrait_palette_builder, portrait_id
    ) in \
            enumerate(zip(char_palettes, default_palettes, ow_palette_builders,
                    portrait_palette_builders, portait_ids)):
        if new_palette != default_palette:
            ow_palette = ow_palette_builder(new_palette)
            ow_pc_palettes.set_pc_palette(ind, ow_palette)

            portait_palette = portrait_palette_builder(new_palette)
            portait_palette.write_to_ctrom(ct_rom, portrait_id)

    ow_pc_palettes.write_to_ctrom(ct_rom, 0)


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
    default_opts.menu_style = post_rando_options.window_background - 1

    default_opts.write_to_ctrom(ct_rom)
    write_palettes(ct_rom, post_rando_options)
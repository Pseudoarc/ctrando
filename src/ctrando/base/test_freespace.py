from ctrando.common import ctrom
from ctrando.base import basepatch

ct_rom = ctrom.CTRom.from_file('./ct.sfc')
basepatch.mark_initial_free_space(ct_rom)

ct_rom.rom_data.patch_ips_file('./base_patch.ips')

ct_rom.rom_data.space_manager.print_blocks()

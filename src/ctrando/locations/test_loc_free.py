from ctrando.base import basepatch
from ctrando.common import ctenums, ctrom
from ctrando.locations import locationevent
from ctrando.strings import ctstrings


def main():
    ct_rom = ctrom.CTRom.from_file('./ct.sfc')
    bad_ids = [ctenums.LocID.JUNK_1C0, ctenums.LocID.JUNK_1C4,
               ctenums.LocID.JUNK_1C5, ctenums.LocID.JUNK_1C6,
               ctenums.LocID.JUNK_1C7]

    script_dict: dict[ctenums.LocID, locationevent.LocationEvent] = {}
    
    for loc_id in ctenums.LocID:
        if loc_id in bad_ids:
            # print(f'Skipping {loc_id}')
            continue
        # print(f'{int(loc_id):04X}: {loc_id}')
        script_dict[loc_id] = locationevent.LocationEvent.from_rom_location(
            ct_rom.getbuffer(), loc_id)
        # locationevent.free_script_on_ctrom(ct_rom, loc_id)
        # locationevent.free_script_strings_on_ct_rom(ct_rom, loc_id)

    ct_rom.make_exhirom()
    FSW = ctrom.freespace.FSWriteType
    ct_rom.space_manager.mark_block((0x1B0000, 0x1C0000), FSW.MARK_FREE)
    ct_rom.space_manager.mark_block((0x368000, 0x3CF9F0), FSW.MARK_FREE)
    ct_rom.space_manager.mark_block((0x3D9000, 0x3DA000), FSW.MARK_FREE)
    basepatch.mark_vanilla_dialogue_free(ct_rom)

    script = script_dict[ctenums.LocID.DORINO_PERVERT_RESIDENCE]
    strings = script.strings

    for string in strings:
        print(string)
        if 1 in string:
            input('bad')
        print(ctstrings.CTString(string))
    
    input('start write')
    for loc_id, script in script_dict.items():
        locationevent.write_location_script_to_ctrom(
            script, ct_rom, loc_id
        )
    input('end_write')
    ct_rom.space_manager.print_blocks()

    with open('./ct-event-move.sfc', 'wb') as outfile:
        outfile.write(ct_rom.getbuffer())

if __name__ == '__main__':
    main()

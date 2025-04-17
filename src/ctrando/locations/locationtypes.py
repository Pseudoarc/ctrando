"""Module with types for data used by locataions."""
from __future__ import annotations
import itertools

from ctrando.common import byteops, ctenums, ctrom, cttypes


# Location Data (above):
# 360000	361BFF	DATA	N	Location Data (14 bytes each)

# Location Data	00	FF	1	Music played at location
# Location Data	01	FF	1	Tileset Layer 1 & 2
# Location Data	02	FF	1	Tile Chunks for Layer 3
# Location Data	03	FF	1	PaletteSet
#   ((PS * 0xD2) + 0x3624C0)
# Location Data	04	FF	2	Loaded map
# Location Data	06	FF	2	Ignored
# Location Data	08	FF	2	Location Events
# Location Data	0A	FF	1	Left
# Location Data	0B	FF	1	Top
# Location Data	0C	FF	1	Right
# Location Data	0D	FF	1	Bottom
class LocationData(cttypes.SizedBinaryData):
    """Class for Location Data (mostly indices into other structures)"""
    SIZE = 0xE
    ROM_RW = cttypes.AbsPointerRW(0x001B7A)

    music = cttypes.byte_prop(0)
    layer_12_tileset = cttypes.byte_prop(1)
    layer_3_tilechunks = cttypes.byte_prop(2)
    palette = cttypes.byte_prop(3)
    map_id = cttypes.bytes_prop(4, 2)
    event_id = cttypes.bytes_prop(8, 2)
    left_tile_bound = cttypes.byte_prop(0xA)
    top_tile_bound = cttypes.byte_prop(0xB)
    right_tile_bound = cttypes.byte_prop(0xC)
    bottom_tile_bound = cttypes.byte_prop(0xD)


# Location Exit	00	FF	1	X coord	2004.04.21
# Location Exit	01	FF	1	Y coord	2004.04.21
# Location Exit	02	7F	1	Width - 1	2004.04.22
# Location Exit	02	80	1	Vertical flag	2004.04.22
# Location Exit	03	01FF	2	Destination Location	2004.04.30
# Location Exit	04	06	1	Destination Facing	2004.04.21
# Location Exit	04	08	1	Half tile to the left of Dest exit
# Location Exit	04	10	1	Half tile above Dest exit
# Location Exit	04	E0	1	Not used	2004.04.22
# Location Exit	05	FF	1	Destination X coord	2004.04.21
# Location Exit	06	FF	1	Destination Y coord	2004.04.21
class LocationExit(cttypes.SizedBinaryData):
    """
    Class for a single location exit.
    """
    SIZE = 7
    ROM_RW = None # ROM_RW doesn't make sense.  Let Location handle.

    exit_x = cttypes.byte_prop(0)
    exit_y = cttypes.byte_prop(1)
    width = cttypes.byte_prop(
        2, 0x7F,
        input_filter=lambda self, val: val-1,
        output_filter=lambda self, val: val+1
    )
    is_vertical = cttypes.byte_prop(2, 0x80)
    destination = cttypes.bytes_prop(3, 2, 0x01FF, ret_type=ctenums.LocID)
    destination_facing = cttypes.byte_prop(4, 0x06)
    half_left = cttypes.byte_prop(4, 0x08)
    half_above = cttypes.byte_prop(4, 0x10)
    dest_x = cttypes.byte_prop(5)
    dest_y = cttypes.byte_prop(6)


# Location exits are stored as follows:
#  - There is a table of two-byte local pointers, one per location (+1 extra)
#    in location order.
#  - Bank of pointer == bank of pointer table.
#  - To get a location's exits take the range between that location's pointer
#    and the next (that's why there's +1 extra for location 0x1FF's end)
# It doesn't make sense to do the usual ROM_RW stuff because we're never
# trying to get a location exit with a specific index.  Instead, hold a dict
# that is int (LocID) -> list[LocationExit] with functions for reading/writing.
def get_location_exit_ptr_start(ct_rom: ctrom.CTRom) -> int:
    """
    Returns the start of the pointer table for location exits.
    """
    ct_rom.seek(0x00A6A6)
    ptr_table_start = int.from_bytes(ct_rom.read(3), 'little')
    ptr_table_start = byteops.to_file_ptr(ptr_table_start)

    return ptr_table_start


def get_location_exit_start(ct_rom: ctrom.CTRom,
                            loc_id: int) -> int:
    """Get the start address of a location's exits """
    ptr_table_start = get_location_exit_ptr_start(ct_rom)

    ptr_start = ptr_table_start + 2*loc_id
    ct_rom.seek(ptr_start)
    local_ptr = int.from_bytes(ct_rom.read(2), 'little')
    ptr = (ptr_table_start & 0xFF0000) + local_ptr
    return ptr


def get_location_exits(ct_rom: ctrom.CTRom,
                       loc_id: int) -> list[LocationExit]:
    """Get all of a location's exits"""
    start = get_location_exit_start(ct_rom, loc_id)
    end = get_location_exit_start(ct_rom, int(loc_id) + 1)

    if (end - start) % LocationExit.SIZE != 0:
        raise ValueError

    num_exits = (end - start) // LocationExit.SIZE
    ct_rom.seek(start)
    exits = [LocationExit(ct_rom.read(LocationExit.SIZE))
             for _ in range(num_exits)]

    # print(f'{loc_id}: Start at {start:06X}, {num_exits} exits')
    return exits


def get_exit_dict_from_ctrom(
        ct_rom: ctrom.CTRom
        ) -> dict[ctenums.LocID, list[LocationExit]]:
    """
    Returns a dict[int (LocID), list[LocationExit]] to store all exits for
    all locations.
    """
    ret_dict = {
        ctenums.LocID(loc_id): get_location_exits(ct_rom, loc_id)
        for loc_id in range(0x200)
    }

    return ret_dict


def repoint_location_exits(
        ct_rom: ctrom.CTRom,
        new_ptr_start: int,
        new_data_start: int
):
    """
    If location exits move, update all pointers to the new data.
    """
    if new_data_start & 0xFF0000 != new_ptr_start & 0xFF0000:
        raise ValueError("Data and pointers must be in the same bank")

    ptr_refs = [0x00A69E, 0x00A6A6]
    data_refs = [0x00A6B9, 0x00A6C2, 0x009CF6, 0x009D10, 0x009D1E,
                 0x009CD4, 0x009CDC, 0x009CE6, 0x009D17, 0x00A6E2]

    current_ptr_start = get_location_exit_ptr_start(ct_rom)
    current_data_start = get_location_exit_start(ct_rom, 0)

    # Use the bytes_io version because it will call ct_rom's write and
    # enforce mirroring.
    byteops.update_ptrs_bytesio(ct_rom, ptr_refs,
                                current_ptr_start, new_ptr_start)

    # data pointers are all based on bank
    byteops.update_ptrs_bytesio(ct_rom, data_refs,
                                current_data_start & 0xFF0000,
                                new_data_start & 0xFF0000)

    assert ct_rom.getbuffer()[0x008000:0x010000] == \
        ct_rom.getbuffer()[0x408000:0x410000]


def write_exit_dict_to_ctrom(
        ct_rom: ctrom.CTRom,
        exit_dict: dict[int, list[LocationExit]]
):
    """Write exit data out to rom, repointing if needed."""

    # Collect the binary exit data.
    exit_data = b''.join(
        loc_exit
        for loc_id in range(0x200)
        for loc_exit in exit_dict[loc_id]
    )

    ptr_table_st = get_location_exit_ptr_start(ct_rom)

    ct_rom.seek(ptr_table_st)
    first_ptr = int.from_bytes(ct_rom.read(2), 'little')
    first_ptr += ptr_table_st & 0xFF0000

    ct_rom.seek(ptr_table_st + 0x200)
    last_ptr = int.from_bytes(ct_rom.read(2), 'little')
    last_ptr += ptr_table_st & 0xFF0000

    starts = ct_rom.space_manager.get_same_bank_free_addrs(
        [0x402, len(exit_data)], 0x410000
    )

    ptr_start, data_start = starts[0], starts[1]
    # Build pointers now that we know where the data will go.
    ptrs = [data_start & 0xFFFF] + [len(exit_dict[ind])*LocationExit.SIZE
                  for ind in range(0x200)]
    ptrs = list(itertools.accumulate(ptrs))

    ptr_b = b''.join(int.to_bytes(ptr, 2, 'little') for ptr in ptrs)

    ct_rom.seek(ptr_start)
    ct_rom.write(ptr_b, ctrom.freespace.FSWriteType.MARK_USED)

    ct_rom.seek(data_start)
    ct_rom.write(exit_data, ctrom.freespace.FSWriteType.MARK_USED)

    repoint_location_exits(ct_rom, ptr_start, data_start)


def main():
    """Just for testing."""
    ct_rom = ctrom.CTRom.from_file('./ct.sfc')

    loc_exits = get_exit_dict_from_ctrom(ct_rom)
    exits = loc_exits[ctenums.LocID.CRONOS_KITCHEN]
    for loc_exit in exits:
        print(loc_exit)

    ct_rom.make_exhirom()

    write_exit_dict_to_ctrom(ct_rom, loc_exits)

    with open('./ct-exits.sfc', 'wb') as outfile:
        outfile.write(ct_rom.getbuffer())


if __name__ == '__main__':
    main()

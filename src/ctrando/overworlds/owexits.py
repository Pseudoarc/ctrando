"""Module to handle overworld exit data."""
from __future__ import annotations
from typing import Optional

from ctrando.common import byteops, ctrom, cttypes, ctenums
from ctrando.compression import ctcompression


# Notes on OW Exit Names:
# - Pointer Table at 0x06F400
# - Actual names need to be in the same bank as the pointer table.
# - Pointer index stored in the location exit
# - Names have dialog format instead of item name format

class OverworldExit(cttypes.BinaryData):
    """Class to handle a normal overworld exit."""
    SIZE = 7

    is_active = cttypes.byte_prop(0, 0x80, ret_type=bool)
    exit_x = cttypes.byte_prop(0, 0x7F)
    exit_y = cttypes.byte_prop(1, 0x3F)
    # Overworld Exits	01    C0    1
    # "???, only used for Denadoro Mtns in 600AD"
    unknown_1_C0 = cttypes.byte_prop(1, 0xC0)
    location_name = cttypes.byte_prop(2)

    # If location is set to 0x1FF, then the exit is marked as using a code
    # pointer.  The pointer index is given by dest_x.
    location = cttypes.bytes_prop(3, 2, 0x01FF)
    dest_facing = cttypes.byte_prop(4, 0x06)
    half_tile_left = cttypes.byte_prop(4, 0x08, ret_type=bool)
    half_tile_above = cttypes.byte_prop(4, 0x10, ret_type=bool)
    dest_x = cttypes.byte_prop(5)
    dest_y = cttypes.byte_prop(6)

    # Note: Some exits trigger ow event code instead of immediate area
    #       transitions.  To do this, set location=0x1FF and set dest_x to the
    #       index of the code pointer in the event to use.

    def __str__(self):
        ret_str = 'OWExit@'
        ret_str += f"({self.exit_x:02X}, {self.exit_y:02X}) -> "
        ret_str += str(ctenums.LocID(self.location))
        ret_str += f"@({self.dest_x:02X}, {self.dest_y:02X})"

        return ret_str


class OverworldCodeEntry(cttypes.BinaryData):
    """
    Class to handle an overworld entry associated with event code.

    Examples (possibly exhaustive):
      - When entering 1000AD from the vortex, one is triggered.
      - When entering 600AD from "riding the wind" one is triggered.
    """
    SIZE = 3

    entry_x = cttypes.byte_prop(0)
    entry_y = cttypes.byte_prop(1)
    code_pointer_index = cttypes.byte_prop(2)

    def __str__(self):
        ret_str = f"OverworldCodeEntry @ ({self.entry_x:02X}, " \
            f"{self.entry_y:02X}), pointer_id={self.code_pointer_index}"

        return ret_str
        

class OverWorldExitUnknownData(cttypes.BinaryData):
    """Class for holding the unknown part of OW exit packets."""
    SIZE = 4


# TODO: Put this thing in cttypes.py?
class CompressedAbsPtrTableRW:
    """
    Class for reading/writing/freeing compressed data on a CTRom when the data
    records are located by an absolute (3-byte) pointer table.
    """
    def __init__(self, ptr_table_ptr: int,
                 num_pointers: Optional[int] = None):
        """
        Initialize the RW with a position on the ROM which contains the address
        of an absolute (3-byte) pointer table.

        Example.
          The code "$C22A5D  BF C0 FF C6     LDA $C6FFC0,X" is a lookup into
          the location exit pointer table.  So we would provide ptr_table_ptr
          as 0x0C22A5E to read "C0 FF C6" (0x06FFC0) as the start of the
          pointer table.

        Optionally, provide the number of pointers.  Will raise IndexError
        if a pointer outside of range(num_pointers) is accessed.
        """
        self.ptr_table_ptr = ptr_table_ptr
        self.num_pointers = num_pointers

    def _get_ptr_addr(self, ct_rom: ctrom.CTRom, ptr_index: int):
        if (
                self.num_pointers is not None and
                ptr_index not in range(self.num_pointers)
        ):
            raise IndexError(f'{ptr_index} not in range({self.num_pointers})')

        ptr_table_st = byteops.file_ptr_from_rom(
            ct_rom.getbuffer(), self.ptr_table_ptr)

        # print(f'ptr table start: {ptr_table_st:06X}')

        return ptr_table_st + 3*ptr_index

    def _get_ptr(self, ct_rom: ctrom.CTRom, ptr_index: int) -> int:
        ptr_addr = self._get_ptr_addr(ct_rom, ptr_index)
        ptr = byteops.file_ptr_from_rom(
            ct_rom.getbuffer(), ptr_addr)
        return ptr

    def read_data_from_ctrom(self,
                             ct_rom: ctrom.CTRom,
                             record_index: int = 0) -> bytes:
        """Reads a data record from the CTRom."""
        ptr = self._get_ptr(ct_rom, record_index)

        # print(f'ptr: {ptr:06X}')
        data = ctcompression.decompress(ct_rom.getbuffer(), ptr)

        return data


    def free_data_on_ct_rom(self, ct_rom: ctrom.CTRom,
                            record_index: int):
        """Frees the existing data record on the CTRom."""
        ptr = self._get_ptr(ct_rom, record_index)
        existing_size = ctcompression.get_compressed_length(
            ct_rom.getbuffer(), ptr
        )

        mark_free = ctrom.freespace.FSWriteType.MARK_FREE
        ct_rom.space_manager.mark_block(
            (ptr, ptr+existing_size), mark_free
        )
        
    def write_data_to_ct_rom(self,
                             ct_rom: ctrom.CTRom,
                             data: bytearray,
                             record_index: int,
                             free_existing: bool = True):
        """Writes a new data record to the CTRom."""
        if free_existing:
            self.free_data_on_ct_rom(ct_rom, record_index)

        ptr_addr = self._get_ptr_addr(ct_rom, record_index)
        ptr = byteops.file_ptr_from_rom(ct_rom.getbuffer(), ptr_addr)

        compressed_data = ctcompression.compress(data)
        new_ptr = ct_rom.space_manager.get_free_addr(
            len(compressed_data)
        )

        mark_used = ctrom.freespace.FSWriteType.MARK_USED
        ct_rom.seek(new_ptr)
        ct_rom.write(compressed_data, mark_used)

        ct_rom.seek(ptr_addr)
        new_rom_ptr_b = int.to_bytes(byteops.to_rom_ptr(new_ptr), 3, 'little')
        ct_rom.write(new_rom_ptr_b, mark_used)


_owexitpacket_rw = CompressedAbsPtrTableRW(0x022A5E)
class OverworldExitPacket:
    """
    Class to handle the entire overworld exit packet.  Includes exits, code
    entries, and code pointers.
    """
    def __init__(self, data: bytes):
        """
        Construct an OverworldEventPacket from binary data.

        Data follows the format of a decompressed packet from the rom.
          - Number of exits (1 byte)
          - OverworldExit data (7 bytes each)
          - Number of OverworldCodeEntry
          - OverworldCodeEntry data (3 bytes each)
          - Unknown Data - Always 01 01 00 00 (4 bytes)
          - Number of code pointers (1 byte)
          - Code pointers (2 bytes each).
              Note that code pointers are offsets into 0x7F0000 rather than
              the event code.  Event code starts at 0x7F0400 so a code pointer
              of 0x0400 would be pointing to the first command (0x0000) in the
              event.
        """
        self.exits: list[OverworldExit]
        self.entries: list[OverworldCodeEntry]
        self.unknown_data: OverWorldExitUnknownData
        self.code_pointers: list[int]

        num_exits = data[0]
        size = OverworldExit.SIZE
        pos = 1
        self.exits = [
            OverworldExit(data[1+ind*size:1+(ind+1)*size])
            for ind in range(num_exits)
        ]
        pos += num_exits*size

        num_entries = data[pos]
        pos += 1
        size = OverworldCodeEntry.SIZE
        self.entries = [
            OverworldCodeEntry(data[pos+ind*size:pos+(ind+1)*size])
            for ind in range(num_entries)
        ]

        pos = pos + num_entries*size
        if data[pos] != 1:
            raise ValueError(f"Expected 1 Unknown record, got {data[pos]}")

        self.unknown_data = OverWorldExitUnknownData(data[pos:pos+4])
        pos += 4

        num_code_pointers = data[pos]
        pos += 1
        self.code_pointers = [
            int.from_bytes(data[pos+2*ind:pos+2*(ind+1)], 'little')
            for ind in range(num_code_pointers)
        ]
        pos += 2*num_code_pointers

        if pos != len(data):
            byteops.print_bytes(data[pos:], 16)
            raise ValueError("Data longer than expected.")

    def get_bytes(self) -> bytearray:
        """Return (uncompressed) binary representation of this object"""
        ret_b = bytearray()
        ret_b.append(len(self.exits))
        ret_b.extend(b''.join(owexit[:] for owexit in self.exits))

        ret_b.append(len(self.entries))
        ret_b.extend(b''.join(entry[:] for entry in self.entries))

        ret_b.extend(self.unknown_data[:])

        ret_b.append(len(self.code_pointers))
        ret_b.extend(
            b''.join(pointer.to_bytes(2, 'little')
                     for pointer in self.code_pointers)
        )

        return ret_b

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom,
                        packet_id: int) -> OverworldExitPacket:
        """Read an OverworldExitPacket from CTRom."""

        return OverworldExitPacket(
            _owexitpacket_rw.read_data_from_ctrom(ct_rom, packet_id)
        )

    @classmethod
    def free_data_on_ct_rom(cls, ct_rom: ctrom.CTRom,
                            packet_id: int):
        """Read an OverworldExitPacket from CTRom."""
        _owexitpacket_rw.free_data_on_ct_rom(ct_rom, packet_id)

    def write_data_to_ct_rom(
            self, ct_rom: ctrom.CTRom,
            packet_id: int,
            free_existing: bool = True):
        """Write this packet to the CTRom)."""
        _owexitpacket_rw.write_data_to_ct_rom(
            ct_rom, self.get_bytes(), packet_id, free_existing
        )

    def __str__(self):
        ret_str = 'Exits:\n'
        for ind, owexit in enumerate(self.exits):
            ret_str += f"  {ind:02X}: {str(owexit)}\n"

        if self.entries:
            ret_str += 'Code Entries:\n'
            for ind, entry in enumerate(self.entries):
                ret_str += f"  {entry}\n"

        if self.code_pointers:
            ret_str += "Code Pointers\n"
            for ind, code_pointer in enumerate(self.code_pointers):
                ret_str += f"  {ind:02X}: {code_pointer:04X}"

        return ret_str

def main():
    ct_rom = ctrom.CTRom.from_file('./ct.sfc')

    ow_rw = CompressedAbsPtrTableRW(0x022A5E)
    data = ow_rw.read_data_from_ctrom(ct_rom, 1)

    exits = OverworldExitPacket(data)

    exits_2 = OverworldExitPacket(exits.get_bytes())
    
    print(exits.get_bytes() == exits_2.get_bytes())

if __name__ == '__main__':
    main()

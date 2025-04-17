"""
Module for basic operations on a Chrono Trigger ROM.
"""
import hashlib
import typing

from ctrando.common import freespace


class InvalidRomException(Exception):
    """Exception to raise when a rom file is not recognizable as a CT rom."""


class CTRom(freespace.FSRom):
    """
    Class for storing and modifying a CT rom and tracking its free space.
    """

    def __init__(self, rom: typing.ByteString, ignore_checksum=False):
        # ignore_checksum is so that I can load already-randomized roms
        # if need be.
        if not ignore_checksum and not CTRom.validate_ct_rom_bytes(rom):
            raise InvalidRomException("Bad checksum.")

        freespace.FSRom.__init__(self, rom, False)

    @classmethod
    def from_file(cls, filename: str, ignore_checksum=False):
        """
        Read a CT rom from the given file name.
        """
        with open(filename, "rb") as infile:
            rom_bytes = infile.read()

        return cls(rom_bytes, ignore_checksum)

    @staticmethod
    def validate_ct_rom_file(filename: str) -> bool:
        with open(filename, "rb") as infile:
            hasher = hashlib.md5()

            infile.seek(0, 2)
            file_size = infile.tell()

            if file_size == 4194816:
                infile.seek(0x200)

            chunk_size = 8192

            infile.seek(0)
            chunk = infile.read(chunk_size)
            while chunk:
                hasher.update(chunk)
                chunk = infile.read(chunk_size)

            return hasher.hexdigest() == "a2bc447961e52fd2227baed164f729dc"

    @staticmethod
    def validate_ct_rom_bytes(rom: bytes) -> bool:
        hasher = hashlib.md5()
        # Check if this is the size of a headered ROM.
        # If it is, strip off the header before hashing.
        if len(rom) == 4194816:
            rom = rom[0x200:]

        chunk_size = 8192
        start = 0

        while start < len(rom):
            hasher.update(rom[start : start + chunk_size])
            start += chunk_size

        return hasher.hexdigest() == "a2bc447961e52fd2227baed164f729dc"

    def fix_snes_checksum(self):
        if len(self.getbuffer()) == 0x400000:
            exhirom = False
        elif len(self.getbuffer()) == 0x600000:
            exhirom = True
        else:
            raise InvalidRomException("Invalid ROM size.")

        # Write dummy checksums that add up to 0xFFFF like they ought.
        self.seek(0xFFDC)
        self.write(int(0xFFFF0000).to_bytes(4, "little"))

        if exhirom:
            self.seek(0x40FFDC)
            self.write(int(0xFFFF0000).to_bytes(4, "little"))

        def get_checksum(byte_seq: bytes) -> int:
            # return functools.reduce(
            #     lambda x, y: (x+y) % 0x10000,
            #     byte_seq,
            #     0
            # )
            return sum(byte_seq) % 0x10000

        # Compute the checksum of the first 0x400000
        checksum = get_checksum(self.getbuffer()[0:0x400000])

        # Compute twice the expanded 2MB if exhirom
        if exhirom:
            checksum += 2 * get_checksum(self.getbuffer()[0x400000:0x600000])
            checksum = checksum % 0x10000

        inverse_checksum = checksum ^ 0xFFFF
        checksum_b = inverse_checksum.to_bytes(2, "little") + checksum.to_bytes(
            2, "little"
        )

        # Write correct checksum out -- should auto-mirror for exhirom
        self.seek(0xFFDC)
        self.write(checksum_b)

        # Mirror in bank 0x40 if exhirom
        # if exhirom:
        #     self.seek(0x40FFDC)
        #     self.write(checksum_b)

    def is_expanded(self):
        return len(self.getbuffer()) == 0x600000

    def make_exhirom(self):
        """
        Turns a HiROM CTRom into an ExHiROM CTRom.

        Throws an exception if the rom is not HiROM
        """

        def header_is_hirom(buffer) -> bool:
            if buffer[0xFFD5] != 0x31 or buffer[0xFFD7] != 0x0C:
                return False
            return True

        if len(self.getbuffer()) != 0x400000 or not header_is_hirom(self.getbuffer()):
            raise InvalidRomException("Existing ROM not HiRom")

        # ROM type:  Old value was 0x31 - HiROM + fastrom
        #            New value is  0x35 for ExHiROM
        self.seek(0xFFD5)
        super().write(b"\x35")

        # ROM size:  Old value was 0x0C - 4Mbit (why?)
        #            New value is  0x0D
        # I don't know how the value is determined, but ok.
        self.seek(0xFFD7)
        super().write(b"\x0D")

        FSW = freespace.FSWriteType
        # Mirror [0x008000, 0x010000) to [0x408000, 0x410000)
        self.seek(0x008000)
        mirror_bytes = self.read(0x8000)

        # 00s to [0x400000, 0x408000)
        self.seek(0x400000)
        super().write(b"\x00" * 0x8000, FSW.MARK_FREE)
        # Mirror
        super().write(mirror_bytes, FSW.MARK_USED)
        super().write(b"\x00" * 0x1F0000, FSW.MARK_FREE)

        self.fix_snes_checksum()

    # TODO: Write tests for the overlap methods.
    @staticmethod
    def _get_overlap(st_1, end_1, st_2, end_2) -> tuple[int, int]:
        """Assumes overlap exists"""
        start = max(st_1, st_2)
        end = min(end_1, end_2) + 1
        return (start, end)

    @staticmethod
    def _has_overlap(st_1, end_1, st_2, end_2) -> bool:
        # No overlap: end1 <= st2 OR st1 >= end2 (half-open)
        # Then use DeMorgan
        return end_2 > st_1 and st_2 < end_1

    def _write_mirror(
        self,
        payload,
        start: int,
        over_st: int,
        over_end: int,
        write_mark: freespace.FSWriteType,
    ):
        if 0x008000 <= (start + over_st) < 0x010000:
            shift = 0x400000
        elif 0x408000 <= (start + over_st) < 0x410000:
            shift = -0x400000
        else:
            raise ValueError

        self.seek(start + over_st + shift)
        # print(f'Mirroring [{start+over_st:06X}, {start+over_end:06X}) to '
        #       f'[{start + over_st +shift:06X}, {start+over_end+shift:06X})')
        super().write(payload[over_st:over_end], write_mark)

    def write(
        self, payload, write_mark: freespace.FSWriteType = freespace.FSWriteType.NO_MARK
    ):
        """
        FSRom write but mirrors [0x008000, 0x010000) w/ [0x408000, 0x410000)
        """
        start = self.tell()
        end = start + len(payload)

        has_overlap = self._has_overlap(start, end, 0x008000, 0x010000)
        has_mirror_overlap = self._has_overlap(start, end, 0x480000, 0x410000)

        # print(f'{start:06X}:{end:06X}', has_overlap, has_mirror_overlap)

        if not (has_overlap or has_mirror_overlap) or not self.is_expanded():
            super().write(payload, write_mark)
        elif has_overlap and has_mirror_overlap:
            # If it overlaps the mirrored region and its mirror, the two
            # need to agree.
            over_st, over_end = self._get_overlap(start, end, 0x008000, 0x010000)
            over_st -= start
            over_end -= start
            over_b = payload[over_st, over_end]

            over_m_st, over_m_end = self._get_overlap(start, end, 0x408000, 0x410000)
            over_m_st -= start
            over_m_end -= start
            over_m_b = payload[over_m_st, over_m_end]

            if not over_b == over_m_b:
                raise ValueError("Inconsistent write to mirrored region.")
            super().write(payload, write_mark)
        elif has_overlap:
            # Copy the write to the mirror in the expanded part
            over_st, over_end = self._get_overlap(start, end, 0x008000, 0x010000)
            over_st -= start
            over_end -= start

            self._write_mirror(payload, start, over_st, over_end, write_mark)
            self.seek(start)
            super().write(payload, write_mark)
        else:
            # Copy the write to the mirrored region in the normal part
            over_m_st, over_m_end = self._get_overlap(start, end, 0x408000, 0x410000)
            over_m_st -= start
            over_m_end -= start

            self._write_mirror(payload, start, over_m_st, over_m_end, write_mark)
            self.seek(start)
            super().write(payload, write_mark)

        # assert (
        #     self.getbuffer()[0x008000:0x010000]
        #     == self.getbuffer()[0x408000:0x410000]
        # )


def main():
    pass


if __name__ == "__main__":
    main()

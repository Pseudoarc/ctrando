"""Module for dealing with Battle Messages used by AI Scripts."""
import io
import typing

from ctrando.common import byteops, cttypes as ctty, ctrom, freespace
from ctrando.common.cttypes import T, RomRW
from ctrando.strings import ctstrings


class BattleMessageRW(ctty.RomRW):
    """Class for reading/writing/freeing battle messages"""
    def __init__(self,
                 ptr_bank_addr: int = 0x0D02A0,
                 ptr_offset_addr: int = 0x0D0299):
        """
        Battle Messages are accessed via local pointers.
        - ptr_bank_addr is an address on the ct_rom which contains the bank in which
          the battle messages and battle message pointers live.
        - ptr_offset_addr is an address on the ct_rom which begins a two-byte offset
          for the start of the pointer table.
        """
        self.ptr_bank_addr = ptr_bank_addr
        self.ptr_offset_addr = ptr_offset_addr

    def get_ptr_table_start(self, ct_rom: ctrom.CTRom) -> int:
        """Returns the start of the pointer table on ct_rom"""
        buf = ct_rom.getbuffer()
        bank = buf[self.ptr_bank_addr] * 0x10000
        offset = int.from_bytes(
            buf[self.ptr_offset_addr: self.ptr_offset_addr+2], "little"
        )

        return byteops.to_file_ptr(bank+offset)

    def get_record_start(self, ct_rom: ctrom.CTRom, record_num: int):
        """Returns the start of a record"""
        ptr_loc = self.get_ptr_table_start(ct_rom) + 2 * record_num
        buf = ct_rom.getbuffer()
        offset = int.from_bytes(buf[ptr_loc: ptr_loc+2], "little")
        message_loc = (ptr_loc & 0xFF0000) + offset

        return message_loc

    @staticmethod
    def get_record_size(ct_rom: ctrom.CTRom, pos: int) -> int:
        """
        Returns the end of a record beginning at pos
        """
        return byteops.get_string_length(ct_rom.getbuffer(), pos, 0)

    def read_data_from_ctrom(self,
                             ct_rom: ctrom.CTRom,
                             num_bytes: typing.Optional[int] = None,
                             record_num: int = 0) -> bytes:
        message_loc = self.get_record_start(ct_rom, record_num)

        if num_bytes is None:
            num_bytes = self.get_record_size(ct_rom, message_loc)

        ct_rom.seek(message_loc)
        return ct_rom.read(num_bytes)

    def write_data_to_ct_rom(self,
                             ct_rom: ctrom.CTRom,
                             data: typing.ByteString,
                             record_num: int = 0):
        ptr_table_addr = byteops.to_file_ptr(self.get_ptr_table_start(ct_rom))
        bank = ptr_table_addr & 0xFF0000

        message_loc = ct_rom.space_manager.get_free_addr(len(data), bank)
        if message_loc & 0xFF0000 != bank:
            raise freespace.FreeSpaceError("No Space in Bank.")

        ct_rom.seek(message_loc)
        ct_rom.write(data, freespace.FSWriteType.MARK_USED)

    def free_data_on_ct_rom(self, ct_rom: ctrom.CTRom,
                            num_bytes: int, record_num: int = 0):
        message_loc = self.get_record_start(ct_rom.getbuffer(), record_num)
        message_len = self.get_record_size(ct_rom.getbuffer(), message_loc)

        ct_rom.space_manager.mark_block(
            (message_loc, message_loc+message_len), freespace.FSWriteType.MARK_FREE
        )


T = typing.TypeVar('T', bound='BattleMessage')


class BattleMessage(ctty.BinaryData):
    ROM_RW = BattleMessageRW()

    @classmethod
    def from_string(cls, string: str) -> 'BattleMessage':
        """Create a BattleMessage from a Python string"""
        ct_str = ctstrings.CTString.from_str(string)
        if ct_str[-1] != 0:
            ct_str.append(0)
        return BattleMessage(ct_str)

    @classmethod
    def read_from_ctrom(cls: typing.Type[T], ct_rom: ctrom.CTRom, record_num: int = 0,
                        rom_rw: typing.Optional[RomRW] = None) -> T:
        data = cls.ROM_RW.read_data_from_ctrom(ct_rom, record_num=record_num)
        return cls(data)

    def write_to_ctrom(
            self, ct_rom: ctrom.CTRom,
            record_num: int = 0,
            rom_rw: typing.Optional[RomRW] = None):
        if rom_rw is None:
            rom_rw = self.ROM_RW
        rom_rw.write_data_to_ct_rom(ct_rom, self, record_num)


    @classmethod
    def free_data_on_ct_rom(
            cls, ct_rom: ctrom.CTRom,
            record_num: int = 0,
            rom_rw: typing.Optional[RomRW] = None):
        if rom_rw is None:
            rom_rw = cls.ROM_RW

    def __str__(self):
        return ctstrings.CTString.ct_bytes_to_ascii(self)


class BattleMessageManager:
    """Class for keeping track of battle messages."""
    def __init__(self, message_dict: dict[int, str]):
        self.message_dict = {
            key: BattleMessage.from_string(val) for (key, val) in message_dict.items()
        }


    @classmethod
    def read_from_ct_rom(cls, ct_rom: ctrom.CTRom, num_messages: int = 0xE3) -> 'BattleMessageManager':
        """
        Read all battle messages from a ct_rom.
        There is no easy way to get the maximum number of messages.  Vanilla is 0xE3.
        """

        bm_man = cls(dict())

        message_dict = {
            ind: BattleMessage.read_from_ctrom(ct_rom, ind)
            for ind in range(num_messages)
        }
        bm_man.message_dict = message_dict

        return bm_man

    @classmethod
    def free_existing_battle_messages(
            cls,
            ct_rom: ctrom.CTRom, num_messages: int = 0xE3,
            free_ptr_table: bool = True
    ):
        """
        Free all battle messages on the given ct_rom.
        """

        for ind in range(num_messages):
            BattleMessage.free_data_on_ct_rom(ct_rom, ind)

        if free_ptr_table:
            ptr_table_start = BattleMessage.ROM_RW.get_ptr_table_start(ct_rom)
            ct_rom.space_manager.mark_block(
                (ptr_table_start, ptr_table_start+2*num_messages),
                freespace.FSWriteType.MARK_FREE
            )

    @classmethod
    def _update_references(cls, ct_rom: ctrom.CTRom, new_ptr_table_start: int):
        """
        Update the ct_rom to look in a new spot for pointers.
        """

        # Only reference?
        # CD0298  A2 C9 CB       LDX #$CBC9  <-- Offset
        # CD029B  8E 0D 02       STX $020D
        # CD029E  48             PHA
        # CD029F  A9 CC          LDA #$CC    <-- Bank
        # CD02A1  8D 0F 02       STA $020F

        rom_addr = byteops.to_rom_ptr(new_ptr_table_start)
        offset = rom_addr & 0x00FFFF
        bank = rom_addr >> 16

        ct_rom.seek(0x0D0299)
        ct_rom.write(offset.to_bytes(2, "little"))
        ct_rom.seek(0x0D02A0)
        ct_rom.write(bank.to_bytes(1))

    def __getitem__(self, item: int) -> str:
        return str(self.message_dict[item])


    def __setitem__(self, item: int, val: str):
        if not val.lower().endswith("{null}"):
            val = val + "{null}"

        self.message_dict[item] = BattleMessage.from_string(val)


    def write_to_ct_rom(self, ct_rom: ctrom.CTRom, hint: int = 0x410000):
        """
        Write all battle messages to ct_rom and update references.
        """
        vanilla_num_ptrs = 0xE3

        for ind in range(vanilla_num_ptrs):
            if ind not in self.message_dict:
                self.message_dict[ind] = BattleMessage.read_from_ctrom(ct_rom, ind)

        max_ind = max(self.message_dict.keys())
        num_ptrs = max_ind +1
        if num_ptrs > 0x100:
            raise ValueError

        out_buf = io.BytesIO()
        ptrs: list[int] = []
        for ind in range(num_ptrs):
            ptrs.append(out_buf.tell())
            if ind in self.message_dict:
                out_buf.write(self.message_dict[ind])

        ptr_size = 2*num_ptrs
        total_size = ptr_size+len(out_buf.getbuffer())

        new_start = ct_rom.space_manager.get_free_addr(total_size, hint)
        offset = (new_start & 0xFFFF) + 2*num_ptrs
        ptr_b = b"".join(
            int.to_bytes(ptr+offset, 2, "little")
            for ptr in ptrs
        )
        ct_rom.seek(new_start)
        ct_rom.write(ptr_b, freespace.FSWriteType.MARK_USED)
        ct_rom.write(out_buf.getbuffer(), freespace.FSWriteType.MARK_USED)

        self._update_references(ct_rom, new_start)
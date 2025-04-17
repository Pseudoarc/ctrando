import copy
from typing import Optional

from ctrando.common import byteops
from ctrando.overworlds.overworld import Overworld
from ctrando.common import ctenums, ctrom
from ctrando.strings import ctstrings

class OWManager:
    """Class which keeps track of overworld data."""
    def __init__(
            self,
            ct_rom: ctrom.CTRom,
            overworld_dict: Optional[dict[ctenums.OverWorldID,
                                          Overworld]] = None,
            name_dict: Optional[dict[int, str]] = None
    ):
        if overworld_dict is None:
            overworld_dict = {}
        if name_dict is None:
            name_dict = {}

        self.overworld_dict: dict[ctenums.OverWorldID, Overworld] = {}
        for ow_id in ctenums.OverWorldID:
            if ow_id in overworld_dict:
                self.overworld_dict[ow_id] = copy.deepcopy(overworld_dict[ow_id])
            else:
                self.overworld_dict[ow_id] = Overworld.read_from_ctrom(ct_rom, ow_id)

        num_names = 0x70
        self.name_dict = self._read_name_dict(ct_rom, num_names)
        self.name_dict.update(name_dict)
        self._ct_rom = ct_rom

    @staticmethod
    def _read_name_dict(ct_rom: ctrom.CTRom, num_names: int) -> dict[int, str]:
        """Read the names as strings."""
        ret_dict: dict[int, str] = dict()

        # C2567A  A2 00 F4       LDX #$F400
        # C2567D  8E 0D 02       STX $020D
        # C25680  A9 C6          LDA #$C6
        # C25682  8D 0F 02       STA $020F
        ct_rom.seek(0x02567B)
        offset = int.from_bytes(ct_rom.read(2), "little")
        bank = ct_rom.getbuffer()[0x025681] * 0x10000
        ptr_table_addr = byteops.to_file_ptr(bank + offset)

        for ind in range(num_names):
            ct_rom.seek(ptr_table_addr + 2*ind)
            offset = int.from_bytes(ct_rom.read(2), "little")
            ct_rom.seek(byteops.to_file_ptr(bank+offset))
            name_b = ct_rom.read(0x20)
            name_b = name_b[:name_b.index(0)]
            name = ctstrings.CTString.ct_bytes_to_ascii(name_b)
            ret_dict[ind] = name

        return ret_dict

    @staticmethod
    def _write_exit_names_to_ctrom(name_dict: dict[int, str], ct_rom: ctrom.CTRom):
        """Write names back to CT Rom and update pointers"""

        # Free old
        num_names = 0x70
        ct_rom.seek(0x02567B)
        offset = int.from_bytes(ct_rom.read(2), "little")
        bank = ct_rom.getbuffer()[0x025681] * 0x10000
        ptr_table_addr = byteops.to_file_ptr(bank + offset)

        ct_rom.space_manager.mark_block(
            (ptr_table_addr,  ptr_table_addr+num_names*2),
            ctrom.freespace.FSWriteType.MARK_FREE
        )

        ct_rom.seek(ptr_table_addr)
        name_st = ptr_table_addr & 0xFF0000 + int.from_bytes(ct_rom.read(2), "little")
        ct_rom.seek(ptr_table_addr + (num_names-1)*2)
        last_name_st = ptr_table_addr & 0xFF0000 + int.from_bytes(ct_rom.read(2), "little")
        ct_rom.seek(last_name_st)
        last_name_b = ct_rom.read(0x20).split(b'\x00')[0]
        name_end = last_name_st + len(last_name_b) + 1
        ct_rom.space_manager.mark_block(
            (name_st, name_end), ctrom.freespace.FSWriteType.MARK_FREE
        )

        payload = bytearray()
        offsets: list[int] = [0]
        for ind in range(0x70):
            name_str = name_dict.get(ind, "") + "{null}"
            name_b = ctstrings.CTString.from_str(name_str, True)
            payload.extend(name_b)
            offsets.append(offsets[-1] + len(name_b))

        len_offsets = 0x70*2
        total_size = len_offsets + len(payload)

        new_name_st = ct_rom.space_manager.get_free_addr(total_size, 0x410000)
        cur_name_ptr = new_name_st + num_names*2
        new_ptr_table_st = byteops.to_rom_ptr(new_name_st)
        ct_rom.seek(new_name_st)
        for offset in offsets[:-1]:
            offset = (offset + cur_name_ptr) & 0xFFFF
            ct_rom.write(int.to_bytes(offset, 2, "little"),
                         ctrom.freespace.FSWriteType.MARK_USED)

        ct_rom.write(payload, ctrom.freespace.FSWriteType.MARK_USED)

        # C2567A  A2 00 F4       LDX #$F400
        # C2567D  8E 0D 02       STX $020D
        # C25680  A9 C6          LDA #$C6
        # C25682  8D 0F 02       STA $020F
        ct_rom.seek(0x02567B)
        ct_rom.write(int.to_bytes(new_ptr_table_st & 0xFFFF, 2, "little"))
        ct_rom.getbuffer()[0x025681] = new_ptr_table_st // 0x10000

    def __getitem__(self, key: ctenums.OverWorldID) -> Overworld:
        if key in self.overworld_dict:
            return self.overworld_dict[key]

        ow_data = Overworld.read_from_ctrom(self._ct_rom, key)
        self.overworld_dict[key] = ow_data
        return ow_data

    def __setitem__(self, key: ctenums.OverWorldID, value: Overworld):
        self.overworld_dict[key] = value

    def __delitem__(self, key: ctenums.OverWorldID):
        del self.overworld_dict[key]

    def add_ow_exit_name(self, name: str, find_existing: bool = False) -> int:
        """Adds a name.  Returns its name index."""
        for ind in reversed(range(0x6A)):
            if self.name_dict[ind] == "":
                self.name_dict[ind] = name
                return ind

        raise ValueError

    def write_overworld(self, overworld_id: ctenums.OverWorldID):
        if overworld_id not in self.overworld_dict:
            raise KeyError

        ow_data = self.overworld_dict[overworld_id]
        ow_data.write_to_ctrom(self._ct_rom, overworld_id)

    def write_all_overworlds_to_ctrom(self):
        for overworld_id in self.overworld_dict:
            self.write_overworld(overworld_id)

        self._write_exit_names_to_ctrom(self.name_dict, self._ct_rom)
"""Module to handle modification of CT Overworlds"""
from __future__ import annotations

from ctrando.common import ctrom, cttypes
from ctrando.overworlds import owevent, owexits


class OverWorldHeader(cttypes.BinaryData):
    ROM_RW = cttypes.LocalPointerRW(0x022764, 0x06FD00)
    SIZE = 0x17

    tileset_1 = cttypes.byte_prop(0, 0x7F)
    tileset_1_unused = cttypes.byte_prop(0, 0x80)

    tileset_2 = cttypes.byte_prop(1, 0x7F)
    tileset_2_unused = cttypes.byte_prop(1, 0x80)

    tileset_3 = cttypes.byte_prop(2, 0x7F)
    tileset_3_unused = cttypes.byte_prop(2, 0x80)

    tileset_4 = cttypes.byte_prop(3, 0x7F)
    tileset_4_unused = cttypes.byte_prop(3, 0x80)

    tileset_5 = cttypes.byte_prop(4, 0x7F)
    tileset_5_unused = cttypes.byte_prop(4, 0x80)

    tileset_6 = cttypes.byte_prop(5, 0x7F)
    tileset_6_unused = cttypes.byte_prop(5, 0x80)

    tileset_7 = cttypes.byte_prop(6, 0x7F)
    tileset_7_unused = cttypes.byte_prop(6, 0x80)

    tileset_8 = cttypes.byte_prop(7, 0x7F)
    tileset_8_unused = cttypes.byte_prop(7, 0x80)

    layer3_tileset = cttypes.byte_prop(8, 0x7F)
    layer3_tileset_unused = cttypes.byte_prop(8, 0x80)

    # Overworld Data	09	FF	1	Ignored	2004.04.26
    layer12_palette = cttypes.byte_prop(0xA)
    ocean_palette = cttypes.byte_prop(0xB)

    sprites_1 = cttypes.byte_prop(0xC, 0x7F)
    sprites_1_unused = cttypes.byte_prop(0xC, 0x80)

    sprites_2 = cttypes.byte_prop(0xD, 0x7F)
    sprites_2_unused = cttypes.byte_prop(0xD, 0x80)

    sprites_3 = cttypes.byte_prop(0xE, 0x7F)
    sprites_3_unused = cttypes.byte_prop(0xE, 0x80)

    sprites_4 = cttypes.byte_prop(0xF, 0x7F)
    sprites_5_unused = cttypes.byte_prop(0xF, 0x80)

    tile_assembly = cttypes.byte_prop(0x10)
    map_index = cttypes.byte_prop(0x11)
    tile_properties_index = cttypes.byte_prop(0x12)
    music_transition = cttypes.byte_prop(0x13)
    tile_assembly_l3 = cttypes.byte_prop(0x14)
    location_exit_index = cttypes.byte_prop(0x15)
    event_index = cttypes.byte_prop(0x16, 0x7F)
    events_unused = cttypes.byte_prop(0x16, 0x80)


class Overworld:
    """
    Combine all data used by an overworld.
    """
    def __init__(
            self,
            header: OverWorldHeader,
            ow_exit_data: owexits.OverworldExitPacket,
            ow_event: owevent.OverworldEvent
    ):
        self.header = header
        self.exit_data = ow_exit_data
        self.event = ow_event

        self._code_ptr_labels: dict[int, str] = {}
        self._set_code_pointer_labels()

    def get_code_ptr_label(self, index: int) -> str:
        return self._code_ptr_labels[index]

    def _set_code_pointer_labels(self):
        offset = 0x0400
        found_count = 0
        for ind, command in enumerate(self.event.commands):
            if offset in self.exit_data.code_pointers:
                code_ptr_ind = self.exit_data.code_pointers.index(offset)
                label = self.event.get_label(ind)
                self._code_ptr_labels[code_ptr_ind] = label
                found_count += 1
            offset += len(command)

        # if found_count != len(self.exit_data.code_pointers):
        #     print(', '.join(f'{ptr:04X}' for ptr in self.exit_data.code_pointers))
        #     raise ValueError("Not all code pointers are offsets")

    def _update_code_pointers(self):
        cmd_ind_to_ptr_ind: dict[int, int] = {}
        for ind, label in self._code_ptr_labels.items():
            target_ind = self.event.labels[label]
            cmd_ind_to_ptr_ind[target_ind] = ind

        offset = 0x400
        found_count = 0
        for ind, command in enumerate(self.event.commands):
            if ind in cmd_ind_to_ptr_ind:
                code_ptr_ind = cmd_ind_to_ptr_ind[ind]
                self.exit_data.code_pointers[code_ptr_ind] = offset
                found_count += 1

            offset += len(command)

        # if found_count != len(self.exit_data.code_pointers):
        #     raise ValueError("Not all code pointers are offsets")

    @classmethod
    def read_from_ctrom(
            cls, ct_rom: ctrom.CTRom,
            overworld_id: int) -> Overworld:
        """Read an Overworld from a CTRom"""
        header = OverWorldHeader.read_from_ctrom(ct_rom, overworld_id)
        exits = owexits.OverworldExitPacket.read_from_ctrom(
            ct_rom, overworld_id)
        event_id = header.event_index
        event = owevent.OverworldEvent.read_from_ctrom(ct_rom, event_id)

        return Overworld(header, exits, event)

    @classmethod
    def free_data_on_ct_rom(cls, ct_rom: ctrom.CTRom, overworld_id: int):
        header = OverWorldHeader.read_from_ctrom(ct_rom, overworld_id)

        owexits.OverworldExitPacket.free_data_on_ct_rom(ct_rom, overworld_id)
        event_id = header.event_index
        owevent.OverworldEvent.free_data_on_ctrom(ct_rom, event_id)

    def write_to_ctrom(self, ct_rom: ctrom.CTRom, overworld_id: int,
                       free_existing: bool = True):
        """Write this Overworld to the CTRom."""
        self.header.write_to_ctrom(ct_rom, overworld_id)

        self._update_code_pointers()
        self.exit_data.write_data_to_ct_rom(ct_rom, overworld_id,
                                            free_existing)
        event_id = self.header.event_index
        self.event.write_to_ctrom(ct_rom, event_id, free_existing)

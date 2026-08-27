"""Module for modifying Location Maps"""
import typing

from ctrando.common import byteops, ctenums, ctrom, cttypes
from ctrando.compression import ctcompression
from ctrando.locations import locationtypes

_MAP_PTR_TABLE_START: typing.Final = 0x361E00


def get_map_ptr_address(rom: typing.ByteString, map_id: int):
    """
    Get the address of a map pointer.
    """
    return _MAP_PTR_TABLE_START + 3*map_id


def get_map_ptr(rom: typing.ByteString, map_id: int):
    """
    Get the start address (file, not rom) for the given map.
    """
    ptr_addr = _MAP_PTR_TABLE_START + 3*map_id
    rom_ptr = int.from_bytes(rom[ptr_addr:ptr_addr+3], 'little')
    file_ptr = byteops.to_file_ptr(rom_ptr)

    return file_ptr


def set_map_ptr(ct_rom: ctrom.CTRom, map_id: int, file_ptr: int):
    """
    Set the start address for the given map.

    Note: file_ptr is a position in the file, not the rom.  For example,
          file_ptr=0x000000 instead of 0xC00000.
    """

    FSW = ctrom.freespace.FSWriteType

    ptr_addr = _MAP_PTR_TABLE_START + 3*map_id
    rom_ptr = byteops.to_rom_ptr(file_ptr)
    ct_rom.seek(ptr_addr)
    ct_rom.write(int.to_bytes(rom_ptr, 3, 'little'),
                          FSW.MARK_USED)


def _map_dim_input_filter(self, val: int) -> int:
    val = int(val)
    quot, rem = divmod(val, 16)
    if rem != 0:
        raise ValueError("Map sizes must be multiples of 16")
    if quot <= 0:
        raise ValueError("Map sizes must be positive")

    return quot - 1

def _map_dim_output_filter(self, val: int) -> int:
    return (val+1)*16

class LocationMapHeader(cttypes.BinaryData):
    """
    Location Map Header Data
    Based off of Geiger's original Data Format.txt
    """
    SIZE = 6

    def set_properties(
            self, / ,
            layer_1_width: int | None = None,  layer_1_height: int | None = None,
            layer_2_width: int | None = None, layer_2_height: int | None = None,
            layer_3_width: int | None = None, layer_3_height: int | None = None,
            layer_1_scrolling: int | None = None,
            layer_2_scrolling: int | None = None,
            layer_3_scrolling: int | None = None,
            draw_layer_3: bool | None = None,
            use_layer_1_mainscreen: bool | None = None,
            use_layer_2_mainscreen: bool | None = None,
            use_layer_3_mainscreen: bool | None = None,
            use_sprites_mainscreen: bool | None = None,
            use_layer_1_subscreen: bool | None = None,
            use_layer_2_subscreen: bool | None = None,
            use_layer_3_subscreen: bool | None = None,
            use_sprites_subscreen: bool | None = None,
            enable_layer_1_subscreen_addsub: bool | None = None,
            enable_layer_2_subscreen_addsub: bool | None = None,
            enable_layer_3_subscreen_addsub: bool | None = None,
            unknown_5_08: bool | None = None,
            enable_sprite_subscreen_add_sub: bool | None = None,
            enable_default_color_subscreen_add_sub: bool | None = None,
            half_color: bool | None = None,
            use_subscreen_sub:bool | None = None
    ):
        kwargs = {
            k: v for k, v in locals().items() if v is not None
        }
        for key, val in kwargs.items():
            setattr(self, key, val)

        return self

    layer_1_width = cttypes.byte_prop(
        0, 0x03,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )
    layer_1_height = cttypes.byte_prop(
        0, 0xC,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )

    layer_2_width = cttypes.byte_prop(
        0, 0x30,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )
    layer_2_height = cttypes.byte_prop(
        0, 0xC0,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )

    layer_3_width = cttypes.byte_prop(
        1, 0x03,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )
    layer_3_height = cttypes.byte_prop(
        1, 0xC,
        input_filter=_map_dim_input_filter,
        output_filter=_map_dim_output_filter
    )
    # Location Map	01	70	1	???	2003.11.12
    # Guess Layer 1 Scrolling
    layer_1_scrolling = cttypes.byte_prop(1, 0x70)
    draw_layer_3 = cttypes.byte_prop(1, 0x80)
    # Location Map	02	FF	1	???	2003.07.10
    # Location Map	03	FF	1	???	2003.07.10
    # Guess Layer 2/3 Scrolling
    layer_2_scrolling = cttypes.byte_prop(2, 0xFF)
    layer_3_scrolling = cttypes.byte_prop(3, 0xFF)

    use_layer_1_mainscreen = cttypes.byte_prop(4, 0x01, ret_type=bool)
    use_layer_2_mainscreen = cttypes.byte_prop(4, 0x02, ret_type=bool)
    use_layer_3_mainscreen = cttypes.byte_prop(4, 0x04, ret_type=bool)
    use_sprites_mainscreen = cttypes.byte_prop(4, 0x08, ret_type=bool)
    use_layer_1_subscreen = cttypes.byte_prop(4, 0x10, ret_type=bool)
    use_layer_2_subscreen = cttypes.byte_prop(4, 0x20, ret_type=bool)
    use_layer_3_subscreen = cttypes.byte_prop(4, 0x40, ret_type=bool)
    use_sprites_subscreen = cttypes.byte_prop(4, 0x80, ret_type=bool)
    enable_layer_1_subscreen_addsub = cttypes.byte_prop(5, 0x01, ret_type=bool)
    enable_layer_2_subscreen_addsub = cttypes.byte_prop(5, 0x02, ret_type=bool)
    enable_layer_3_subscreen_addsub = cttypes.byte_prop(5, 0x04, ret_type=bool)
    # Location Map	05	08	1	???	2004.12.03
    unknown_5_08 = cttypes.byte_prop(5, 0x08, ret_type=bool)
    enable_sprite_subscreen_add_sub = cttypes.byte_prop(5, 0x10, ret_type=bool)
    enable_default_color_subscreen_add_sub = cttypes.byte_prop(5, 0x20, ret_type=bool)
    half_color = cttypes.byte_prop(5, 0x40, ret_type=bool)
    use_subscreen_sub = cttypes.byte_prop(5, 0x80, ret_type=bool)


class SolidityType(ctenums.StrIntEnum):
    """Class to hold various tile solidity types."""


class MovementDirection(ctenums.StrIntEnum):
    """Class to encode forced movement direction on a tile."""
    NORTH = 0
    SOUTH = 1
    EAST = 2
    WEST = 3


# Using the 'Data Format.txt' from the database as a basis for this.
class LocationTileProperties(cttypes.BinaryData):
    """Class to hold properties for a tile on a map."""
    SIZE = 3

    l1_use_second_tileset_graphic = cttypes.byte_prop(0, 0x01, ret_type=bool)
    l2_use_second_tileset_graphic = cttypes.byte_prop(0, 0x02, ret_type=bool)
    solidity = cttypes.byte_prop(0, 0x7C)

    movement_direction = cttypes.byte_prop(1, 0x3,
                                           ret_type=MovementDirection)
    movement_speed = cttypes.byte_prop(1, 0x0C)
    is_door = cttypes.byte_prop(1, 0x10, ret_type=bool)
    unused_1_20 = cttypes.byte_prop(1, 0x20, ret_type=bool)
    l1_draw_over = cttypes.byte_prop(1, 0x40, ret_type=bool)
    is_battle_solid = cttypes.byte_prop(1, 0x80, ret_type=bool)

    primary_z_plane = cttypes.byte_prop(2, 0x03)
    ignore_nonprimary_z_solidity = cttypes.byte_prop(2, 0x04)
    solidity_modifier = cttypes.byte_prop(2, 0x18)
    is_z_neutral = cttypes.byte_prop(2, 0x20, ret_type=bool)
    l2_draw_over = cttypes.byte_prop(2, 0x40, ret_type=bool)
    is_npc_solid = cttypes.byte_prop(2, 0x80, ret_type=bool)


class LocationMap:
    """
    Class to hold data for a CT Map.

    Holds tile indices and tile properties.  Does not hold any graphics
    information.
    """

    def __init__(
            self,
            header: LocationMapHeader,
            l1_tiles: bytearray,
            l2_tiles: bytearray,
            l3_tiles: bytearray,
            tile_properties: list[LocationTileProperties]
    ):
        self.header = header
        self.l1_tiles = l1_tiles
        self.l2_tiles = l2_tiles
        self.l3_tiles = l3_tiles
        self.tile_props = list(tile_properties)

    @classmethod
    def from_bytes(cls, map_data: bytes) -> typing.Self:
        header = LocationMapHeader(map_data[0:6])

        num_l1_tiles = header.layer_1_width*header.layer_1_height
        num_l2_tiles = header.layer_2_width*header.layer_2_height

        if header.draw_layer_3:
            num_l3_tiles = header.layer_3_height*header.layer_3_width
        else:
            num_l3_tiles = 0

        start = 6
        l1_tiles = bytearray(map_data[start:start+num_l1_tiles])

        start += num_l1_tiles
        l2_tiles = bytearray(map_data[start: start+num_l2_tiles])

        start += num_l2_tiles
        l3_tiles = bytearray(map_data[start: start+num_l3_tiles])

        tile_props: list[LocationTileProperties] = []
        start += num_l3_tiles
        cur_pos = start
        num_props = 0

        while cur_pos < len(map_data):
            cur_props_b = bytearray(map_data[cur_pos: cur_pos+3])
            cur_props_b[0] &= 0x7F

            if map_data[cur_pos] & 0x80:
                num_reps = map_data[cur_pos+3]
                cur_pos += 4
            else:
                num_reps = 1
                cur_pos += 3

            # print(f'Repeat: {num_reps}')
            tile_props.extend(
                [LocationTileProperties(cur_props_b) for _ in range(num_reps)]
            )
            num_props += num_reps

        return cls(header, l1_tiles, l2_tiles, l3_tiles, tile_props)

    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom, map_id: int) -> 'LocationMap':
        """Read a map from a given slot."""
        map_ptr = get_map_ptr(ct_rom.getbuffer(), map_id)
        map_b = ctcompression.decompress(ct_rom.getbuffer(), map_ptr)
        return cls.from_bytes(map_b)

    @classmethod
    def get_location_map(cls, ct_rom: ctrom.CTRom, loc_id: ctenums.LocID):
        """Read a location's map"""
        loc_data = locationtypes.LocationData.read_from_ctrom(ct_rom, loc_id)
        map_id = loc_data.map_id

        return cls.read_from_ctrom(ct_rom, map_id)

    def _collect_tile_props(self) -> bytearray:
        """
        Convert self.tile_props to a bytearray as it would appear in map data
        on the rom.
        """
        cur_pos = 0

        ret = bytearray()
        while cur_pos < len(self.tile_props):
            cur_props = self.tile_props[cur_pos]
            end_pos = cur_pos + 1

            while (
                    end_pos < len(self.tile_props) and
                    self.tile_props[end_pos] == self.tile_props[cur_pos]
            ):
                end_pos += 1

            num_reps = end_pos - cur_pos

            if num_reps == 1:
                ret.extend(cur_props)
            else:
                next_entry = bytearray(4)
                next_entry[0:3] = cur_props
                next_entry[0] |= 0x80
                next_entry[3] = num_reps
                ret.extend(next_entry)

            cur_pos = end_pos

        return ret

    def get_as_bytearray(self) -> bytearray:
        """
        Get a bytearray of this object usable by CT when compressed.
        """
        ret_b = bytearray()
        ret_b.extend(self.header)
        ret_b.extend(self.l1_tiles)
        ret_b.extend(self.l2_tiles)
        ret_b.extend(self.l3_tiles)
        ret_b.extend(self._collect_tile_props())

        return ret_b

    def _validate_tile_input(
            self,
            top: int, left: int, bottom: int, right: int, layer: int | None,
    ) -> tuple[int, int, bytearray]:
        xmin, ymin = 0, 0
        if layer == 1:
            xmax, ymax = self.header.layer_1_width, self.header.layer_1_height
            tile_arr = self.l1_tiles
        elif layer == 2:
            xmax, ymax = self.header.layer_2_width, self.header.layer_2_height
            tile_arr = self.l2_tiles
        elif layer == 3:
            xmax, ymax = self.header.layer_3_width, self.header.layer_3_height
            tile_arr = self.l3_tiles
        else:
            raise ValueError

        if not all(xmin <= x <= xmax for x in (left, right)):
            raise ValueError("x value out of range")

        if not all(ymin <= y <= ymax for y in (top, bottom)):
            raise ValueError("y value out of range")

        return xmax, ymax, tile_arr

    def get_tile_properties(
            self, top: int, left: int, bottom: int, right: int
    ) -> list[LocationTileProperties]:
        xmin, ymin = 0, 0
        xmax, ymax, tile_arr = self._validate_tile_input(top, left, bottom, right, 1)

        ret_props: list[LocationTileProperties] = []

        for row in range(top, bottom):
            start = row * xmax + left
            end = start + (right - left)
            ret_props.extend(self.tile_props[start:end])

        return ret_props

    def get_tiles(self, top: int, left: int, bottom: int, right: int, layer: int) -> bytearray:
        xmin, ymin = 0, 0
        xmax, ymax, tile_arr = self._validate_tile_input(top, left, bottom, right, layer)

        ret_tiles: bytearray = bytearray()

        for row in range(top, bottom):
            start = row*xmax + left
            end = start + (right-left)
            ret_tiles.extend(tile_arr[start:end])

        return ret_tiles

    def set_tiles(self, top: int, left: int, bottom: int, right: int, layer: int,
                  tile_arr: bytearray | memoryview):
        xmin, ymin = 0, 0
        xmax, ymax, tile_arr = self._validate_tile_input(top, left, bottom, right, layer)
        data_width = right - left

        for row in range(top, bottom):
            in_st = row*data_width
            start = row*xmax + left
            end = start + data_width
            tile_arr[start:start+data_width] = tile_arr[in_st:in_st+data_width]

    def write_to_ctrom(self,
                       ct_rom: ctrom.CTRom, map_id: int,
                       free_existing: bool = True):
        """Write this map to a CTRom in the given slot."""
        rom = ct_rom
        space_man = rom.space_manager
        FSW = ctrom.freespace.FSWriteType

        cur_ptr_addr = get_map_ptr_address(rom.getbuffer(), map_id)
        cur_ptr = get_map_ptr(rom.getbuffer(), map_id)

        if free_existing:
            compr_len = ctcompression.get_compressed_length(
                rom.getbuffer(), cur_ptr)

            space_man.mark_block(
                (cur_ptr, cur_ptr + compr_len),
                FSW.MARK_FREE
            )

        map_b = self.get_as_bytearray()
        compr_map = ctcompression.compress(map_b)
        free_addr = space_man.get_free_addr(len(compr_map))
        rom.seek(free_addr)
        rom.write(compr_map, ctrom.freespace.FSWriteType.MARK_USED)

        free_addr_rom = byteops.to_rom_ptr(free_addr)
        rom.seek(cur_ptr_addr)
        rom.write(free_addr_rom.to_bytes(3, 'little'))


def main():
   ...


if __name__ == "__main__":
    main()
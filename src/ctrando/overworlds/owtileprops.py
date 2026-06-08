from enum import IntEnum, auto
from ctrando.common import cttypes as ctt


class TileProperty(IntEnum):
    ETHEREAL = 0
    SOLID_TO_PCS = 1
    SOLID_TO_HOVERCRAFT = 2
    SOLID_TO_DACTYLS = 3
    EXIT = 4


class OWTileProps(ctt.BinaryData):
    SIZE = 2

    nw_quad = ctt.byte_prop(0, 0xF0, ret_type=TileProperty)
    ne_quad = ctt.byte_prop(0, 0x0F, ret_type=TileProperty)
    sw_quad = ctt.byte_prop(1, 0xF0, ret_type=TileProperty)
    se_quad = ctt.byte_prop(1, 0x0F, ret_type=TileProperty)


class OWMapTileProperties(ctt.BinaryData):
    ROM_RW = ctt.CompressedAbsPtrTableRW(0x0229D4)  # C229D3  BF 80 FF C6    LDA $C6FF80,X

    def get_tile_props(self, tile_id: int):
        if not ( 0 <= tile_id < 512):
            raise IndexError

        start = tile_id*OWTileProps.SIZE
        return OWTileProps(self[start: start+OWTileProps.SIZE])

    def set_tile_props(self, props: OWTileProps, tile_id: int):
        if not ( 0 <= tile_id < 512):
            raise IndexError

        start = tile_id * OWTileProps.SIZE
        self[start: start+OWTileProps.SIZE] = props[:]


def main():
    from ctrando.common import ctrom
    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")

    props = OWMapTileProperties.read_from_ctrom(ct_rom, 1)
    x = props.get_tile_props(186)
    pass



if __name__ == "__main__":
    main()

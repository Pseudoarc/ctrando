from collections.abc import Iterable

from ctrando.common import cttypes as ctt
from typing import Self

class CTColor(ctt.SizedBinaryData):
    SIZE = 2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.unused = 0

    # 0x0bbb bbgg gggr rrrr
    red = ctt.bytes_prop(0, 2, 0x001F)
    green = ctt.bytes_prop(0, 2, 0x03E0)
    blue = ctt.bytes_prop(0, 2, 0x7C00)
    unused = ctt.bytes_prop(0, 2, 0x8000)

    def set_from_rgb255(self,
                        red: int | None = None,
                        green: int | None = None,
                        blue: int | None = None) -> Self:

        if red is not None:
            self.red = round(red*31/255)
        if green is not None:
            self.green = round(green*31/255)
        if blue is not None:
            self.blue = round(blue*31/255)

        return self

    def set_from_hex(self, hex_str: str)-> Self:
        val = int(hex_str, 16)
        if val >= 0xFFFFFF:
            raise ValueError

        red = (val & 0xFF0000) >> 16
        green = (val & 0x00FF00) >> 8
        blue = val & 0x0000FF
        return self.set_from_rgb255(red, green, blue)

    def get_hex(self) -> str:
        red = round(self.red*255/31)
        green = round(self.green*255/31)
        blue = round(self.blue*255/31)
        val = f"{red:02X}{green:02X}{blue:02X}"
        return val


class CTPalette(ctt.SizedBinaryData):
    SIZE = 2*12
    ROM_RW = ctt.AbsRomRW(0x240000)

    def get_color(self, item) -> CTColor:
        if not (0 <= item < 12):
            raise IndexError

        color_b = self[2*item: 2*(item+1)]
        return CTColor(color_b)

    def set_color(self, key: int, value: CTColor):
        if not (0 <= key < 12):
            raise IndexError

        self[2*key: 2*(key+1)] = value[:]


def main():
    from ctrando.common import ctrom
    rom = ctrom.CTRom.from_file("../ct.sfc")
    pal = CTPalette.read_from_ctrom(rom, 0)
    for i in range(12):
        color = pal.get_color(i)
        print(f"{i}: {color.red:02X}, {color.green:02X}, {color.blue:02X}")
    pass


if __name__ == "__main__":
    main()


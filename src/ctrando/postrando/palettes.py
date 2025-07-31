"""
Module for working with custom palettes.
"""
import enum
import typing
from collections.abc import Sequence

from ctrando.common import cttypes as cty, ctrom


class SNESColor(cty.SizedBinaryData):
    SIZE = 2

    red = cty.bytes_prop(0, 2, 0x001F)
    green = cty.bytes_prop(0, 2, 0x03E0)
    blue = cty.bytes_prop(0, 2, 0x7C00)

    @staticmethod
    def _scale_snes_to_255(snes_val: float) -> int:
        return round(snes_val * 255/31)

    @staticmethod
    def _scale_255_to_snes(val_255: float) -> int:
        return round(val_255 * 31/255)

    def to_rgb(self) -> tuple[int, int, int]:
        vals =  tuple(self._scale_snes_to_255(x)
                      for x in (self.red, self.green, self.blue))
        return vals[0], vals[1], vals[2]

    def to_rgb_hex(self) -> str:
        red, green, blue = self.to_rgb()
        return(f"#{red:02X}{green:02X}{blue:02X}")

    @classmethod
    def from_hex_str(cls, hex_str: str) -> typing.Self:
        if hex_str.startswith("#"):
            hex_str = hex_str[1:]

        hex_val = int(hex_str, 16)
        if not 0 <= hex_val < 0x1000000:
            raise ValueError

        red = (hex_val & 0xFF0000) >> 16
        green = (hex_val & 0x00FF00) >> 8
        blue = hex_val & 0x0000FF

        color = cls.from_rgb_255(red, green, blue)
        return color

    @classmethod
    def from_rgb_255(cls, red: int, green: int, blue: int) -> typing.Self:
        ret_color = cls()
        ret_color.red = cls._scale_255_to_snes(red)
        ret_color.green = cls._scale_255_to_snes(green)
        ret_color.blue = cls._scale_255_to_snes(blue)

        return ret_color


_loc_palette_rw = cty.AbsRomRW(0x240000)


class SNESPalette:
    NUM_COLORS = 12
    ROM_RW = _loc_palette_rw

    def __init__(self, colors: Sequence[SNESColor]):
        if len(colors) != self.NUM_COLORS:
            raise ValueError

        self.colors: list[SNESColor] = list(colors)

    def __eq__(self, other):
        if not isinstance(other, SNESPalette):
            return False

        return self.colors == other.colors


    def __getitem__(self, item) -> SNESColor:
        return self.colors[item]

    def __setitem__(self, key: int, value: SNESColor | str):
        if not 0 <= key < self.NUM_COLORS:
            raise IndexError

        if isinstance(value, str):
            value = SNESColor.from_hex_str(value)

        self.colors[key] = value

    def to_bytes(self):
        return b''.join(x for x in self.colors)

    def write_to_ctrom(self, ct_rom: ctrom.CTRom, index: int):
        """Write this palette to rom in given index."""

        payload = self.to_bytes()
        self.ROM_RW.write_data_to_ct_rom(ct_rom, payload, index)

    @classmethod
    def read_from_ct_rom(cls, ct_rom: ctrom.CTRom, index: int) -> typing.Self:
        """Return the palette in a given index"""

        palette_b = cls.ROM_RW.read_data_from_ctrom(ct_rom, cls.NUM_COLORS*2, index)
        return cls.from_bytes(palette_b)

    def to_hex_sequence(self) -> str:

        return "".join(color.to_rgb_hex() for color in self.colors)

    @classmethod
    def from_hex_sequence(cls, hex_sequence: str) -> typing.Self:
        """Sequence format: #ABCDEF#ABCDEF#ABCDEF.... 16 colors"""

        trimmed_sequence = "".join(hex_sequence.split())
        hex_strs = trimmed_sequence.split("#")[1:]

        colors = [
            SNESColor.from_hex_str(hex_str) for hex_str in hex_strs
        ]

        return SNESPalette(colors)

    @classmethod
    def from_bytes(cls, palette_b: typing.ByteString) -> typing.Self:
        colors = tuple(
            SNESColor(palette_b[2 * ind: 2 * ind + 2])
            for ind in range(cls.NUM_COLORS)
        )
        return cls(colors)


class CronoPaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_DARKER = 3
    HAIR_LIGHTER = 4
    HAIR_DARKER = 5
    PANTS = 6  # Will have white inside to accent
    GI_LIGHT = 7
    GI_MID = 8
    GI_DARK = 9
    HAIR_DARKEST = 10
    OUTLINE = 11


class MarlePaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_DARKER = 3
    HAIR_LIGHTER = 4
    HAIR_MID = 5
    HAIR_DARKER = 6
    HAIR_DARKEST = 7  # Also some facial outline
    TUNIC_SHADOW_LIGHT = 8
    TUNIC_SHADOW_MID = 9
    TUNIC_SHADOW_DARK = 10
    OUTLINE = 11


class LuccaPaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_DARKER = 3
    TUNIC_LIGHT = 4
    HAT_LIGHTER = 5
    HAT_DARKER = 6
    TUNIC_MID = 7
    TUNIC_DARKER = 8  # Also some shaodws around face
    HAIR_DARK = 9  # Also many shadows
    HAIR_LIGHT = 10  # Very infrequent
    OUTLINE = 11


class RoboPaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_MID = 3
    EYE_LIGHT = 4
    EYE_DARK = 5
    SKIN_DARK = 6
    JOINTS_LIGHT = 7
    SKIN_DARKEST = 8  # Barely used
    JOINTS_MID = 9
    INTERNAL_DARK = 10
    OUTLINE_DARK = 11


class FrogPaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_MID = 3
    ARMOR_LIGHT = 4
    GLOVE_BOOT = 5
    TONGUE = 6
    ARMOR_DARK = 7
    CAPE_LIGHT = 8
    CAPE_MID = 9
    CAPE_DARK = 10
    OUTLINE = 11


class AylaPaletteIndex(enum.IntEnum):
    DARK = 0
    WHITE = 1
    SKIN_LIGHTER = 2
    SKIN_DARKER = 3
    HAIR_LIGHT = 4
    HAIR_MID = 5
    HAIR_DARK = 6  # Also some skin shadows
    INTERNAL_DARK = 7  # Many dark shadows
    CLOTHES_LIGHT = 8
    CLOTHES_MID = 9
    CLOTHES_DARK = 10
    OUTLINE = 11

class MagusPaletteIndex(enum.IntEnum):
    SHADOW = 0
    VERY_LIGHT_GRAY = 1
    SKIN_LIGHTER = 2
    SKIN_DARKER = 3
    HAIR_LIGHT = 4
    HAIR_MID = 5  # Also is pants accent color
    ARMOR_GLOVE_LIGHT = 6
    CAPE_MAIN = 7
    ARMOR_GLOVE_DARK = 8
    PANTS_MAIN = 9
    INTERNAL_DARK = 10  # cape shadow, many dark shadows
    OUTLINE = 11


class SinglePCOWPalette(SNESPalette):
    NUM_COLORS = 8
    ROM_RW = None

def build_crono_ow_palette(
        crono_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors: list[SNESColor] = [
        SNESColor(b'\x12\x00'),  # Unsure, copy vanilla
        crono_loc_palette[CronoPaletteIndex.DARK],
        crono_loc_palette[CronoPaletteIndex.SKIN_LIGHTER],
        crono_loc_palette[CronoPaletteIndex.SKIN_DARKER],
        crono_loc_palette[CronoPaletteIndex.HAIR_DARKER],
        crono_loc_palette[CronoPaletteIndex.GI_MID],
        crono_loc_palette[CronoPaletteIndex.HAIR_DARKEST],
        crono_loc_palette[CronoPaletteIndex.GI_DARK]
    ]

    return SinglePCOWPalette(colors)


def build_marle_ow_palette(
        marle_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x52\x02'),  # Unsure, copy vanilla
        marle_loc_palette[MarlePaletteIndex.DARK],
        marle_loc_palette[MarlePaletteIndex.WHITE],
        marle_loc_palette[MarlePaletteIndex.SKIN_LIGHTER],
        marle_loc_palette[MarlePaletteIndex.HAIR_LIGHTER],
        marle_loc_palette[MarlePaletteIndex.SKIN_DARKER],
        marle_loc_palette[MarlePaletteIndex.TUNIC_SHADOW_MID],
        marle_loc_palette[MarlePaletteIndex.HAIR_DARKEST]
    ]

    return SinglePCOWPalette(colors)


def build_lucca_ow_palette(
        lucca_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x16\x00'),  # copy vanilla
        lucca_loc_palette[LuccaPaletteIndex.DARK],
        lucca_loc_palette[LuccaPaletteIndex.SKIN_LIGHTER],
        lucca_loc_palette[LuccaPaletteIndex.TUNIC_LIGHT],
        lucca_loc_palette[LuccaPaletteIndex.TUNIC_MID],
        lucca_loc_palette[LuccaPaletteIndex.HAT_LIGHTER],
        lucca_loc_palette[LuccaPaletteIndex.HAT_DARKER],
        lucca_loc_palette[LuccaPaletteIndex.TUNIC_DARKER],
    ]

    return SinglePCOWPalette(colors)


def build_robo_ow_palette(
        robo_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x56\x02'),
        robo_loc_palette[RoboPaletteIndex.DARK],
        robo_loc_palette[RoboPaletteIndex.EYE_LIGHT],
        robo_loc_palette[RoboPaletteIndex.SKIN_LIGHTER],
        robo_loc_palette[RoboPaletteIndex.SKIN_MID],
        robo_loc_palette[RoboPaletteIndex.SKIN_DARK],
        robo_loc_palette[RoboPaletteIndex.JOINTS_MID],
        robo_loc_palette[RoboPaletteIndex.SKIN_DARKEST]
    ]

    return SinglePCOWPalette(colors)


def build_frog_ow_palette(
        frog_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x1B\x00'),
        frog_loc_palette[FrogPaletteIndex.DARK],
        frog_loc_palette[FrogPaletteIndex.WHITE],
        frog_loc_palette[FrogPaletteIndex.ARMOR_LIGHT],
        frog_loc_palette[FrogPaletteIndex.SKIN_LIGHTER],
        frog_loc_palette[FrogPaletteIndex.ARMOR_DARK],
        frog_loc_palette[FrogPaletteIndex.CAPE_LIGHT],
        frog_loc_palette[FrogPaletteIndex.CAPE_DARK]
    ]

    return SinglePCOWPalette(colors)


def build_ayla_ow_palette(
        ayla_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x5B\x02'),
        ayla_loc_palette[AylaPaletteIndex.DARK],
        ayla_loc_palette[AylaPaletteIndex.WHITE],
        ayla_loc_palette[AylaPaletteIndex.SKIN_LIGHTER],
        ayla_loc_palette[AylaPaletteIndex.HAIR_DARK],
        ayla_loc_palette[AylaPaletteIndex.HAIR_MID],
        ayla_loc_palette[AylaPaletteIndex.CLOTHES_MID],
        ayla_loc_palette[AylaPaletteIndex.HAIR_DARK]
    ]

    return SinglePCOWPalette(colors)


def build_magus_ow_palette(
        magus_loc_palette: SNESPalette
) -> SinglePCOWPalette:
    colors = [
        SNESColor(b'\x1F\x00'),
        magus_loc_palette[MagusPaletteIndex.SHADOW],
        magus_loc_palette[MagusPaletteIndex.SKIN_LIGHTER],
        magus_loc_palette[MagusPaletteIndex.ARMOR_GLOVE_LIGHT],
        magus_loc_palette[MagusPaletteIndex.CAPE_MAIN],
        magus_loc_palette[MagusPaletteIndex.HAIR_MID],
        magus_loc_palette[MagusPaletteIndex.PANTS_MAIN],
        magus_loc_palette[MagusPaletteIndex.INTERNAL_DARK]
    ]

    return SinglePCOWPalette(colors)


class OWPallete(SNESPalette):
    NUM_COLORS = 0x80
    ROM_RW = cty.CompressedAbsPtrTableRW(0x0228B2)

    @classmethod
    def read_from_ct_rom(cls, ct_rom: ctrom.CTRom, index: int) -> typing.Self:
        data = cls.ROM_RW.read_data_from_ctrom(ct_rom, index)

        return OWPallete.from_bytes(data)

    def set_pc_palette(self, index: int, palette: SinglePCOWPalette):
        start = index*SinglePCOWPalette.NUM_COLORS*2
        end = start + SinglePCOWPalette.NUM_COLORS
        self.colors[start:end] = palette.colors














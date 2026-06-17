import copy
import dataclasses
import io
import typing

from PIL import Image

import numpy as np
import numpy.typing as npt

from ctrando.postrando import palettes


_default_colors: dict[int, palettes.SNESColor] = {
    0: palettes.SNESColor(b'\x00\x00'),
    1: palettes.SNESColor(b'\xA5\x14'),
    2: palettes.SNESColor(b'\x4A\x29'),
    3: palettes.SNESColor(b'\x5A\x6B'),
    4: palettes.SNESColor(b'\x32\x3E'),
    5: palettes.SNESColor(b'\x0F\x3A'),
    6: palettes.SNESColor(b'\xCC\x2D'),
    7: palettes.SNESColor(b'\x28\x19'),
    8: palettes.SNESColor(b'\xE7\x0C'),  # Shadow outline
    9: palettes.SNESColor(b'\xDF\x28'),
    10: palettes.SNESColor(b'\xBB\x12'),
    11: palettes.SNESColor(b'\x2D\x09'),  # Minor detail on ship and era marker
    12: palettes.SNESColor(b'\x63\x08'),  # Shadow main, some text on era marker
    13: palettes.SNESColor(b'\xBD\x73'),
    14: palettes.SNESColor(b'\xD6\x56'),
    15: palettes.SNESColor(b'\x72\x42'),
}

def snes_bytes_to_arr_4bpp(
        data: typing.ByteString,
) -> npt.NDArray:

    bits_per_pixel = 4
    num_tiles, rem = divmod(len(data), bits_per_pixel*8)
    if rem != 0:
        raise ValueError

    out_arr = np.zeros(len(data)*8//bits_per_pixel, dtype=np.uint8).reshape((8, -1))
    pos = 0
    for tile_index in range(num_tiles):
        for row in range(8):
            row_arr = extract_8_pixels_4bpp(data, pos)
            col = tile_index*8
            out_arr[row, col:col+8] = row_arr
            pos += 2
        pos += 0x10

    return out_arr


def extract_8_pixels_4bpp(
        data: typing.ByteString,
        pos: int = 0
) -> npt.NDArray:

    row_arr = np.array(
        [[data[pos], data[pos+1], data[pos+0x10], data[pos+0x11]]],
        dtype=np.uint8
    ).T

    bits = np.unpackbits(row_arr, axis=1)
    scalers = np.array([[2**n for n in range(4)]]).T

    out_arr = np.sum(bits*scalers, axis=0)
    return out_arr


def tile_to_ct_bytes(arr: npt.NDArray) -> typing.ByteString:
    if arr.shape != (8,8):
        print(arr.shape)
        raise ValueError

    out_data = bytearray(0x20)
    for row in range(8):
        for col in range(8):
            val = arr[row, col]
            bit = 0x80 >> col

            base_ind = row*2
            if val & 0x01:
                out_data[base_ind] |= bit
            if val & 0x02:
                out_data[base_ind+1] |= bit
            if val & 0x04:
                out_data[base_ind+0x10] |= bit
            if val & 0x08:
                out_data[base_ind+0x11] |= bit

    return out_data


def png_to_ct_bytes(image: Image.Image) -> tuple[typing.ByteString, list[palettes.SNESColor]]:

    image = image.convert("P", palette=Image.Palette.ADAPTIVE)
    arr = np.asarray(image, dtype=np.uint8)
    uniques = np.unique(arr).reshape(-1).tolist()

    palette = image.getpalette()
    if palette is None:
        raise TypeError

    ct_colors: list[palettes.SNESColor] = []

    for red, green, blue in zip(
        palette[::3], palette[1::3], palette[2::3]
    ):
        ct_colors.append(palettes.SNESColor.from_rgb_255(red, green, blue))

    translation = get_epoch_palette_translation(arr, ct_colors)

    translated_arr = np.vectorize(translation.get)(arr)
    translated_colors = [palettes.SNESColor(_default_colors[ind].copy()) for ind in range(16)]

    for ind, color in enumerate(ct_colors):
        if ind in translation:
            translated_colors[translation[ind]] = color

    translated_arr = np.array(translated_arr, dtype=np.uint8)
    new_im = Image.fromarray(translated_arr, "P")
    new_im.putpalette(
        [x for color in translated_colors for x in color.to_rgb()]
    )

    len_y, len_x = translated_arr.shape
    out_data = bytearray()
    for y in range(0, len_y, 8):
        for x in range(0, len_x, 8):
            out_data.extend(tile_to_ct_bytes(translated_arr[y:y+8, x:x+8]))

    return out_data, translated_colors


def get_closet_color_ind(
        base_color: palettes.SNESColor,
        colors: list[palettes.SNESColor],
        available_indices: list[int]
):
    return min(
        available_indices,
        key = lambda x: palettes.color_diff_rgb255(
            *base_color.to_rgb(),
            *colors[x].to_rgb(),
        )
    )


def get_epoch_palette_translation(
        img_arr: npt.NDArray,
        img_palette: list[palettes.SNESColor],
) -> dict[int, int]:

    avail_orig_indices: list[int] = list(range(4, 16))
    bg_index = img_arr[0,0]
    translation: dict[int, int] = {
        bg_index: 0
    }

    uniques, counts = np.unique(img_arr, return_counts=True)
    remaining_img_indices: list[int] = uniques.tolist()
    remaining_img_indices.remove(bg_index)

    # Palettes are allowed to use indices 1-3 but they must match the defaults
    for default_ind in range(1, 4):
        for ind, color in enumerate(img_palette):
            if color == _default_colors[default_ind]:
                translation[ind] = default_ind
                if ind in remaining_img_indices:
                    remaining_img_indices.remove(ind)

    # Indices 8 and 12 are for light/dark shadows
    if len(remaining_img_indices) > 10:
        default_shadow_color = _default_colors[12]
        shadow_ind = get_closet_color_ind(
            default_shadow_color, img_palette, remaining_img_indices
        )
        translation[shadow_ind] = 12
        remaining_img_indices.remove(shadow_ind)

        lighter_shadow_color = _default_colors[8]
        light_shadow_ind = get_closet_color_ind(
            lighter_shadow_color, img_palette, remaining_img_indices
        )
        translation[light_shadow_ind] = 8
        remaining_img_indices.remove(light_shadow_ind)

    avail_orig_indices.remove(12)
    avail_orig_indices.remove(8)

    for orig_ind in avail_orig_indices:
        if not remaining_img_indices:
            break

        closet_color = get_closet_color_ind(
            _default_colors[orig_ind],
            img_palette,
            remaining_img_indices
        )

        translation[closet_color] = orig_ind
        remaining_img_indices.remove(closet_color)

    return translation


def main():
    from ctrando.common import ctrom
    from ctrando.compression import ctcompression
    from ctrando.postrando import palettes

    image = Image.open("/home/ross/Downloads/bb.png")
    img2 = image.convert("P", palette=Image.Palette.ADAPTIVE)
    make_epoch_gif(img2)
    exit()

    png_to_ct_bytes(img2)

    ct_rom = ctrom.CTRom.from_file("/home/ross/Documents/ct.sfc")
    data = ctcompression.decompress(ct_rom.getbuffer(), 0x05B114)
    data_arr = snes_bytes_to_arr_4bpp(data)

    palette = palettes.OWPallete.read_from_ct_rom(ct_rom, 5)
    for color in palette.colors:
        print(color)

    # 0x040A20 epoch palette
    palette = palettes.OWPallete.read_from_ct_rom(ct_rom, 2)
    for color in palette.colors:
        print(color)

    pil_palette = [222,132,222, 41, 41, 41, 82, 82, 82, 214, 214, 214,] + [
        x for color in palette[4:] for x in color.to_rgb()
    ] + [
        24, 24, 16, 239, 239, 231, 181, 181, 173, 148, 156, 132,
    ]

    reformateed_array = np.zeros_like(data_arr).reshape((-1, 128))
    row = 0
    col = 0

    while col < data_arr.shape[1]:
        reformateed_array[row:row+8, :] = data_arr[:, col: col+128]
        row += 8
        col += 128

    vals = set()
    for x in reformateed_array.reshape(-1):
        vals.add(int(x))

    im = Image.fromarray(reformateed_array, "P")
    im.putpalette(pil_palette)
    im.save("/home/ross/Documents/epoch.png", "png", compress_level=0)
    im.show()


@dataclasses.dataclass()
class TileData:
    tile_id: tuple[int, int]
    flip_lr: bool
    flip_ud: bool


def get_tiles(
        tile_arr: npt.NDArray,
        top: int,
        left: int,
        x_len: int,
        y_len: int,
        flip_lr: bool = False,
        flip_ud: bool = False
) -> npt.NDArray:
    row_st = 8*top
    row_end = row_st + y_len*8

    col_st = 8*left
    col_end = col_st + x_len*8

    ret_arr = tile_arr[row_st: row_end, col_st: col_end]
    if flip_lr:
        ret_arr = np.fliplr(ret_arr)

    if flip_ud:
        ret_arr = np.flipud(ret_arr)

    return  ret_arr


def copy_tiles(
        dest_arr: npt.NDArray,
        tile_arr: npt.NDArray,
        dest_top: int,
        dest_left: int,
        src_top: int,
        src_left: int,
        x_len: int,
        y_len: int,
        flip_lr: bool = False,
        flip_ud: bool = False
):

    dest_arr[8*dest_top: 8*(dest_top+y_len), 8*dest_left: 8*(dest_left+x_len)] = get_tiles(
        tile_arr, src_top, src_left, x_len, y_len, flip_lr, flip_ud
    )


def make_epoch_gif(
        in_img: Image.Image,
) -> io.BytesIO:
    if in_img.size != (128, 64):
        raise ValueError

    ct_bytes, snes_colors = png_to_ct_bytes(in_img)
    data_arr = snes_bytes_to_arr_4bpp(ct_bytes)

    tile_arr = np.zeros_like(data_arr).reshape((-1, 128))
    row = 0
    col = 0

    while col < data_arr.shape[1]:
        tile_arr[row:row + 8, :] = data_arr[:, col: col + 128]
        row += 8
        col += 128

    landed = np.zeros((32, 32), np.uint8)
    landed[0:32, 0:16] = tile_arr[0:32, 0:16]
    landed[0:32, 16:] = np.fliplr(landed[0:32, 0:16])

    taking_off_1 = np.zeros_like(landed)
    copy_tiles(taking_off_1, tile_arr, 0, 0, 0, 6, 2, 4)
    copy_tiles(taking_off_1, tile_arr, 0, 2, 0, 6, 2, 4, flip_lr=True)

    taking_off_2 = np.zeros_like(landed)
    copy_tiles(taking_off_2, tile_arr, 0, 0, 0, 2, 2, 4 )
    copy_tiles(taking_off_2, tile_arr, 0, 2, 0, 2, 2, 4, flip_lr=True)

    flying_1_down = np.zeros_like(landed)
    copy_tiles(flying_1_down, tile_arr, 0, 0, 0, 4, 2, 4)
    copy_tiles(flying_1_down, tile_arr, 0, 2, 0, 4, 2, 4, flip_lr=True)

    flying_2_down = np.zeros_like(landed)
    copy_tiles(flying_2_down, flying_1_down, 2, 0, 2, 0, 4, 2)
    copy_tiles(flying_2_down, tile_arr, 0, 0, 0, 14, 2, 2)
    copy_tiles(flying_2_down, tile_arr, 0, 2, 0, 14, 2, 2, flip_lr=True)


    flying_left_1 = np.zeros_like(landed)
    copy_tiles(flying_left_1, tile_arr, 0, 0, 0, 10, 2, 4)
    copy_tiles(flying_left_1, tile_arr, 1, 2, 0, 12, 2, 2)

    flying_left_2 = np.zeros_like(landed)
    copy_tiles(flying_left_2, tile_arr, 0, 0, 0, 10, 2, 4)
    copy_tiles(flying_left_2, tile_arr, 1, 2, 2, 12, 2, 2)

    flying_up_1 = np.zeros_like(landed)
    copy_tiles(flying_up_1, tile_arr, 0, 0 , 0, 8, 2, 4)
    copy_tiles(flying_up_1, tile_arr, 0, 2, 0, 8, 2, 4, flip_lr=True)

    flying_up_2 = np.zeros_like(landed)
    copy_tiles(flying_up_2, flying_up_1, 0, 0, 0, 0, 4, 2)
    copy_tiles(flying_up_2, tile_arr, 2, 0, 2, 14, 2, 2)
    copy_tiles(flying_up_2, tile_arr, 2, 2, 2, 14, 2, 2, flip_lr=True)

    flying_right_1 = np.fliplr(flying_left_1)
    flying_right_2 = np.fliplr(flying_left_2)

    take_off_arrays = [landed, taking_off_1, taking_off_2, flying_1_down, flying_2_down]
    arrays = take_off_arrays[:]
    arrays += [flying_1_down, flying_2_down]*4
    arrays += [flying_left_1, flying_left_2]*4
    arrays += [flying_up_1, flying_up_2]*4
    arrays += [flying_right_1, flying_right_2]*4
    arrays += take_off_arrays[::-1]
    images = [Image.fromarray(arr, "P") for arr in arrays]
    for img in images:
        img.putpalette([x for color in snes_colors for x in color.to_rgb()])

    ret_obj = io.BytesIO()
    images[0].save(ret_obj, format="gif",
                   save_all=True,
                   append_images=images[1:],
                   duration = 100,
                   loop = 1
    )

    return ret_obj


if __name__ == "__main__":
    main()
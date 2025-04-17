'''Module providing classes for manipulating shops.'''

from __future__ import annotations
from io import BytesIO
from typing import Optional, ByteString

from ctrando.common import byteops, ctenums, ctrom
from ctrando.items import itemdata


class ShopManager:
    '''Class to handle reading/writing of shop data to rom.'''
    shop_ptr = 0x02DAFD
    shop_data_bank_ptr = 0x02DB09

    def __init__(
            self,
            shop_dict: Optional[dict[ctenums.ShopID, list[ctenums.ItemID]]] = None
    ):
        if shop_dict is None:
            shop_dict = dict()

        self.shop_dict = {
            shop_id: shop_dict.get(shop_id, list())
            for shop_id in ctenums.ShopID
        }
    @classmethod
    def read_from_ctrom(cls, ct_rom: ctrom.CTRom) -> ShopManager:
        """Read the shop data from a ct_rom"""

        ret_shopman = ShopManager()
        rom = ct_rom.getbuffer()
        shop_data_bank, shop_ptr_start = ShopManager.__get_shop_pointers(rom)

        # The sort shouldn't be necessary, but be explicit.
        for shop in sorted(list(ctenums.ShopID), key=lambda x: x.value):
            ptr_start = shop_ptr_start + 2 * shop.value
            shop_ptr_local = int.from_bytes(rom[ptr_start:ptr_start + 2], "little")
            shop_ptr = shop_ptr_local + shop_data_bank

            pos = shop_ptr

            # Items in the shop are a 0-terminated list
            null_pos = pos
            while rom[null_pos] != 0:
                # print(ctenums.ItemID(rom[pos]))
                ret_shopman.shop_dict[shop].append(ctenums.ItemID(rom[pos]))
                null_pos += 1

            ret_shopman.shop_dict[shop] = [
                ctenums.ItemID(x) for x in rom[pos: null_pos]
            ]
        return ret_shopman

    # Returns start of shop pointers, start of bank of shop data
    @classmethod
    def __get_shop_pointers(cls, rom: ByteString):
        shop_data_bank = byteops.to_file_ptr(rom[cls.shop_data_bank_ptr] << 16)
        shop_ptr_start = \
            byteops.to_file_ptr(
                int.from_bytes(rom[cls.shop_ptr:cls.shop_ptr+3], "little")
            )
        return shop_data_bank, shop_ptr_start

    @classmethod
    def __determine_shop_data_length(cls, ct_rom: ctrom.CTRom) -> int:
        """
        Determine how much space shops are using on the rom.
        Assumed that shop data follows shop pointers.
        """
        shop_data_bank, shop_ptr_start = \
            ShopManager.__get_shop_pointers(ct_rom.getbuffer())

        ct_rom.seek(shop_ptr_start)
        first_ptr = int.from_bytes(ct_rom.read(2), "little")
        first_shop_data_start = first_ptr + shop_data_bank

        ptr_block_len = first_shop_data_start - shop_ptr_start
        if ptr_block_len % 2 != 0:
            raise ValueError("Odd length pointer block")

        ct_rom.seek(shop_ptr_start + ptr_block_len - 2)
        last_ptr = int.from_bytes(ct_rom.read(2), "little") + shop_data_bank
        ct_rom.seek(last_ptr)
        last_shop_items = ct_rom.read(33)
        last_shop_data_len = last_shop_items.index(0) + 1

        shop_data_end = last_ptr + last_shop_data_len

        return shop_data_end - shop_ptr_start

    def write_to_ctrom(self, ct_rom: ctrom.CTRom, bank: Optional[int] = None):
        '''Write all shops out to the CTRom.'''

        # Always assume that shop data immediately follows pointer data.
        # Otherwise there's no way to figure out how many shops are in use.

        shop_ptr_len = 2*len(ctenums.ShopID)
        shop_data_len = sum(len(itemlist) + 1 for itemlist in self.shop_dict.values())
        out_data_len = shop_ptr_len + shop_data_len

        shop_data_bank, shop_ptr_start = \
            ShopManager.__get_shop_pointers(ct_rom.getbuffer())

        existing_data_len = self.__determine_shop_data_length(ct_rom)

        if True:
            hint = 0 if bank is None else bank << 16
            new_shop_addr = ct_rom.space_manager.get_free_addr(
                out_data_len, hint)
            if new_shop_addr >> 16 != bank and bank is not None:
                raise ctrom.freespace.FreeSpaceError("No space in bank")
        else:
            new_shop_addr = shop_ptr_start

        ct_rom.seek(shop_ptr_start)
        ct_rom.write(bytes.fromhex('FF' * existing_data_len),
                     ctrom.freespace.FSWriteType.MARK_FREE)

        new_shop_rom_addr = byteops.to_rom_ptr(new_shop_addr)
        ct_rom.seek(self.shop_ptr)
        ct_rom.write(int.to_bytes(new_shop_rom_addr, 3, "little"))

        ct_rom.seek(self.shop_data_bank_ptr)
        ct_rom.write(bytes([new_shop_rom_addr >> 16]))

        out_data = BytesIO(bytearray(out_data_len))
        ptr_loc = 0
        data_start_offset = new_shop_addr & 0xFFFF
        data_loc = shop_ptr_len

        for shop_id in sorted(ctenums.ShopID, key=lambda x: x.value):
            next_ptr = data_loc + data_start_offset
            out_data.seek(ptr_loc)
            out_data.write(next_ptr.to_bytes(2, "little"))
            ptr_loc += 2

            items = self.shop_dict[shop_id]
            items_b = bytes(items + [0])
            out_data.seek(data_loc)
            out_data.write(items_b)
            data_loc += len(items_b)

        ct_rom.seek(new_shop_addr)
        ct_rom.write(out_data.getbuffer(),
                     ctrom.freespace.FSWriteType.MARK_USED)


    def set_shop_items(self, shop: ctenums.ShopID,
                       items: list[ctenums.ItemID]):
        '''Sets the items of a shop.'''
        self.shop_dict[shop] = items[:]

    def get_spoiler_string(
            self,
            item_db: Optional[itemdata.ItemDB] = None) -> str:
        '''
        Return a string of all shops and items.  If an ItemDB is provided,
        include real names and prices.
        '''
        ret = ''
        for shop in sorted(x.value for x in self.shop_dict.keys()):
            if shop in [ctenums.ShopID.EMPTY_12, ctenums.ShopID.EMPTY_14,
                        ctenums.ShopID.LAST_VILLAGE_UPDATED]:
                continue

            ret += str(shop)
            ret += ':\n'
            for item in self.shop_dict[shop]:
                ret += ('    ' + str(item))

                if item_db is not None:
                    price = item_db.item_dict[item].secondary_stats.price
                    ret += f": {price}"

                ret += '\n'

        return ret

    def __str__(self):
        '''Returns a spoiler string without prices or names (just IDs).'''
        return self.get_spoiler_string(None)


def main():
    ct_rom = ctrom.CTRom.from_file('../ct.sfc')

    x = ShopManager()
    x.write_to_ctrom(ct_rom)


if __name__ == '__main__':
    main()
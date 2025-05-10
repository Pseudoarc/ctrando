"""Set options which can be found on the in-game options menu"""
from ctrando.arguments import postrandooptions
from ctrando.common import cttypes as ctty, ctrom


class Options(ctty.SizedBinaryData):
    SIZE = 3
    ROM_RW = ctty.AbsRomRW(0x02FCA6)

    battle_speed = ctty.byte_prop(0, 0x07)
    save_menu_cursor = ctty.byte_prop(0, 0x20, ret_type=bool)

    menu_style = ctty.byte_prop(1, 0x07)
    message_speed = ctty.byte_prop(1, 0x38)
    save_battle_cursor = ctty.byte_prop(1, 0x40, ret_type=bool)
    save_tech_cursor = ctty.byte_prop(1, 0x80, ret_type=bool)

    def __str__(self):
        ret_str = (
            f"{self.__class__.__name__}("
            f"battle_speed={self.battle_speed},"
            f"message_speed={self.message_speed},"
            f"save_battle_cursor={self.save_battle_cursor},"
            f"save_menu_cursor={self.save_menu_cursor},"
        )

        return ret_str
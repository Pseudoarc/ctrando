"""Openworld Northern Ruins Back Room"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    FuncSync as FS,
    Operation as OP,
    Facing,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Northern Ruins Back Room"""

    loc_id = ctenums.LocID.NORTHERN_RUINS_BACK_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Back Room for an Open World.
        - Reorder mem set and add item
        - Change charge text to normal item text.
        """

        sealed_str_id = script.add_py_string(
            "{line break}Sealed by a mysterious force...{null}"
        )
        normal_item_text = owu.add_default_treasure_string(script)
        for obj_id in (0x10, 0x11):
            pos = script.get_function_start(obj_id, FID.ACTIVATE)

            script.insert_commands(
                EF()
                .add_if_else(
                    EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE),
                    EF(),
                    EF().add(EC.auto_text_box(sealed_str_id)).add(EC.return_cmd()),
                )
                .get_bytearray(),
                pos,
            )

            for ind in range(2):
                pos, cmd = script.find_command([0xCA], pos)
                item_id = cmd.args[0]

                script.data[pos : pos + 2] = EC.add_item_memory(0x7F0200).to_bytearray()
                new_cmd = EC.assign_val_to_mem(item_id, 0x7F0200, 1)
                script.insert_commands(new_cmd.to_bytearray(), pos)
                pos += len(new_cmd)

                # Remove item memory setting command.
                pos = script.find_exact_command(
                    EC.assign_val_to_mem(item_id, 0x7F0200, 1), pos
                )
                script.delete_commands(pos, 1)

                pos, _ = script.find_command([0xC1], pos)
                script.data[pos + 1] = normal_item_text

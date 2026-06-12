"""Openworld Northern Ruins Antechamber"""

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
    """EventMod for Northern Ruins Antechamber"""

    loc_id = ctenums.LocID.NORTHERN_RUINS_ANTECHAMBER

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Northern Ruins Antechamber for an Open World.
        - Reorder mem set and add item
        - Change charge text to normal item text.
        """
        normal_item_text = owu.add_default_treasure_string(script)
        pos = script.get_function_start(8, FID.ACTIVATE)

        for _ in range(2):
            pos, cmd = script.find_command([0xCA], pos)
            item_id = cmd.args[0]

            script.data[pos : pos + 2] = EC.add_item_memory(0x7F0200).to_bytearray()
            new_cmd = EC.assign_val_to_mem(item_id, 0x7F0200, 1)
            script.insert_commands(new_cmd.to_bytearray(), pos)
            pos += len(new_cmd)

            pos, _ = script.find_command([0x4F], pos)
            script.delete_commands(pos)

            pos, _ = script.find_command([0xC1], pos)
            script.data[pos + 1] = normal_item_text

        pos = script.get_function_start(0x10, FID.ACTIVATE)

        script.insert_commands(
            EF()
            .add_if_else(
                EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE),
                EF(),
                EF()
                .add(
                    EC.auto_text_box(
                        script.add_py_string(
                            "{line break}Sealed by a mysterious force...{null}"
                        )
                    )
                )
                .add(EC.return_cmd()),
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

            pos = script.find_exact_command(
                EC.assign_val_to_mem(item_id, 0x7F0200, 1),
                pos
            )
            script.delete_commands(pos)

            pos, _ = script.find_command([0xC1], pos)
            script.data[pos + 1] = normal_item_text

        # The vanilla script doesn't hide defunct object 0xF when beginning the
        # rightmost battle.  It will glitch out depending on what gets loaded
        # for the Macabres.
        pos = script.find_exact_command(
            EC.set_object_drawing_status(0xD, False),
            script.get_object_start(0)
        )
        script.insert_commands(
            EC.set_object_drawing_status(0xF, False).to_bytearray(),
            pos
        )

        # Add departed objects with coordinates to match the defuncts and
        # slots which are compatible so that other transforming enemies will
        # work in the spot.
        cls.add_departed_obj(script, 0x23, 0x19, 6)
        cls.add_departed_obj(script, 0x2F, 0x16, 5)
        cls.add_departed_obj(script, 0x3A, 0x1A, 6)
        cls.add_departed_obj(script, 0x32, 0x14, 9)

    @staticmethod
    def change_slot(
            script: locationevent.LocationEvent,
            obj_id: int,
            new_slot: int
    ):
        pos = script.get_object_start(obj_id)
        pos, _ = script.find_command([0x83], pos)
        val = script.data[pos+2]
        val &= 0x80
        val |= new_slot
        script.data[pos+2] = val

    @staticmethod
    def add_departed_obj(
            script: locationevent.LocationEvent,
            x_tile: int, y_tile: int, slot: int
    ):
        startup = (
            EF()
            .add(EC.load_enemy(ctenums.EnemyID.DEPARTED, slot))
            .add(EC.set_object_coordinates_tile(x_tile, y_tile))
            .add(EC.set_own_drawing_status(False, is_battle_active=True))
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )
        obj_id = script.append_empty_object()
        script.set_function(obj_id, FID.STARTUP, startup)
        script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))

"""Openworld Sun Keep (Prehistory)"""

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
    """EventMod for Sun Keep (Prehistory)"""
    loc_id = ctenums.LocID.SUN_KEEP_65MBC

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Keep (Prehistory) for an Open World.
        - Change draw conditions for Moon Stone to use rando flags.
        - Change turn-in condition to check for the Moon Stone.
        """

        # The star_obj exists for a trigger to place the stone.
        moonstone_obj, star_obj = 9, 8

        # Modify the star_obj

        # New show conditions
        new_star_startup = (
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.MOON_STONE),
                EF().add_if(
                    EC.if_not_flag(memory.Flags.MOONSTONE_PLACED_PREHISTORY),
                    EF().add(EC.set_object_coordinates_pixels(0x88, 0xB8))
                    .add(EC.load_npc(0x70))
                    .jump_to_label(EC.jump_forward(), 'return')
                )
            ).add(EC.remove_object(star_obj))
            .set_label('return')
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )
        script.set_function(star_obj, FID.STARTUP, new_star_startup)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.SUN_PALACE_ITEM_OBTAINED),
            script.get_function_start(star_obj, FID.ACTIVATE)
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.MOON_STONE))

        # New show conditions for moonstone
        new_stone_startup = (
            EF().add(EC.load_npc(0x6E))
            .add(EC.set_object_coordinates_pixels(0x88, 0xB8))
            .add_if(
                EC.if_not_flag(memory.Flags.MOONSTONE_PLACED_PREHISTORY),
                EF().add(EC.set_own_drawing_status(False))
            ).add(EC.return_cmd())
            .add(EC.end_cmd())
        )
        script.set_function(moonstone_obj, FID.STARTUP, new_stone_startup)



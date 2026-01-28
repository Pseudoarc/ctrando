"""Openworld Guardia Court Tower"""
from dataclasses import dataclass

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Court Tower"""
    loc_id = ctenums.LocID.GUARDIA_LAWGIVERS_TOWER

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Court Tower Event.
        - Add item to Yakra box
        """
        pos = script.find_exact_command(
            EC.play_song(0x0C),
            script.get_function_start(8, FID.ACTIVATE)
        )

        item_str_id = owu.add_default_treasure_string(script)
        script.insert_commands(
            EF()
            .add(EC.assign_val_to_mem(ctenums.ItemID.TONIC, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(item_str_id))
            .get_bytearray(), pos
        )
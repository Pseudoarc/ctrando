"""Openworld Porre Mayor 1F"""

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
from ctrando.strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Porre Mayor 1F"""
    loc_id = ctenums.LocID.PORRE_MAYOR_1F

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Mayor 1F for an Open World.
        - Replace the sunstone-related flags with jerky-specific ones.
        - Allow the Jerky item to be scouted.  This ends up losing the chicken dance.
          We need a separate flag for activating the Jerky quest if we want it back.
        """
        interested_str_id = 0xB
        never_heard_str_id = 0xC

        script.strings[interested_str_id] = ctstrings.CTString.from_str(
            "You're interested in the {item}?{linebreak+0}"
            "Well, someone simply left it here.{full break}"
            "Seems important to you folks.{linebreak+0}"
            "Why don't you take it!{null}"
        )

        script.strings[never_heard_str_id] = ctstrings.CTString.from_str(
            "{item}?{linebreak+0}"
            "Never heard of it!{null}"
        )

        mayor_obj_id = 8
        pos = script.get_function_start(mayor_obj_id, FID.ACTIVATE)
        script.insert_commands(
            EC.assign_val_to_mem(ctenums.ItemID.MOP, 0x7F0200, 1)
            .to_bytearray(), pos
        )

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.MOON_STONE), pos)
        script.replace_command_at_pos(pos, EC.add_item_memory(0x7F0200))
        script.insert_commands(EC.set_explore_mode(False).to_bytearray(), pos)

        pos = script.find_exact_command(EC.jump_forward(0), pos)
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.DISCOVERED_MOONSTONE_MISSING_OLD),
            script.get_function_start(mayor_obj_id, FID.ACTIVATE)
        )

        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.PORRE_JERKY_ITEM_OBTAINED)
        )
        pos = script.find_exact_command(
            EC.reset_flag(memory.Flags.OW_PORRE_SUNSTONE), pos
        )
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.PORRE_JERKY_ITEM_OBTAINED)
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.DISCOVERED_MOONSTONE_MISSING_OLD),
            pos
        )
        script.delete_commands(pos, 1)
"""Openworld Choras Cafe"""

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
    """EventMod for Choras Cafe"""
    loc_id = ctenums.LocID.CHORAS_CAFE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Cafe for an Open World.
        - Change the carpenter to check for tools rather than a flag.
        """
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.RECOVERED_RAINBOW_SHELL),
            script.get_function_start(0xD, FID.ACTIVATE)
        )
        script.wrap_jump_cmd(
            pos,
            EC.if_flag(memory.Flags.OBTAINED_TOMA_ITEM)
        )

        pos = script.find_exact_command(EC.add_item(ctenums.ItemID.TOMAS_POP),
                                        script.get_function_start(0xD, FID.ACTIVATE))

        owu.update_add_item(script, pos)
        cls.modify_tools_turnin(script)

    @classmethod
    def modify_tools_turnin(cls, script: Event):
        """
        Change the carpenter to look for Tools instead of a flag.
        """

        pos = script.get_function_start(0xF, FID.ACTIVATE)
        # Remove setting 0x7F019E & 10 which would allow getting present tools.
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CHORAS_1000_RECEIVED_TOOLS), pos
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.TOOLS))


        # Note: Tracker needs to check CHORAS_600_GAVE_CARPENTER_TOOLS and also
        #       having tools in inventory.
        # This would prevent tools from being removed if so desired:
        pos = script.find_exact_command(
            EC.remove_item(ctenums.ItemID.TOOLS), pos
        )
        script.delete_commands(pos, 1)

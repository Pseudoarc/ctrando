"""Openworld Sun Keep (600AD)"""

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
    """EventMod for Sun Keep (600AD)"""

    loc_id = ctenums.LocID.SUN_KEEP_600

    @classmethod
    def modify_moonstone_draw_conditions(cls, script: Event):
        """Change MoonStone to use rando flags"""
        moonstone_obj = 8
        new_hide_condition = EF().add_if(
            EC.if_not_flag(memory.Flags.MOONSTONE_PLACED_PREHISTORY),
            EF().add(EC.remove_object(moonstone_obj)),
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.WONDERSHOT_SUNSHADES_RECEIVED),
            script.get_function_start(moonstone_obj, FID.STARTUP),
        )

        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)

        script.insert_commands(new_hide_condition.get_bytearray(), pos)

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Sun Keep (600AD) for an Open World.
        - Change draw conditions for Moon Stone to use rando flags.
        - Normalize power tab pickup
        """

        cls.modify_moonstone_draw_conditions(script)
        owu.update_add_item(script, script.get_function_start(0xA, FID.ACTIVATE))

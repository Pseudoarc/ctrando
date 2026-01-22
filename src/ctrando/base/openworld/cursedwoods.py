"""Openworld Cursed Woods"""

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
    """EventMod for Cursed Woods"""

    loc_id = ctenums.LocID.CURSED_WOODS
    nu_obj = 0x14

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Cursed Woods for an Open World.
        - Add a flag for the Nu encounter.
        """

        pos = script.find_exact_command(
            EC.set_explore_mode(True),
            script.get_function_start(cls.nu_obj, FID.TOUCH)
        )
        script.insert_commands(
            EC.set_flag(memory.Flags.ENCOUNTERED_CURSED_WOODS_NU).to_bytearray(),
            pos
        )

        for func_id in (FID.ARBITRARY_1, FID.ARBITRARY_2):
            pos = script.get_function_start(cls.nu_obj, func_id)
            script.insert_commands(
                EC.set_flag(memory.Flags.ENCOUNTERED_CURSED_WOODS_NU).to_bytearray(),
                pos
            )



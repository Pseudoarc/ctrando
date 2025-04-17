"""Openworld Porre Elder"""

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
    """EventMod for Porre Elder"""

    loc_id = ctenums.LocID.PORRE_ELDER
    check_pendant_charge_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Porre Elder for an Open World.
        - Remove the option to sell the Jerky because it may not be replaceable.
        - Update Sealed Chests
        """

        owu.update_charge_chest_base_loc(script, 0xD, cls.check_pendant_charge_addr)
        owu.update_charge_chest_base_loc(script, 0xE, cls.check_pendant_charge_addr)

        cook_obj = 0xB
        pos = script.get_function_start(cook_obj, FID.ACTIVATE)

        give_jerky_str_id = 0xC
        script.strings[give_jerky_str_id] = ctstrings.CTString.from_str(
            "Will you sell it for 10,000 G?{line break}"
            "   I'll give it to you.{line break}"
            "   Not interested.{null}"
        )

        script.replace_jump_cmd(pos, EC.if_flag(memory.Flags.GAVE_AWAY_JERKY_PORRE))

        pos, cmd = script.find_command([0xC0], pos)  # decbox
        repl_cmd = EC.decision_box(give_jerky_str_id, 1, 2)
        script.data[pos : pos + len(cmd)] = repl_cmd.to_bytearray()

        # Delete the first option of the checkresult (old selling it)
        pos, _ = script.find_command([0x1A], pos)
        script.delete_jump_block(pos)

        # Bump each other option down by one (give == 1, not interested == 2)
        for _ in range(2):
            pos, cmd = script.find_command([0x1A], pos)
            script.data[pos + 1] -= 1
            pos += len(cmd)

"""Openworld Truce Mayor 2F"""

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
    """EventMod for Truce Mayor 2F"""

    loc_id = ctenums.LocID.TRUCE_MAYOR_2F
    pendant_charge_check_addr = 0x7F0230

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Truce Mayor 2F for an Open World.
        - Update Old man's gold adding function to be ready for random rewards
        """

        pos, _ = script.find_command([0xBB], script.get_function_start(8, FID.ACTIVATE))
        new_cmds = (
            EF()
            .add(EC.assign_val_to_mem(0, 0x7F0200, 1))
            .add(EC.add_gold(300))
        )
        script.insert_commands(new_cmds.get_bytearray(), pos)

        pos += len(new_cmds)
        pos = script.find_exact_command(
            EC.add_gold(300), pos
        )
        script.delete_commands(pos, 1)

        # for ind, ct_str in enumerate(script.strings):
        #     print(f"{ind:02X}: {ctstrings.CTString.ct_bytes_to_ascii(ct_str)}")
        # input()

        new_str = (
            'Hold {"1}Start{"2} and press {"1}Select{"2} on the{linebreak+0}'
            'overworld to warp home.{null}'
        )
        script.strings[3] = ctstrings.CTString.from_str(new_str)

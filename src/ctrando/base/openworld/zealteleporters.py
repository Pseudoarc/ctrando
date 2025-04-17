"""Openworld Zeal Teleporters"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Zeal Teleporters"""
    loc_id = ctenums.LocID.ZEAL_TELEPORTERS

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Zeal Teleporters Event.
        - Immediately jump between bottom and top.
        """

        bot_loc_cmd = EC.change_location(ctenums.LocID.ZEAL_TELEPORTERS,
                                         0x1F, 0x0E, 1, 3, False)
        new_bot_loc_cmd = EC.change_location(ctenums.LocID.ZEAL_TELEPORTERS,
                                             0x35, 0x0E, 1, 3, False)

        pos = script.find_exact_command(bot_loc_cmd)
        script.data[pos:pos + len(bot_loc_cmd)] = new_bot_loc_cmd.to_bytearray()

        top_loc_cmd = EC.change_location(ctenums.LocID.ZEAL_TELEPORTERS,
                                         0x0A, 0x26, 1, 3, False)
        new_top_loc_cmd = EC.change_location(ctenums.LocID.ZEAL_TELEPORTERS,
                                             0x0A, 0xE, 1, 3, False)

        pos = script.find_exact_command(top_loc_cmd)
        script.data[pos:pos + len(bot_loc_cmd)] = new_top_loc_cmd.to_bytearray()
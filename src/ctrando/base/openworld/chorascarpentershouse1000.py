"""Openworld Choras Carpenter's Residence (1000)"""
from ctrando.base import openworldutils as owu
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID
from strings import ctstrings


class EventMod(locationevent.LocEventMod):
    """EventMod for Choras Carpenter's Residence (1000)"""
    loc_id = ctenums.LocID.CHORAS_CARPENTER_1000

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Carpenter's Residence (1000) for an Open World.
        - Add a missing exploremode on command.
        - Normalize reward text
        """

        owu.add_exploremode_to_partyfollows(script)

        pos = script.find_exact_command(
            EC.add_item(ctenums.ItemID.TOOLS),
            script.get_function_start(8, FID.ACTIVATE)
        )
        pos, cmd = script.find_command([0xBB], pos)
        script.strings[cmd.args[0]] = (
            ctstrings.CTString.from_str(owu.get_default_treasure_string())
        )
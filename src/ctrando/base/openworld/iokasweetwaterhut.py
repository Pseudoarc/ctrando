"""Openworld Ioka Sweet Water Hut"""
import dataclasses

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
    """EventMod for Ioka Sweet Water Hut"""

    loc_id = ctenums.LocID.IOKA_SWEETWATER_HUT

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Ioka Sweet Water Hut for an Open World.
        - Make the item given after recruiting Ayla obtainable
        """

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x78),
            script.get_function_start(0x8, FID.ACTIVATE)
        )
        script.delete_jump_block(pos)
        script.replace_jump_cmd(
            pos, EC.if_pc_recruited(ctenums.CharID.AYLA)
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F020E, OP.LESS_THAN, 4),
            pos
        )
        end = script.find_exact_command(EC.set_explore_mode(True))
        script.delete_commands_range(pos, end)
        got_item_str_id = owu.add_default_treasure_string(script)
        script.insert_commands(
            EF()
            .add(EC.play_sound(0xB0))
            .append(owu.get_add_item_block_function(ctenums.ItemID.TONIC, None, got_item_str_id))
            .get_bytearray(), pos
        )







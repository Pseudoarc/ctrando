"""Openworld Bekkler's Lab"""
from typing import Optional

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
    """EventMod for Bekkler's Lab"""
    loc_id = ctenums.LocID.BEKKLERS_LAB
    special_game_addr = 0x7F0238
    silver_pts_addr = 0x7F021A

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Bekkler's Lab for an Open World.
        - Modify triggers for the special clone game.
        - Make the clone game cost no points if part of the quest.
        - Add hooks for a randomized item and update Bekkler's text accordingly.
        """

        # Detecting the special clone game is in the clone object's (09) startup.
        # This also loads the right npc for the clone.
        # Note: We may choose to use a different npc depending on Death Peak recruit.

        # The relevant part:
        # If has gaspar item (trigger):
        #   If has clone:
        #     Goto 'End'
        #   If has Crono's clone
        #     Goto 'End'
        #   Load Crono's Clone
        #   Set special game flag (0x7F0238 = 1)

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_GASPAR_ITEM),
            script.get_object_start(9)
        )
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.C_TRIGGER))

        pos = script.find_exact_command(EC.if_has_item(ctenums.ItemID.CLONE), pos)
        script.replace_jump_cmd(pos, EC.if_flag(memory.Flags.HAS_BEKKLER_ITEM))

        # Make the special game not cost silver points
        pos = script.get_function_start(0, FID.ARBITRARY_0)
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.special_game_addr, OP.EQUALS, 0),
                EF().add_if(
                    EC.if_mem_op_value(cls.silver_pts_addr, OP.LESS_THAN, 40),
                    EF().add(EC.auto_text_box(0xA))
                    .add(EC.return_cmd())
                ).add(EC.sub(cls.silver_pts_addr, 40, 1))
            ).get_bytearray(), pos
        )
        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.silver_pts_addr, OP.GREATER_OR_EQUAL, 40),
            pos
        )

        # Removing the original silver pt check and the original silver pt sub
        script.delete_commands(pos, 2)

        pos, cmd = script.find_command([0xC0], script.get_function_start(0xB, FID.ACTIVATE))
        script.insert_commands(
            EC.assign_val_to_mem(ctenums.ItemID.CLONE, 0x7F0200, 1)
            .to_bytearray(), pos
        )

        str_id: int = cmd.args[0]
        script.strings[str_id] = ctstrings.CTString.from_str(
            "So! You want a {item}?{line break}"
            "Normally I'd never do this, but today{line break}"
            "I'll make an exception.{full break}"
            "Challenge me, and I'll give you one.{line break}"
            "The longer you stay in the game, the{line break}"
            "lower my price will be.{page break}"
            "   Take the challenge!{line break}"
            "   It's not my lucky day.{null}"
        )

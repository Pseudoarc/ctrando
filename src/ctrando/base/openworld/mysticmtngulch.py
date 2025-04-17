"""Openworld Mystic Mountain Gulch"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Mystic Mountain Gulch"""
    loc_id = ctenums.LocID.MYSTIC_MTN_GULCH
    temp_addr = 0x7F0240
    battle_scene_compare_addr = 0x7F0242

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Mystic Mountain Gulch Event.
        - Fix a pre-battle scene that waits for 3 PCs to do an animation.  Instead,
          compute the number of PCs and wait for that many.
        - Add an exploremode on command after the Kilwala battle
        - Remove the forced kilwala fight (as it would be late-game anyway)
        """

        # We have to compare num_pcs + 4 for the scene
        count_pcs_func = owu.get_count_pcs_func(cls.temp_addr,
                                                cls.battle_scene_compare_addr)
        count_pcs_func.add(EC.add(cls.battle_scene_compare_addr, 4))

        pos = script.get_function_start(0, FID.ACTIVATE)
        script.insert_commands(count_pcs_func.get_bytearray(), pos)

        pos = script.get_function_start(8, FID.ARBITRARY_0)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0224, OP.LESS_THAN, 7)
        )
        script.replace_jump_cmd(
            pos, EC.if_mem_op_mem(0x7F0224, OP.LESS_THAN, cls.battle_scene_compare_addr)
        )

        # exploremode after Kilwala
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(0xD, FID.STARTUP)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        # Put the scene in late-game mode
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xA8))
        script.delete_jump_block(pos)
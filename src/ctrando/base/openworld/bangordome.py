"""Openworld Bangor Dome"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Bangor Dome"""
    loc_id = ctenums.LocID.BANGOR_DOME
    temp_addr = 0x7F0220
    can_eot_addr = 0x7F0222

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Bangor Dome Event.
        - Remove cutscene on first entry
        - Change EoT access condition
        - Change charged pendant condition
        """

        # Easiest to just set the flag for having viewed the cutscene
        pos = script.find_exact_command(EC.return_cmd())
        script.insert_commands(
            EC.set_flag(memory.Flags.SEEN_BANGOR_SCENE).to_bytearray(),
            pos
        )

        # Change the door to check the charged pendant
        pos = script.get_function_start(8, FID.ACTIVATE)
        owu.modify_if_not_charge(script, pos, cls.temp_addr)

        # Change the EoT condition to having gate key + 4
        pos = script.get_object_start(0)
        script.insert_commands(
            owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr).get_bytearray(),
            pos
        )

        pos = script.get_function_start(0xB, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x48))
        # The conditional block has the normal mode, so check can_eot == 0
        script.replace_jump_cmd(pos, EC.if_mem_op_value(cls.can_eot_addr, OP.EQUALS, 0))


        # Fix exploremode after portal
        pos = script.find_exact_command(EC.party_follow(),
                                        script.get_object_start(0xC))
        script.insert_commands(
            EC.set_explore_mode(True).to_bytearray(),
            pos
        )
"""Openworld Factory Ruins Entrance"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Factory Ruins Entrance"""
    loc_id = ctenums.LocID.FACTORY_RUINS_ENTRANCE
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Factory Ruins Entrance Event.  There is not much to do.
        - Add an error message to the computer when Robo is not present
        - Fix a small bug if the computer is activated with Robo after being
          activated without Robo (no partyfollow)
        """

        pos = script.get_function_start(8, FID.ACTIVATE)
        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.ROBO), pos)

        # It's annoying to add an "else" after the existing check.  So we add a
        # slightly redundant if-else prior to the existing if.
        script.insert_commands(
            EF().add_if_else(
                EC.if_pc_active(ctenums.CharID.ROBO),
                EF(),
                EF().add(EC.auto_text_box(
                    script.add_py_string("ERROR: Only R-Series can access.{null}")
                ))
            ).get_bytearray(), pos
        )

        # Slightly change the party positioning for the computer activation.
        # It just looks weird for Robo to run up to the computer, run away, and then
        # run back.
        pos, _ = script.find_command([0xD9], pos)
        script.data[pos+1: pos+7] = [9, 0x15, 7, 0x15, 0xB, 0x15]

        move_pos = script.find_exact_command(
            EC.pause(3), script.get_function_start(4, FID.ARBITRARY_2)
        )
        script.data[move_pos+1] = 0x18
        script.insert_commands(
            EC.set_own_facing('up').to_bytearray(), move_pos
        )

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0214, OP.EQUALS, 0), pos
        )
        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(0x7F0214, OP.NOT_EQUALS, 0),
                EF().add(EC.party_follow())
            ).get_bytearray(), pos
        )
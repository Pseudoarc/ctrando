"""Openworld Reptite Lair Weevil Burrows B1"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Reptite Lair Weevil Burrows B1"""
    loc_id = ctenums.LocID.REPTITE_LAIR_WEEVIL_BURROWS_B1

    @classmethod
    def modify(cls, script: Event):
        """
         Update the Reptite Lair Weevil Burrows B1 Event.
         - Add exploremode on after partyfollows.
         - TODO: Fix (vanilla) bad goto jump in weevil function
        """

        cls.fix_tunnel_entry(script)

        pos = script.find_exact_command(EC.end_cmd())
        script.insert_commands(
            EF().add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )

    @classmethod
    def fix_tunnel_entry(cls, script: Event, fall_fid: FID = FID.ARBITRARY_0):
        """
        Fix an animation glitch when entering the tunnel with only two members.
        """

        new_block = (
            EF().add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, 0x7F0240, 1))
            .add_if_else(
                EC.if_mem_op_value(0x7F0240, OP.LESS_THAN, 8),
                EF().add(EC.call_pc_function(1, fall_fid, 1, FS.CONT)),
                EF().add(EC.call_pc_function(1, fall_fid, 1, FS.HALT))
            )

        )
        pos = script.find_exact_command(
            EC.call_pc_function(1, fall_fid, 1, FS.CONT)
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 1)

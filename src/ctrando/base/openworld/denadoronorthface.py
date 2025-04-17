"""Openworld Denadoro Mts North Face"""

from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Denadoro Mts North Face"""
    loc_id = ctenums.LocID.DENADORO_NORTH_FACE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Denadoro Mts North Face event.
        - Make the waterfall jumps a little less janky.  There are little
          glitches that occur when the party is out of CharID order.
        """

        # Jump objects are in 0x10, 0x11, and 0x13

        def fix_jump(obj_id: int, repl_fid: FID):
            new_fall_block = (
                EF().add(EC.call_pc_function(0, repl_fid, 3, FS.HALT))
                .add(EC.call_pc_function(1, repl_fid, 3, FS.HALT))
                .add(EC.call_pc_function(2, repl_fid, 3, FS.HALT))
            )

            new_recover_block = (
                EF().add(EC.call_pc_function(0, FID.ARBITRARY_0, 4, FS.HALT))
                .add(EC.call_pc_function(1, FID.ARBITRARY_0, 4, FS.HALT))
                .add(EC.call_pc_function(2, FID.ARBITRARY_0, 4, FS.HALT))
            )

            pos = script.find_exact_command(
                EC.call_obj_function(1, repl_fid, 3, FS.HALT),
                script.get_function_start(obj_id, FID.TOUCH)
            )

            script.insert_commands(new_fall_block.get_bytearray(), pos)
            pos += len(new_fall_block)
            cmd = locationevent.get_command(script.data, pos)
            script.delete_commands(pos, 7)

            cmd = locationevent.get_command(script.data, pos)
            pos += 1  # Skip partyfollow
            script.insert_commands(new_recover_block.get_bytearray(), pos)
            pos += len(new_recover_block)
            script.delete_commands(pos, 7)

        fix_jump(0x10, FID.ARBITRARY_1)
        fix_jump(0x11, FID.ARBITRARY_2)
        fix_jump(0x13, FID.ARBITRARY_3)

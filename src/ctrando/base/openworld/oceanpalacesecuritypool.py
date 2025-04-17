"""Openworld Ocean Palace Security Pool"""

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


class EventMod(locationevent.LocEventMod):
    """EventMod for Ocean Palace Security Pool"""

    loc_id = ctenums.LocID.OCEAN_PALACE_SECURITY_POOL

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Ocean Palace Security Pool Event.
        - Modify PCs to have the same arbitrary functions and modify calls.
        - Add Magus to the location
        """

        cls.modify_pc_arbs(script)

        # Copying Crono because the rest have linked functions which will break.
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 7)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give everyone the Crono-specific arbs so that switches work properly.
        Modify the calls to pc aribtrary functions.
        """

        # Current scheme:
        # Arb0: Waiting function copied by everyone
        # Arb1: For Crono this is walking onto the switch.  For everyone else it's
        #       the going down function
        # Arb2: For Crono it's going up.  For everyone else, going down.
        # Arb3: For Crono it goes down.  Nobody else has it.

        # Just give everyone Crono's arbs and update the calls!
        for obj_id in range(2, 7):
            for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2,
                        FID.ARBITRARY_3):
                script.link_function(obj_id, fid,1, fid)

        # Explicit call to Obj01.  Replace with first pc
        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_1, 1, FS.HALT),
            script.get_function_start(9, FID.ARBITRARY_0)
        )
        repl_cmd = EC.call_pc_function(0, FID.ARBITRARY_1, 1, FS.HALT)
        script.data[pos:pos+len(repl_cmd)] = repl_cmd.to_bytearray()

        # Note: Reordering so pc_id == 0 (first pc) is the halt.
        new_block = (
            EF().add(EC.call_pc_function(1, FID.ARBITRARY_2, 1, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_2, 1, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_2, 1, FS.HALT))
        )

        pos = script.get_function_start(0, FID.ARBITRARY_0)
        pos = script.find_exact_command(
            EC.call_pc_function(0, FID.ARBITRARY_2, 1, FS.CONT))
        script.data[pos:pos+len(new_block)] = new_block.get_bytearray()

        new_block = (
            EF()
            .add(EC.call_pc_function(1, FID.ARBITRARY_3, 1, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_3, 1, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_3, 1, FS.HALT))
        )
        
        pos = script.get_function_start(0, FID.ARBITRARY_1)
        pos = script.find_exact_command(
            EC.call_pc_function(0, FID.ARBITRARY_3, 1, FS.CONT))
        script.data[pos:pos + len(new_block)] = new_block.get_bytearray()

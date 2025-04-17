"""Openworld Blackbird Left Wing"""

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
    """EventMod for Blackbird Left Wing"""
    loc_id = ctenums.LocID.BLACKBIRD_LEFT_WING
    pc1_addr = 0x7F020E
    pc2_addr = 0x7F0210
    pc3_addr = 0x7F0212

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Blackbird Left Wing for an Open World.
        - Add Crono and Magus to the map.
        - Change the "We don't have all our stuff" dialog.
        - Change the post-Golem Boss scene
        """
        cls.modify_stuff_missing_text(script)
        cls.modify_battle_scenes(script)
        owu.add_exploremode_to_partyfollows(script)
        cls.add_crono_and_magus(script)


    @classmethod
    def modify_stuff_missing_text(cls, script: Event):
        """
        Change the "Stuff missing" text with a generic option.
        """

        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, 1),
            script.get_function_start(0x17, FID.STARTUP)
        )
        end = script.find_exact_command(EC.end_cmd(), pos)

        change_loc_cmd = get_command(bytes.fromhex("E076030216"))  # copied
        new_block = (
            EF().add(EC.decision_box(
                script.add_py_string(
                    "Some items are still missing.{line break}"
                    "   Don't care.{line break}"
                    "   Return.{null}"
                ), 1, 2, 'top'
            )).add_if(
                EC.if_result_equals(2),
                EF().add(change_loc_cmd).add(EC.return_cmd())
            ).add(EC.party_follow()).add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )

        script.insert_commands(new_block.get_bytearray(), pos)


    @classmethod
    def modify_battle_scenes(cls, script: Event):
        """
        Modify the scenes before and after the Golem Boss battle.
        - Handle having Crono and Magus when fighting the Golem Boss
        - Skip many scenes after the fight and go straight to jumping on the Epoch
        """

        # The Golem Boss scene is in Obj16, Startup in a coordinate loop.
        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.AYLA),
            script.get_function_start(0x16, FID.STARTUP)
        )
        end = script.find_exact_command(
            EC.call_obj_function(0x15, FID.ARBITRARY_0, 4, FS.HALT),
            pos
        )
        script.delete_commands_range(pos, end)

        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.AYLA), pos)
        end = script.find_exact_command(
            EC.assign_val_to_mem(1, 0x7F00D2, 1), pos
        )
        script.delete_commands_range(pos, end)

        # Copy other parts of the script to get the Epoch to fly by and have the party
        # jump on it.
        epoch_flyby = (
            EF()
            .add(EC.set_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD))
            .add(EC.play_song(0x22)).add(EC.pause(1))
            .add(EC.call_obj_function(6, FID.ARBITRARY_0, 4, FS.SYNC))
            .add(EC.call_obj_function(7, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.call_obj_function(8, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.call_obj_function(9, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_2, 4, FS.HALT))
            .add(EC.pause(2))
            .add(EC.play_song(0x16))
            .add(EC.move_party(0x0E, 0x06, 0x0C, 0x08, 0x10, 0x08))
            .add(EC.generic_command(0xE7, 7, 0))
            .add(EC.call_pc_function(0, FID.ARBITRARY_5, 4, FS.HALT))
            .add(EC.assign_val_to_mem(
                7, memory.Memory.BLACKBIRD_LEFT_WING_CUTSCENE_COUNTER, 1))
            .add(EC.change_location(ctenums.LocID.REBORN_EPOCH, 7, 0x19,
                                    Facing.UP, 0, False))
        )
        script.insert_commands(epoch_flyby.get_bytearray(), pos)

    @classmethod
    def add_crono_and_magus(cls, script: Event):
        """
        Add Crono and Magus to the scene.
        """

        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 6)
        owu.insert_pc_object(script, ctenums.CharID.CRONO, 1, 1)

        # The copied objects have some references to Marle's pc-index.  Update to match
        # the new characters.

        # Some of these references are in startup and OK to ignore because we never
        # enter this location from the cutscene now.  Just replace them all.
        for obj_id in (1, 7):
            pos = script.get_object_start(obj_id)
            pc_id = obj_id-1
            for _ in range(12):
                pos, cmd = script.find_command([0x12], pos)
                script.data[pos+2] = pc_id

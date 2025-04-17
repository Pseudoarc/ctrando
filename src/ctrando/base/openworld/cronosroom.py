"""Openworld Crono's Room"""

from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Crono's Room """
    loc_id = ctenums.LocID.CRONOS_ROOM

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Crono's Room Event.
        - Link other PC's arbs to Crono's and change Crono calls to PC1
        - Modify the clone pickup to use flags instead of storyline.
        """
        cls.modify_pc_objs(script)
        cls.modify_wakeup_scene(script)
        cls.modify_clone_pickup(script)

    @classmethod
    def modify_clone_pickup(cls, script: Event):
        """
        Allow the clone item to be picked up based on flags.
        Remove the mom cutscene.
        """
        clone_obj_id = 0x13
        new_clone_pickup = (
            EF().add_if(
                EC.if_not_flag(memory.Flags.HAS_BEKKLER_ITEM),
                EF()
                .add(EC.set_own_drawing_status(False))
                .add(EC.play_song(0x3D))
                .add(EC.reset_flag(memory.Flags.WON_CRONO_CLONE))
                .add(EC.set_explore_mode(False))
                .append(owu.get_add_item_block_function(
                    ctenums.ItemID.CLONE,
                    memory.Flags.HAS_BEKKLER_ITEM,
                    owu.add_default_treasure_string(script)
                ))
                .add(EC.set_explore_mode(True))
                .add(EC.generic_command(0xEE))
                .add(EC.play_song(0x1E))
                .add(EC.remove_object(clone_obj_id))
                .add(EC.return_cmd())
            )
        )

        # Remove the normal clone pickup scene.
        pos = script.get_function_start(clone_obj_id, FID.ACTIVATE)
        script.insert_commands(new_clone_pickup.get_bytearray(), pos)
        pos += len(new_clone_pickup)
        end = script.find_exact_command(EC.play_sound(2), pos)
        script.delete_commands_range(pos, end)

        # Remove mom spawning during clone pickup
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_GASPAR_ITEM),
        )
        script.delete_jump_block(pos)

    @classmethod
    def modify_wakeup_scene(cls, script: Event):
        """
        Change Crono calls to first PC calls.
        """
        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_0, 6, FS.CONT),
            script.get_object_start(8)
        )
        new_cmd = EC.call_pc_function(0, FID.ARBITRARY_5, 6, FS.CONT)
        script.data[pos:pos+len(new_cmd)] = new_cmd.to_bytearray()

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_2, 4, FS.CONT)
        )
        new_cmd = EC.call_pc_function(0, FID.ARBITRARY_6, 4, FS.CONT)
        script.data[pos:pos+len(new_cmd)] = new_cmd.to_bytearray()

    @classmethod
    def modify_pc_objs(cls, script: Event):

        startup_block = (
            EF().add_if(
                EC.if_storyline_counter_lt(2),
                EF().add(EC.set_own_facing('up'))
                .add(EC.set_object_coordinates_tile(0x1A, 0x08))
                .add(EC.script_speed(0x10))
                .add(EC.set_move_speed(0x10))
                .add(EC.generic_command(0x8E, 0x26))  # Sprite prio
            )
        )
        startup_block_b = startup_block.get_bytearray()

        for obj_id in range(2, 8):
            pos = script.find_exact_command(
                EC.return_cmd(),
                script.get_object_start(obj_id)
            )
            script.insert_commands(startup_block_b, pos)

        for obj_id in range(1, 8):
            script.link_function(
                obj_id, FID.ARBITRARY_5, 1, FID.ARBITRARY_0
            )
            script.link_function(
                obj_id, FID.ARBITRARY_6, 1, FID.ARBITRARY_2
            )

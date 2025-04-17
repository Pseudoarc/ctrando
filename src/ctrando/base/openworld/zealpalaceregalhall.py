"""Openworld Zeal Palace Regal Hall"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# This event uses storyline to compute a value in 0x7F0210
# 0xA5 <= Storyline < 0xA8 [Charged Pen, Captured) --> 3
# 0xA2 <= Storyline < 0xA5 [Schala Opens, Charged Pen) --> 2
# Storyline < 0xA2 and Shala's room scene seen --> 1
# Otherwise --> 0

class EventMod(locationevent.LocEventMod):
    """EventMod for Zeal Palace Regal Hall"""
    loc_id = ctenums.LocID.ZEAL_PALACE_REGAL_HALL
    room_status_addr = 0x7F0210  # See notes above

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Zeal Palace Regal Hall Event.
        - Trigger the sealed door with the PENDANT_CHARGED flag.
        - Change the fake exit to always go to the room with the golem.
        """

        # Most generic commands are color commands that aren't implemented yet
        new_activate = (
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE),
                EF().add(EC.set_explore_mode(False))
                .add(EC.move_party(0x07, 0x0B, 0x06, 0x0C, 0x09, 0x0C))
                .add(EC.set_object_script_processing(0xA, True))
                .add(EC.call_obj_function(0xA, FID.ARBITRARY_2, 4, FS.HALT))
                .add(EC.play_sound(9)).add(EC.play_sound(9))
                .add(EC.set_own_drawing_status(False))
                .add(EC.set_object_script_processing(0xB, True))
                .add(EC.call_obj_function(0xB, FID.ARBITRARY_0, 4, FS.HALT))
                .add(EC.pause(0.5))
                .add(EC.generic_command(0xF1, 0x9F, 0x02))  # Color math
                .add(EC.generic_command(0xF3))
                .add(EC.generic_command(0xF1, 0x80, 0x01)).add(EC.generic_command(0xF3))
                .add(get_command(
                    bytes.fromhex("E50706080810063B")))  # copytiles (copied)
                .add(EC.play_sound(0x51))
                .add(get_command(bytes.fromhex("2E507102F002")))
                .add(get_command(bytes.fromhex("2E507507F002"))).add(EC.pause(0.875))
                .add(get_command(bytes.fromhex("E51706180807063B")))
                .add(EC.pause(0.125))
                .add(EC.play_sound(0x56))
                .add(EC.set_flag(memory.Flags.HAS_OPENED_ZEAL_THRONE_DOOR))
                .add(EC.remove_object(0xB))
                .add(EC.call_obj_function(0xA, FID.ARBITRARY_1, 4, FS.HALT))
                .add(EC.remove_object(0xA))
                .add(EC.party_follow()).add(EC.set_explore_mode(True))
                .add(EC.return_cmd())
            ).add(EC.play_sound(1))
            .add(EC.auto_text_box(
                script.add_py_string("Charged Pendant is required.{null}")
            )).add(EC.return_cmd())
        )

        script.set_function(0xD, FID.ACTIVATE, new_activate)
        script.set_function(0xD, FID.TOUCH, EF().add(EC.return_cmd()))

        # Change fake exit
        pos = script.find_exact_command(
            EC.if_mem_op_value(cls.room_status_addr, OP.LESS_THAN, 4),
            script.get_object_start(0xE)
        )
        script.delete_jump_block(pos)




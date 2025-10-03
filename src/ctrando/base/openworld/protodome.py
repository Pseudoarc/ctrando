"""Openworld Proto Dome"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


# Event Notes
# - Storyline 0x3C is set by picking up Robo
# - Storyline 0x42 is set when the R-Series is defeated
# - Storyline 0x45 is set when Robo is fixed

# - 7F0150 is used for a few purposes
#   - Bits 0x01, and 0x02 indicate whether it's Marle or Lucca respectively who
#     are staying behind.
#   - Bits 0x04 and 0x08 determine whether the fights have been completed

# - 7F0148 is used to track the scene with Robo getting repaired
# - PC arbitrary functions 0 - 4 are all common stuff.  The rest are PC-specific,
#   usually for cutscenes.


class EventMod(locationevent.LocEventMod):
    """EventMod for Proto Dome"""
    loc_id = ctenums.LocID.PROTO_DOME
    pause_pc_addr = 0x7F0240
    time_gauge_eot_addr = 0x7F0242

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Proto Dome Event.
        - Streamline PC objects to remove references to storyline/cutscene flags
          Recruit object handled separately.
        - Modify the entry fight to use a party move instead of pc-specific functions
        """
        cls.modify_startup(script)
        cls.modify_pc_objects(script)
        cls.modify_intro_battle(script)
        cls.modify_portal_door(script)
        cls.fix_enertron(script)

    @classmethod
    def modify_portal_door(cls, script: Event):
        """
        Change the door to be open when the flag is set.
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x42))

        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.PROTO_DOME_DOOR_UNLOCKED))

    @classmethod
    def modify_startup(cls, script: Event):
        """
        Remove various cutscene conditions from the startup.  Keep battles.
        """

        pos, _ = script.find_command([0x12])
        script.delete_jump_block(pos)  # Storyline == 0x42
        script.delete_jump_block(pos)  # Part of robo repair scene

        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0148, OP.LESS_THAN, 0xF), pos
        )
        end = script.find_exact_command(
            EC.play_song(0x2D), pos
        )
        script.delete_commands_range(pos, end)
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0148, OP.LESS_THAN, 0xF), pos
        )
        end = script.find_exact_command(EC.end_cmd(), pos)
        script.delete_commands_range(pos, end)

    @classmethod
    def modify_pc_objects(cls, script: Event):
        """
        Remove cutscene and storyline conditions from startup objects.
        The Proto Dome recruit handles the recruit separately.
        """

        for char_id in ctenums.CharID:
            obj_id = char_id + 1

            startup_func = (
                EF().add(EC.load_pc_in_party(char_id))
                .add(EC.return_cmd())
                .add(EC.set_move_destination(True, False))
                .set_label('loop')
                .add_if(
                    EC.if_mem_op_value(cls.pause_pc_addr, OP.EQUALS, 0),
                    EF().add(EC.set_controllable_once())
                    .jump_to_label(EC.jump_back(), 'loop')
                )
                .add(EC.break_cmd())
                .jump_to_label(EC.jump_back(), 'loop')
            )

            script.set_function(obj_id, FID.STARTUP, startup_func)
            script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))

    @classmethod
    def modify_intro_battle(cls, script: Event):
        """
        Change the opening battle to use a party move instead of pc functions.
        Also change the condition to have a max y coord check.
        """

        pos = script.get_function_start(0xF, FID.STARTUP)

        # Add a max y check for the intro battle.
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F021A, OP.LESS_THAN, 0x2D))
        script.wrap_jump_cmd(
            pos, EC.if_mem_op_value(0x7F021A, OP.GREATER_THAN, 0x26)
        )

        pos = script.find_exact_command(
            EC.call_obj_function(1, FID.ARBITRARY_6, 2, FS.CONT)
        )
        script.delete_commands(pos, 3)
        script.insert_commands(
            EC.move_party(0x37, 0x2A, 0x36, 0x2B, 0x38, 0x2B).to_bytearray(),
            pos
        )

    @classmethod
    def fix_enertron(cls, script: Event):
        """Allow the Enertron to work with non-max party size."""

        temp_addr, num_pcs_addr = 0x7F0230, 0x7F0232
        count_fn = owu.get_count_pcs_func(temp_addr, num_pcs_addr)

        pos = script.find_exact_command(
            EC.set_explore_mode(False),
            script.get_function_start(0x0E, FID.ACTIVATE)
        ) + 2

        script.insert_commands(count_fn.get_bytearray(), pos)

        for _ in range(2):
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F021E, OP.LESS_THAN, 3),
                pos
            )
            script.replace_jump_cmd(
                pos,
                EC.if_mem_op_mem(0x7F021E, OP.LESS_THAN, num_pcs_addr)
            )

"""Update Crono's Kitchen for an open world."""
from ctrando.common import ctenums, memory
from ctrando.strings import ctstrings
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, EF
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP

# Notes:
#  - Mom (0xF), Arb2 seems to be unused and has a MomFlags = 1 command that
#    might interfere with things if it ever gets run.
#  - Lots of complicated Mom Logic for greeting party members that needs to be
#    looked more closely at.
#  - Should allowance be a randomized check?  Crono Locked?

class EventMod(locationevent.LocEventMod):
    loc_id = ctenums.LocID.CRONOS_KITCHEN

    mom_obj = 0xF

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Crono's Kitchen (001) event.

        - Don't have mom ask you about Lucca's name (frees up a flag)
        - Allow picking up allowance regardless of storyline counter
        """
        cls.update_mom_startup(script)
        cls.update_mom_activate(script)


    @classmethod
    def update_mom_startup(cls, script: locationevent.LocationEvent):
        """
        Skip the Lucca naming scene at the start of the game.
        """
        mom_lucca_cmd = EC.if_flag(memory.Flags.MOM_UNUSED)  # was lucca name
        start = script.get_function_start(cls.mom_obj, 0)
        end = script.get_function_end(cls.mom_obj, 1)

        pos = script.find_exact_command(mom_lucca_cmd, start, end)
        script.delete_jump_block(pos)

        cmd = EC.set_object_coordinates_tile(0x5, 0x5)
        if script.data[pos] != 0x8B:
            raise ValueError('Expected Coordinate command')

        script.data[pos:pos+len(cmd)] = cmd.to_bytearray()

        pos = script.find_exact_command(mom_lucca_cmd, pos, end)
        vec_move = locationevent.get_command(script.data,
                                             pos+len(mom_lucca_cmd))

        script.insert_commands(vec_move.to_bytearray(), pos)
        pos += len(vec_move)

        del_end = script.find_exact_command(vec_move, pos, end)
        script.delete_commands_range(pos, del_end)

    @classmethod
    def update_mom_activate(cls, script: locationevent.LocationEvent):
        """
        Remove lock on MomFlags & 01.  Remove storyline check on allowance.
        """

        flag_check = EC.if_mem_op_value(
            memory.Memory.MOMFLAGS, OP.LESS_THAN, 1, 1, 0
        )

        # Mom's activate runs into her touch function.
        # Remove the check on MOMFLAGS to prematurely end the function
        start, end = script.get_function_bounds(cls.mom_obj, FID.TOUCH)
        pos = script.find_exact_command(flag_check, start, end)
        script.delete_jump_block(pos)

        # Remove the storyline < 0x27 check for allowance
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x27, 0),
            pos, end)
        script.delete_commands(pos, 1)

        # Add a Crono lock to the
        pos = script.find_exact_command(EC.set_explore_mode(False), pos)
        end = script.find_exact_command(EC.return_cmd(), pos) + 1
        jump_cmd = EC.if_pc_active(ctenums.CharID.CRONO)

        # Reminder: jumps are from the last byte of the jump cmd, so one more
        # than the length of the jumped-over block.
        jump_cmd.args[-1] = end-pos+1
        script.insert_commands(jump_cmd.to_bytearray(), pos)

        # Add dummy memset for later item assignment
        # Make a more uniform reward string.
        pos, _ = script.find_command([0xBB],  pos)
        str_id = script.data[pos+1]
        py_str = ctstrings.CTString.ct_bytes_to_ascii(script.strings[str_id])
        py_str = py_str.replace("{line break}            Received 200 G!{null}",
                                "{line break}Got 200 G!{null}")
        script.strings[str_id] = ctstrings.CTString.from_str(py_str, True)
        script.insert_commands(
            EC.assign_val_to_mem(0x00, 0x7F0200, 1)
            .to_bytearray(), pos
        )

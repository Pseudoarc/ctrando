"""Openworld Courtroom King's Trial"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import (
    EventCommand as EC,
    Operation as OP,
    get_command,
)
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Courtroom King's Trial"""
    loc_id = ctenums.LocID.KINGS_TRIAL

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Courtroom King's Trial for an Open World.
        - Prevent loading some objects when the scene is set for the boss fight.
        - Shorten the post-boss fight scene with Marle and the king.
        """
        cls.remove_objects_for_battle(script)
        cls.modify_marle_king_scene(script)
        cls.modify_marle_window_scene(script)

    @classmethod
    def modify_marle_window_scene(cls, script: Event):
        """
        Remove most dialogue from the scene where Marle crashes in.
        """

        keep_string_ids = (0xF, 0x10, 0x1E)
        pos, end = script.get_function_bounds(0xA, FID.ARBITRARY_3)

        while pos < end:
            cmd = get_command(script.data, pos)
            if cmd.command in EC.str_commands and cmd.args[0] not in keep_string_ids:
                script.data[pos: pos+len(cmd)] = \
                    EC.generic_command(0xAD, 0x04).to_bytearray()

            pos += len(cmd)

    @classmethod
    def modify_marle_king_scene(cls, script: Event):
        """
        Shorten the scene with Marle and the king.
        """

        pos, end = script.get_function_bounds(2, FID.ARBITRARY_3)

        while pos < end:
            cmd = get_command(script.data, pos)

            if cmd.command in EC.str_commands:
                script.data[pos: pos+len(cmd)] = \
                    EC.generic_command(0xAD, 0x08).to_bytearray()
            elif cmd.command == 0xAD:  # pause
                pause_duration = script.data[pos+1]
                if (0x10 <= pause_duration < 0x50):
                    pause_duration = 0x10
                elif (0x50 <= pause_duration < 0x100):
                    pause_duration = 0x20
                script.data[pos+1] = pause_duration
            elif cmd.command == 0xB7:  # loop animation
                script.data[pos+2] //= 2

            pos += len(cmd)



    @classmethod
    def remove_objects_for_battle(cls, script: Event):
        """
        Remove some objects during the boss fight to avoid sprite limits
        """

        # Can delete:
        #   - Object 0xB: The false witness against the king
        #   - Object 0xC: The paper the chancellor holds up in trial (small)
        #   - Object 0x19: The blue sparkle left by the Yakra key (or maybe not?)
        # Of these, only 0xB is significant.

        for obj_id in (0xC, 0xB):
            # remove_block = (
            #     EF().add_if(
            #         EC.if_mem_op_value(memory.Memory.KINGS_TRIAL_PROGRESS_COUNTER,
            #                            OP.EQUALS, 0x10),
            #         EF().add(EC.remove_object(obj_id))
            #         .add(EC.return_cmd()).add(EC.end_cmd())
            #     )
            # )

            remove_block = (
                EF()
                .add(EC.remove_object(obj_id))
                .add(EC.return_cmd()).add(EC.end_cmd())
            )

            script.insert_commands(
                remove_block.get_bytearray(),
                script.get_object_start(obj_id)
            )
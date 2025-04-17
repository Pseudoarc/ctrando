"""Module for altering the loading screen for open world CT."""
from ctrando.common.memory import Memory as Mem, Flags
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS
from ctrando.locations.eventfunction import EventFunction as EF

from ctrando.base import openworldutils as owu


class EventMod(locationevent.LocEventMod):
    loc_id = ctenums.LocID.LOAD_SCREEN

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Load Screen.
        - Skip the opening cutscene on 1000 AD's overworld and go straight to
        Crono's room.'
        - Actually go to Special Purpose Area to get the Leene's Bell/Wake up.
        - Any flags that need to be set will also get placed here.
        """

        char_lock_cmd = EC.generic_command(
            0x4A, Mem.CHARLOCK, 0x80)
        pos = script.find_exact_command(char_lock_cmd)
        script.delete_commands(pos, 1)

        pos, _ = script.find_command([0xE0], pos)  # change location
        new_change_loc_cmd = EC.change_location(
            ctenums.LocID.SPECIAL_PURPOSE_AREA,
            0x08, 0x08, 0
        )

        script.delete_commands(pos, 1)
        script.insert_commands(new_change_loc_cmd.to_bytearray(), pos)

        cls.set_initial_state(script)

    @classmethod
    def set_initial_state(cls, script: locationevent.LocationEvent):
        """
        Do whatever initial flag setting needs to be done,
        - Vortex Pt activate
        Set up initial Epoch status
        """

        starting_flags = (
            Flags.OW_VORTEX_ACTIVE,
            Flags.HAS_PRESENT_TIMEGAUGE_ACCESS,
            Flags.HAS_PREHISTORY_TIMEGAUGE_ACCESS,
            Flags.HAS_MIDDLE_AGES_TIMEGAUGE_ACCESS,
            Flags.EPOCH_OUT_OF_HANGAR,
        )

        set_flags_block = EF()
        for flag in starting_flags:
            set_flags_block.add(EC.set_flag(flag))

        flag_obj_id = script.append_empty_object()
        script.set_function(
            flag_obj_id, FID.STARTUP,
            EF().add(EC.return_cmd()).add(EC.end_cmd())
        )

        # Default memory sets Epoch at bogus coords on a bogus map.

        # Set Epoch in the present in vanilla spot
        # set_epoch_block = owu.get_epoch_set_block(
        #     ctenums.LocID.OW_PRESENT,
        #     epoch_x_coord=0x270, epoch_y_coord=0x258,
        #     require_flight_to_move=False
        # )

        set_epoch_block = owu.get_epoch_set_block(
            ctenums.LocID.OW_APOCALYPSE,  # Any unobtainable map should be ok.
            epoch_x_coord=0x270, epoch_y_coord=0x258,
            require_flight_to_move=False,
            require_epoch_to_move=False
        )

        # epoch_status_byte = Flags.EPOCH_OBTAINED.value.bit
        # # TODO: Remove when done testing
        # epoch_status_byte |= Flags.EPOCH_CAN_FLY.value.bit
        # set_epoch_block = (
        #     EF().add(EC.assign_val_to_mem(epoch_status_byte, Mem.EPOCH_STATUS, 1))
        #     .add(EC.set_flag(Flags.OBTAINED_EPOCH_FLIGHT))
        #     .append(set_epoch_block)
        # )

        set_magic_block = (
            EF().add(EC.assign_val_to_mem(0xFF, Mem.MAGIC_LEARNED, 1))
        )

        script.set_function(
            flag_obj_id, FID.ACTIVATE,
            set_epoch_block.append(set_flags_block).append(set_magic_block)
        )

        hook_cmd = EC.assign_val_to_mem(0, Mem.LOAD_SCREEN_STATUS, 1)
        pos = script.find_exact_command(hook_cmd) + len(hook_cmd)
        script.insert_commands(
            EC.call_obj_function(
                flag_obj_id, FID.ACTIVATE, 5, FS.HALT
            ).to_bytearray(), pos
        )

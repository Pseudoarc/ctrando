"""Change Medina Portal (Imp House) for open world."""
from ctrando.base import openworldutils as owu
from ctrando.common.memory import Flags
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event,\
    get_command
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS,\
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Medina Portal"""
    loc_id = ctenums.LocID.MEDINA_PORTAL
    temp_addr = 0x7F0220
    can_eot_addr = 0x7F0222

    @classmethod
    def modify(cls, script: Event):
        """
        Update Medina Portal
        - Remove the imp dialogue that triggers on first entry/exit.
        - Remove the first portal use animation.
        - Remove storyline mentions
        """

        cls.remove_imp_dialogue(script)
        cls.remove_first_portal_use_animation(script)
        cls.modify_portal_activation(script)
        cls.remove_storyline_mentions(script)

    @classmethod
    def remove_imp_dialogue(cls, script: Event):
        """
        Remove the imps talking to you when you first enter/exit.
        """

        pos, _ = script.find_command([0x22])  # Get PC Coords
        script.delete_commands(pos, 1)
        script.delete_jump_block(pos)  # Block for testing doorway
        script.delete_commands(pos, 1) # back goto

    @classmethod
    def remove_first_portal_use_animation(cls, script: Event):
        """
        Remove the shocked imp animation that plays when the Medina portal is
        first used.
        """
        start = script.find_exact_command(
            EC.if_mem_op_value(0x7F0199, OP.BITWISE_AND_NONZERO, 0x80)
        )
        pos, cmd = script.find_command([0x10], start)
        bytes_jump = cmd.args[-1]

        end = pos + 1 + bytes_jump
        script.delete_commands_range(start, end)

    @classmethod
    def remove_storyline_mentions(cls, script: Event):
        """Remove storyline getting/setting"""
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x4E)
        )
        script.delete_jump_block(pos)

    @classmethod
    def modify_portal_activation(cls, script: Event):
        """
        Make the portal go to EoT with gate key and >= 4 characters.  Otherwise,
        it goes to Prehistory.
        """

        # Put a portal-ready check in obj00, activate
        pos = script.get_function_start(0, FID.ACTIVATE)
        can_eot_func = owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr)
        script.insert_commands(
            can_eot_func.get_bytearray(), pos
        )

        pos = script.get_function_start(0xD, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.ENTERING_EOT_MEDINA), pos
        )

        # Copying from EoT change location to MM Portal
        change_loc_cmd = get_command(bytes.fromhex('DD10030A0B'))

        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.can_eot_addr, OP.NOT_EQUALS, 1),
                EF().add(change_loc_cmd)
                .add(EC.play_sound(0x37))
                .add(EC.generic_command(0xFF, 0x82))  # mode7
                .add(EC.return_cmd())
            ).get_bytearray(), pos
        )
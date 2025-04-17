"""Change Mystic Mountain Portal for open world."""
from ctrando.base import openworldutils as owu
from ctrando.common.memory import Flags
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event,\
    get_command
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS,\
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


# Notes:
# - This event uses an interesting method of testing PC-index.
#   0x7E1000 + 2*obj_id is some sort of object status byte.  For PCs it will hold
#   their PC-index (0, 1, 2)
# - There are some storyline references here.  The storyline is stored into
#   0x7F0210.  Comparisons are always == 0x6C or == 0x7D, so they can be ignored.
# - The 0xDD version of the changelocation command is used for this (and other)
#   transitions that need to play the portal animation.

class EventMod(locationevent.LocEventMod):
    """EventMod for Mystic Mountain Portal"""
    loc_id = ctenums.LocID.MYSTIC_MTN_PORTAL
    temp_addr = 0x7F0230
    can_eot_addr = 0x7F0232

    @classmethod
    def modify(cls, script: Event):
        """
        Update Mystic Mountain Portal
        - Change the portal to go to Medina or EoT depending on conditions.
        - Fix the touch == activate potential bugs.
        """

        can_eot_func = owu.get_can_eot_func(cls.temp_addr, cls.can_eot_addr)
        pos = script.get_function_start(0, FID.ACTIVATE)

        script.insert_commands(can_eot_func.get_bytearray(), pos)

        pos = script.get_function_start(0xA, FID.ACTIVATE)
        pos = script.find_exact_command(
            EC.if_has_item(ctenums.ItemID.GATE_KEY), pos
        )
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.set_flag(memory.Flags.ENTERING_EOT_MYSTIC_MTS), pos
        )

        # Copy bytes from EoT script
        change_loc_cmd = get_command(bytes.fromhex("DD24020704"))

        script.insert_commands(
            EF().add_if(
                EC.if_mem_op_value(cls.can_eot_addr, OP.NOT_EQUALS, 1),
                EF().add(change_loc_cmd)
                .add(EC.play_sound(0x37))
                .add(EC.generic_command(0xFF, 0x82))
                .add(EC.return_cmd())
            ).get_bytearray(), pos
        )

        # Give dummy touch function
        script.set_function(0xA, FID.TOUCH, EF().add(EC.return_cmd()))
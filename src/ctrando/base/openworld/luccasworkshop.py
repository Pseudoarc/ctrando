"""Update Lucca's Workshop for an open world."""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID

from ctrando.base import openworldutils as owu

class EventMod(locationevent.LocEventMod):
    """EventMod for Lucca's Workshop"""
    loc_id = ctenums.LocID.LUCCAS_WORKSHOP

    lucca_obj = 0x03
    taban_obj = 0x08

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Lucca's Workshop (004) event.

        - Make Taban always appear.
        - Remove usage of LUCCAFLAGS & 01 which was previously used for when
          Lucca had left Crono to escort Marle to the castle.
        """
        cls.update_lucca_object(script)
        cls.always_show_taban(script)
        cls.modify_taban_rewards(script)

    @classmethod
    def modify_taban_rewards(cls, script: locationevent.LocationEvent):
        """
        Make the Taban rewards all follow the normal script reward format.
        """
        pos = script.get_function_start(cls.taban_obj, FID.ACTIVATE)

        storyline_command_flag_triples = [
            (0xAE, EC.if_has_item(ctenums.ItemID.PENDANT_CHARGE), memory.Flags.TABAN_SUIT_GIVEN),
            (0x81, EC.if_flag(memory.Flags.HAS_FORGED_MASAMUNE), memory.Flags.TABAN_HELM_GIVEN),
            (0x51, EC.if_flag(memory.Flags.HECKRAN_DEFEATED), memory.Flags.TABAN_VEST_GIVEN)
        ]

        for storyline_val, condition, flag in storyline_command_flag_triples:
            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F0000, OP.GREATER_OR_EQUAL, storyline_val),
                pos
            )
            script.replace_jump_cmd(pos, condition)
            owu.update_add_item(script, pos, update_text=False)
            pos = script.find_exact_command(EC.set_flag(flag), pos)
            block = (
                EF()
                .add(EC.auto_text_box(6))
                .add(EC.play_song(0x3D))
                .add(EC.auto_text_box(owu.add_default_treasure_string(script)))
            )
            script.insert_commands(
                block.get_bytearray(), pos
            )
            pos += len(block)

        pos = script.find_exact_command(EC.auto_text_box(6), pos)
        script.delete_commands(pos, 3)







    @classmethod
    def update_sunstone_rewards(cls, script: locationevent.LocationEvent):
        """
        Make the gained items (Wondershot, Sunshades) use the normal
        format and string.
        """

        pos = script.get_function_start(3, FID.ARBITRARY_1)
        pos = script.find_exact_command(EC.add_item(    ctenums.ItemID.WONDERSHOT))
        owu.update_add_item(script, pos)

        pos = script.find_exact_command_opt(EC.add_item(ctenums.ItemID.SUN_SHADES))
        owu.update_charge_chest_base_loc(script, pos)

    @classmethod
    def update_lucca_object(cls, script: locationevent.LocationEvent):
        """
        Make Lucca's startup, activate, and touch normal.  In vanilla it is
        weird because Lucca appears as an NPC while Crono escorts Marle.
        """

        new_startup = (
            EF()
            .add(EC.load_pc_in_party(ctenums.CharID.LUCCA))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )

        new_activate = EF().add(EC.return_cmd())

        script.set_function(cls.lucca_obj, FID.STARTUP, new_startup)
        script.set_function(cls.lucca_obj, FID.ACTIVATE, new_activate)

    @classmethod
    def always_show_taban(cls, script: locationevent.LocationEvent):
        """
        Allow Taban to always appear.  Should free LUCCAFLAGS & 04.
        """
        taban_show_cmd = EC.if_flag(memory.Flags.LUCCA_UNUSED_04)
        start, end = script.get_function_bounds(cls.taban_obj, FID.STARTUP)
        pos = script.find_exact_command(taban_show_cmd, start, end)
        script.delete_commands(pos, 1)

        # delete an unneeded jump/hide command
        cmd = locationevent.get_command(script.data, pos)
        pos += len(cmd)
        script.delete_commands(pos, 2)

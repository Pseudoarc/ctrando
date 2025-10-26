"""Openworld North Cape"""

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
    """EventMod for North Cape"""
    loc_id = ctenums.LocID.NORTH_CAPE

    @classmethod
    def modify(cls, script: Event):
        """
        Modify North Cape for an Open World.
        - Remove storyline checks.
        - Remove checks related to the Magus flashback scene.
        - Default hide the sparkle (recruit enables).
        - Give everyone a normal startup function and let the recruit setter handle
          the rest.
        """
        cls.remove_extra_checks(script)
        cls.fix_magus_startup(script)
        cls.modify_pc_arbs(script)
        cls.modify_sparkle(script)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        # Save functions before messing with the pc objects
        stopping_arb = script.get_function(2, FID.ARBITRARY_0)
        surprise_arb = script.get_function(2, FID.ARBITRARY_1)

        for pc_id in ctenums.CharID:
            obj_id = pc_id + 1
            script.set_function(obj_id, FID.ACTIVATE, EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.TOUCH, EF().add(EC.return_cmd()))
            script.set_function(obj_id, FID.ARBITRARY_0, stopping_arb)
            script.set_function(obj_id, FID.ARBITRARY_1, surprise_arb)

    @classmethod
    def modify_sparkle(cls, script: Event):
        """
        Have ths sparkle launch directly into the boss fight.
        """
        sparkle_obj = 0x10
        script.set_function(
            sparkle_obj, FID.STARTUP,
            EF().add(EC.load_npc(0x71))
            .add(EC.set_object_coordinates_tile(7, 6))
            .add_if(
                EC.if_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
                EF().add(EC.set_own_drawing_status(False)))
            .add(EC.return_cmd()).add(EC.end_cmd())
        )

        script.set_function(
            sparkle_obj, FID.ACTIVATE,
            EF().add_if(
                EC.if_not_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED),
                EF().add(EC.party_follow())
                .add(EC.call_obj_function(9, FID.ACTIVATE, 1, FS.HALT))
            ).add(EC.return_cmd())
        )

        boss_obj = 8
        battle_fn = (
            EF()
            .add(EC.set_explore_mode(False))
            .add(EC.assign_val_to_mem(1, 0x7F020E, 1))  # Stop Fn
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_0, 4, FS.CONT))
            .add(EC.generic_command(0xE7, 0, 2))  # Scroll
            .add(EC.move_party(0x07, 0x09,
                               0x05, 0x09,
                               0x09, 0x09))
            .add(EC.remove_object(0x10))
            .add(EC.call_obj_function(8, FID.ACTIVATE, 1, FS.HALT))
            .add(EC.generic_command(0xD8, 0x93, 0xC0)) # battle
            .add(EC.call_obj_function(8, FID.TOUCH, 1, FS.HALT))
            .add(EC.assign_val_to_mem(0, 0x7F020E, 1))  # Stop Fn
            .add(EC.set_flag(memory.Flags.NORTH_CAPE_RECRUIT_OBTAINED))
            .add(EC.party_follow()).add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )

        script.set_function(9, FID.ACTIVATE, battle_fn)

    @classmethod
    def remove_extra_checks(cls, script: Event):
        """
        Remove unneeded code.  This is not strictly needed but it
        1) Frees up a flag (NC Flashback), and
        2) Makes the event much simpler to parse for the recruit setting later.
        """

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.VIEWING_NORTH_CAPE_MAGUS_FLASHBACK)
        )
        script.delete_jump_block(pos)
        script.delete_jump_block(pos)

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xD2)
        )

        script.delete_jump_block(pos)
        script.delete_jump_block(pos)

        script.insert_commands(
            EC.set_own_drawing_status(False).to_bytearray(), pos)

    @classmethod
    def fix_magus_startup(cls, script: Event):
        """
        Give Magus a normal startup function.
        """
        startup = (
            EF().add(EC.load_pc_in_party(ctenums.CharID.MAGUS))
            .add(EC.return_cmd())
            .add(EC.set_controllable_infinite())
        )
        script.set_function(7, FID.STARTUP, startup)


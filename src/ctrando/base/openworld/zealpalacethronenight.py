"""Openworld Zeal Palace Throne (Night)"""

# Note: This is the version of the room after returning with the Epoch.

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Zeal Palace"""
    loc_id = ctenums.LocID.ZEAL_PALACE_THRONE_NIGHT
    boss_obj = 0xA

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Zeal Palace Throne (Night) Event.
        - Replace Dalton with the Golem fight.
        - Remove text and special animations from the pre- and post-battle scene.
        """

        cls.modify_storyline_checks(script)
        cls.modify_boss_object_load(script)
        cls.modify_battle_scenes(script)
        cls.modify_ending_objects(script)

    @classmethod
    def modify_ending_objects(cls, script: Event):
        """
        Dummy out objects that are only used in an ending.
        """
        obj_ids = (0xE, 0xF, 0x10)
        for obj_id in obj_ids:
            pos = script.get_object_start(obj_id)
            script.insert_commands(
                EF().add_if(
                    EC.if_mem_op_value(0x7F0210, OP.NOT_EQUALS, 0x44),
                    EF().add(EC.return_cmd()).add(EC.end_cmd())
                ).get_bytearray(), pos
            )


    @classmethod
    def modify_storyline_checks(cls, script: Event):
        """
        Change a storyline check into a boss defeated check
        """
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xBD))
        script.replace_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.ZEAL_THRONE_BOSS_DEFEATED)
        )

    @classmethod
    def modify_boss_object_load(cls, script: Event):
        """
        Change Dalton load to golem.  Modify coordinates.
        """

        # Overwrite load with golem -- Now back to normal Dalton
        pos = script.get_object_start(cls.boss_obj)
        # new_load = EC.load_enemy(ctenums.EnemyID.GOLEM, 3, True)
        # script.data[pos: pos+len(new_load)] = new_load.to_bytearray()

        # Overwrite the coordinate function.  Golem is a bit taller than Dalton
        pos, _ = script.find_command([0x8D], pos)
        new_coord = EC.set_object_coordinates_pixels(0x180, 0x7B)
        script.data[pos: pos+len(new_coord)] = new_coord.to_bytearray()

        # Remove Dalton's angry animation that most bosses lack.
        pos, _ = script.find_command([0xAA], pos)
        script.delete_commands(pos, 1)

    @classmethod
    def modify_battle_scenes(cls, script: Event):
        """
        Remove text and extra animations from the pre- and post-battle scenes.
        Remove the storyline setting in favor of flag setting.
        """

        pos = script.get_function_start(8, FID.STARTUP)
        pos, _ = script.find_command([0xC2])
        script.delete_commands(pos, 1)

        pos = script.get_function_start(cls.boss_obj, FID.ARBITRARY_0)
        script.delete_commands(pos, 3)  # animation + 2 textboxes

        pos = script.find_exact_command(EC.static_animation(0xE))
        script.delete_commands(pos, 1)

        for _ in range(2):
            pos, __ = script.find_command([0xBB], pos)
            script.delete_commands(pos, 1)

        pos = script.find_exact_command(EC.set_storyline_counter(0xBD), pos)
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.ZEAL_THRONE_BOSS_DEFEATED))
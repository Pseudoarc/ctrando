"""Change Heckran Cave Entrance for open world."""
from ctrando.common.memory import Flags
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS,\
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Heckran's Cave Entrance"""
    loc_id = ctenums.LocID.HECKRAN_CAVE_ENTRANCE

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Entrance of Hecrkan's Cave.
        - Add a coordinate check to the first fight so that it doesn't trigger
          if you first enter from the vortex.
        - Fix the Jinn Bottle fight so that the battle isn't called from an
          enemy's object.
        """
        cls.alter_initial_fight(script)
        cls.fix_jinn_bottle_fight(script)

    @classmethod
    def alter_initial_fight(cls, script: locationevent.LocationEvent):
        """
        Add coordinate check for the initial battle so that it doesn't trigger
        when entering from the vortex.
        """
        pos, _ = script.find_command([0xD9])
        end_cmd = EC.set_flag(Flags.HECKRAN_CAVE_ENTRANCE_INITIAL_BATTLE)
        end = script.find_exact_command(end_cmd, pos) + len(end_cmd)

        block = EF.from_bytearray(script.data[pos: end])

        x_addr, y_addr = 0x7F0212, 0x7F0214
        wrapper = (
            EF().add_if(
                EC.if_mem_op_value(x_addr, OP.GREATER_OR_EQUAL, 0x1C),
                EF().add_if(
                    EC.if_mem_op_value(y_addr, OP.GREATER_OR_EQUAL, 0x15),
                    block
                )
            )
        )

        script.insert_commands(wrapper.get_bytearray(), pos)
        script.delete_commands_range(pos+len(wrapper), end+len(wrapper))

    @classmethod
    def fix_jinn_bottle_fight(cls, script: locationevent.LocationEvent):
        """
        Add a new object to call the battle for the Jinn bottle fight.
        """

        battle_obj = script.append_empty_object()
        script.set_function(battle_obj, FID.STARTUP,
                            EF().add(EC.return_cmd()).add(EC.end_cmd()))
        script.set_function(battle_obj, FID.ACTIVATE,
                            EF().add(EC.return_cmd()))
        script.set_function(
            battle_obj, FID.ARBITRARY_0,
            EF().add(EC.generic_command(0xD8, 0x10, 0x40))  # battle
            .add(EC.return_cmd())
        )

        pos, _ = script.find_command(
            [0xD8], script.get_function_start(0xA, FID.ACTIVATE)
        )
        script.delete_commands(pos, 1)
        script.insert_commands(
            EC.call_obj_function(
                battle_obj, FID.ARBITRARY_0, 5, FS.CONT
            ).to_bytearray(), pos
        )

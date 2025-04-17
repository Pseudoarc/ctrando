"""Openworld Denadoro Entrance"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP


class EventMod(locationevent.LocEventMod):
    """EventMod for Denadoro Entrance"""
    loc_id = ctenums.LocID.DENADORO_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Denadoro Entrance Event.
        - Change Tata cutscene to set a flag.
        - Maybe even just erase the Tata cutscene.
        """

        tata_flag = memory.Flags.TATA_SCENE_COMPLETE
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.LESS_THAN, 0x5D)
        )
        script.replace_jump_cmd(pos, EC.if_not_flag(tata_flag))

        pos = script.find_exact_command(EC.set_storyline_counter(0x5D))
        repl_cmd = EC.set_flag(memory.Flags.TATA_SCENE_COMPLETE)
        script.replace_command_at_pos(pos, repl_cmd)

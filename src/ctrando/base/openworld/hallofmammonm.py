"""Openworld Hall of the Mammon Machine"""

# Note: There is a Night version of this map which is only for the scene where
#       the party is imprisoned after the Golem fight.  The change is storyline-based
#       and we ignore changing it because we aren't letting the storyline progress to
#       that level.

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Hall of the Mammon Machine"""
    loc_id = ctenums.LocID.ZEAL_PALACE_HALL_OF_MAMMON
    temp_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Hall of the Mammon Machine Event.
        - Add a pendant check to the Mammon machine.
        - When there's nothing to do but polish, we can fix up the dialog.
          The script sets 0x7F0210 depending on storyline and uses that for dialog.
          We can leave it as-is because the storyline never advances.
        """


        pos = script.get_function_start(0x10, FID.ACTIVATE)
        # Activate begins with a check
        script.replace_jump_cmd(pos, EC.if_has_item(ctenums.ItemID.PENDANT))
        script.wrap_jump_cmd(
            pos, EC.if_not_flag(memory.Flags.HAS_USED_MAMMON_MACHINE))

        pos = script.find_exact_command(EC.set_storyline_counter(0xA5))
        block = (
            EF().add(EC.set_flag(memory.Flags.HAS_USED_MAMMON_MACHINE))
            .add(EC.assign_val_to_mem(ctenums.ItemID.PENDANT_CHARGE, 0x7F0200, 1))
            .add(EC.add_item_memory(0x7F0200))
            .add(EC.auto_text_box(owu.add_default_treasure_string(script)))
            .add(EC.reset_animation())
            .add((EC.party_follow()))
            .add(EC.set_explore_mode(True))
        )
        script.insert_commands(block.get_bytearray(), pos)
        pos += len(block)
        script.delete_commands(pos, 5)
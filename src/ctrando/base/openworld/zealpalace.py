"""Openworld Zeal Palace"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Zeal Palace"""
    loc_id = ctenums.LocID.ZEAL_PALACE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Zeal Palace Event.
        - Remove the decision box on the plant lady so that you can't say no to her.
        - TODO: Consider putting a seed gate on this.
        """

        script.set_function(
            0xC, FID.ACTIVATE,
            EF().add(EC.set_own_facing_pc(0))
            .add_if(
                EC.if_flag(memory.Flags.PLANT_LADY_SAVES_SEED),
                EF().add(EC.auto_text_box(9))
                .add(EC.set_own_facing('down'))
                .add(EC.return_cmd())
            ).add(EC.auto_text_box(8))
            .add(EC.set_own_facing('down'))
            .add(EC.set_flag(memory.Flags.PLANT_LADY_SAVES_SEED))
            .add(EC.return_cmd())
        )
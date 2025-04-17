"""Openworld Death Peak Entrance"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event
from ctrando.locations.eventcommand import EventCommand as EC, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Death Peak Entrance"""
    loc_id = ctenums.LocID.DEATH_PEAK_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Death Peak Entrance Event.
        - Spawn Poyozos with clone and trigger
        """

        new_block = (
            EF()
            .add_if(
                EC.if_has_item(ctenums.ItemID.CLONE),
                EF().add_if(
                    EC.if_has_item(ctenums.ItemID.C_TRIGGER),
                    EF().add(EC.set_flag(memory.Flags.KEEPERS_NU_SENT_POYOZOS))
                )
            )
        )
        pos = script.get_object_start(0)
        script.insert_commands(new_block.get_bytearray(), pos)

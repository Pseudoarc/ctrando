"""Openworld Death Peak Entrance"""
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent as Event, FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.eventfunction import EventFunction as EF


class EventMod(locationevent.LocEventMod):
    """EventMod for Death Peak Entrance"""
    loc_id = ctenums.LocID.DEATH_PEAK_ENTRANCE

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Death Peak Entrance Event.
        - Spawn Poyozos with clone and trigger
        - Exploremode after partyfollow
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

        # Poyozo Exploremode
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(9, FID.ACTIVATE)
        )

        ins_block = (
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
        )

        script.insert_commands(ins_block.get_bytearray(), pos)
        pos += len(ins_block)

        script.delete_commands(pos, 1)

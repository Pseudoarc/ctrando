"""Openworld Dactyl Nest (Upper)"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

# Note that there are some storyline < 0xA8 checks here that we're leaving alone
# because they have no effect.  We're never letting storyline get past 3.

class EventMod(locationevent.LocEventMod):
    """EventMod for Dactyl Nest (Upper)"""
    loc_id = ctenums.LocID.DACTYL_NEST_UPPER

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Dactyl Nest (Upper) Event.
        - Add an NPC to block the way if the player has no Dreamstone.  Talking to the
          Laruba chief is only needed to scout the recruitment spot.
        - Fix a partyfollow after a battle.
        """

        # Add the "Keeper" npc to block access without Dreamstone
        obj_id = script.append_empty_object()
        script.set_function(
            obj_id, FID.STARTUP,
            EF().add_if(
                EC.if_has_item(ctenums.ItemID.DREAMSTONE),
                EF().add(EC.remove_object(obj_id))
                .jump_to_label(EC.jump_forward(), 'end')
            )
            .add(EC.load_npc(0x3F))
            .add(EC.set_object_coordinates_tile(0x1B, 0x11))
            .add(EC.set_own_facing('down'))
            .set_label('end')
            .add(EC.return_cmd())
            .add(EC.end_cmd())
        )
        script.set_function(
            obj_id, FID.ACTIVATE,
            EF()
            .add(EC.auto_text_box(
                script.add_py_string("KEEPER: Bring Dreamstone!{line break}"
                                     "Prove strength!{null}")
            )).add(EC.return_cmd())
        )

        # Fix the partyfollow
        pos = script.find_exact_command(
            EC.party_follow(),
            script.get_function_start(8, FID.TOUCH)
        ) + 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

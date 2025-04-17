"""Openworld Choras Carpenter 1F (600)"""

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
from ctrando.strings import ctstrings
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event

class EventMod(locationevent.LocEventMod):
    """EventMod for Choras Carpenter 1F (600)"""
    loc_id = ctenums.LocID.CHORAS_600_CARPENTER_RESIDENCE_1F

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Choras Carpenter 1F (600) for an Open World.
        - Fix the whole ruins on first payment (4000G instead of 2x 2000G).
        """

        new_decbox_str = ctstrings.CTString.from_str(
            "You want the Northern Ruins repaired?{linebreak+0}"
            "It'll cost you 4000 G.{line break}"
            "   Yes{line break}"
            "   No{null}"
        )
        new_decbox_str.compress()
        script.strings[2] = new_decbox_str

        new_carpenter_act = (
            EF().add(EC.set_explore_mode(False))
            .add_if(
                EC.if_flag(memory.Flags.NORTHERN_RUINS_REPAIRS_COMPLETE),
                EF().add(EC.auto_text_box(5))
                .jump_to_label(EC.jump_forward(), 'end')
            )
            .add(EC.decision_box(2, 2, 3))
            .add_if(
                EC.if_result_equals(2),
                EF().add_if_else(
                    EC.if_has_gold(4000),
                    EF()
                    .add(EC.set_flag(memory.Flags.NORTHERN_RUINS_LANDING_REPAIRED))
                    .add(EC.set_flag(memory.Flags.NORTHERN_RUINS_BASEMENT_CORRIDOR_REPAIRED))
                    .add(EC.set_flag(memory.Flags.NORTHERN_RUINS_ANTECHAMBER_REPAIRED))
                    .add(EC.sub_gold(4000))
                    .jump_to_label(EC.jump_forward(), 'lazy_blokes'),
                    # Else
                    EF().add(EC.auto_text_box(3))
                    .jump_to_label(EC.jump_forward(), 'end')
                )
            )
            .set_label('lazy_blokes')
            .add(EC.set_flag(memory.Flags.CHORAS_600_CARPENTER_AT_RUINS))
            .add(EC.set_own_facing('left'))
            .add(EC.auto_text_box(1))
            .add(EC.call_obj_function(9, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(0.438))
            .add(EC.call_obj_function(0xA, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(0.438))
            .add(EC.call_obj_function(0xB, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(0.438))
            .add(EC.call_obj_function(0xC, FID.TOUCH, 6, FS.CONT))
            .add(EC.pause(0.438))
            .add(EC.set_move_speed(0x20))
            .add(EC.move_sprite(0xB, 0x2B))
            .add(EC.move_sprite(0xB, 0x2F))
            .add(EC.set_own_drawing_status(False))
            .add(EC.pause(2))
            .set_label('end')
            .add(EC.set_explore_mode(True))
            .add(EC.return_cmd())
        )

        script.set_function(8, FID.ACTIVATE, new_carpenter_act)

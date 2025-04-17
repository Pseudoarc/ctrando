"""Openworld Castle Magus Hall of Apprehension"""

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
    """EventMod for Castle Magus Hall of Apprehension"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_HALL_APPREHENSION

    pc_wait_addr = 0x7F020C
    pc1_addr = 0x7F0214
    pc2_addr = 0x7F0216
    pc3_addr = 0x7F0218

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Hall of Apprehension for an Open World.
        - Give Ayla and Magus animations for battle poses.
        - Restore exploremode after Ozzie leaves.
        """
        cls.modify_pc_arbs(script)

        pos = script.get_function_start(0xA, FID.ACTIVATE) - 1
        script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give Ayla and Magus animation functions.
        """
        pc_anim_dict: dict[ctenums.CharID, list[int]] = {
            # face up, face left, face right
            ctenums.CharID.CRONO: [79, 51, 55],
            ctenums.CharID.MARLE: [47, 55, 59],
            ctenums.CharID.LUCCA: [49, 57, 61],
            ctenums.CharID.ROBO: [55, 49, 52],
            ctenums.CharID.FROG: [47, 55, 59],
            ctenums.CharID.AYLA: [43, 53, 58],  # ?
            ctenums.CharID.MAGUS: [125, 162, 165] # [58, 51, 55]  # ?
        }

        arb0 = (
            EF().set_label('start')
            .add_if(
                EC.if_mem_op_value(cls.pc_wait_addr, OP.EQUALS, 0),
                EF().add(EC.break_cmd())
                .jump_to_label(EC.jump_back(), 'end')
            )
            .add(EC.return_cmd())
        )

        script.set_function(ctenums.CharID.AYLA + 1, FID.ARBITRARY_0, arb0)
        script.set_function(ctenums.CharID.MAGUS + 1, FID.ARBITRARY_0, arb0)

        for char_id in ctenums.CharID:
            obj_id = char_id + 1
            anims: list[int] = pc_anim_dict[char_id]
            arb1 = (
                EF().add(EC.loop_animation(0xC, 1))
                .add_if(
                    EC.if_mem_op_value(cls.pc1_addr, OP.EQUALS, char_id),
                    EF().add(EC.static_animation(anims[0]))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add_if(
                    EC.if_mem_op_value(cls.pc2_addr, OP.EQUALS, char_id),
                    EF().add(EC.static_animation(anims[1]))
                    .jump_to_label(EC.jump_forward(), 'end')
                ).add(EC.static_animation(anims[2]))
                .set_label('end')
                .add(EC.return_cmd())
            )

            script.set_function(obj_id, FID.ARBITRARY_1, arb1)

        for fid in (FID.ARBITRARY_2, FID.ARBITRARY_3):
            script.link_function(ctenums.CharID.AYLA+1, fid, 1, fid)
            script.link_function(ctenums.CharID.MAGUS+1, fid, 1, fid)
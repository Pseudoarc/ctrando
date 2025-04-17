"""Openworld Castle Magus Chamber of Guillotines"""

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

# Slash is in 0xB, Slash + Sword is in 0xC

class EventMod(locationevent.LocEventMod):
    """EventMod for Castle Magus Chamber of Guillotines"""
    loc_id = ctenums.LocID.MAGUS_CASTLE_GUILLOTINES

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Castle Magus Chamber of Guillotines for an Open World.
        - Restore exploremode after Ozzie's text.
        - Add capability for Magus and Ayla to hit the guillotines.
        - TODO:  There's a bug where guillotines only check the low byte of hp.
                 Fix it or keep it vanilla?  For now I'm keeping the bug for Magus/Ayla.
        """
    
        pos = script.get_object_start(8)
        for _ in range(3):
            pos = script.find_exact_command(EC.party_follow(), pos) + 1
            script.insert_commands(EC.set_explore_mode(True).to_bytearray(), pos)

        cls.modify_pc_arbs(script)
        cls.modify_guillotine_hit(script)

    @classmethod
    def modify_guillotine_hit(cls, script: Event):
        """
        Add routines to reduce Ayla and Magus's HP
        """
        temp_hps: dict[ctenums.CharID, int] = {
            ctenums.CharID.AYLA: 0x7F0232,
            ctenums.CharID.MAGUS: 0x7F0234
        }
        ayla_hp_addr = 0x7E2603 + 0x50*ctenums.CharID.AYLA
        ayla_temp_hp_addr = 0x7F0232
        magus_hp_addr = 0x7E2603 + 0x50 * ctenums.CharID.MAGUS
        magus_temp_hp_addr = 0x7F0234

        guillotine_blade_objs = (0xB, 0xE, 0x11, 0x14, 0x17, 0x1A)

        def get_hit_fn(char_id: ctenums.CharID,
                       hp_addr: int,
                       temp_hp_addr: int) -> EF:
            """
            Mimic bugged behavior of guillotines by using 1 byte instead of 2.
            """
            return (
                EF().add_if(
                    EC.if_pc_active(char_id),
                    EF().add_if_else(
                        EC.if_mem_op_value(temp_hp_addr, OP.GREATER_THAN, 0x32, 1),
                        EF().add(EC.sub(temp_hp_addr, 0x32, 1)),
                        EF().add(EC.assign_val_to_mem(1, temp_hp_addr, 1))
                    ).add(EC.assign_mem_to_mem(temp_hp_addr, hp_addr, 2))
                )
            )


        for blade_obj in guillotine_blade_objs:
            pos = script.find_exact_command(
                EC.assign_mem_to_mem(0x7E2603, 0x7F021A, 2),
                script.get_function_start(blade_obj, FID.TOUCH)
            )

            script.insert_commands(
                EF().add(EC.assign_mem_to_mem(ayla_hp_addr, ayla_temp_hp_addr, 2))
                .add(EC.assign_mem_to_mem(magus_hp_addr, magus_temp_hp_addr, 2))
                .get_bytearray(), pos
            )

            pos = script.find_exact_command(
                EC.if_mem_op_value(0x7F021A, OP.GREATER_THAN, 0x32, 1),
                pos
            )
            end = script.find_exact_command(EC.if_pc_active(ctenums.CharID.MARLE), pos)
            jump_bytes = end+1-pos

            script.insert_commands(
                get_hit_fn(ctenums.CharID.AYLA, ayla_hp_addr, ayla_temp_hp_addr)
                .append(get_hit_fn(ctenums.CharID.MAGUS, magus_hp_addr, magus_temp_hp_addr))
                .add(EC.if_pc_active(ctenums.CharID.CRONO, jump_bytes))
                .get_bytearray(), pos
            )




    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Give Ayla and Magus some animations for being hit by the guillatine.
        """

        for pc_id in (ctenums.CharID.AYLA, ctenums.CharID.MAGUS):
            obj_id = pc_id + 1
            for fid in (FID.ARBITRARY_0, FID.ARBITRARY_1, FID.ARBITRARY_2,
                        FID.ARBITRARY_3):
                script.link_function(obj_id, fid,
                                     1, fid)

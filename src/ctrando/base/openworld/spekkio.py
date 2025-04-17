"""Openworld Spekkio"""
from dataclasses import dataclass

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, Facing, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Spekkio"""
    loc_id = ctenums.LocID.SPEKKIO
    pc1_level_addr = 0x7F020C
    assign_tech_level_addr = 0x7F0250
    assign_tech_bitmask = 0x7F0252
    temp_tech_levl_addr = 0x7F0254
    temp_addr = 0x7F0256

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Spekkio Event.
        - Remove opening dialogue (?)
        - Instead of setting the magic bits, have Spekkio increase the party's tech levels.
        """

        cls.set_tech_level_values(script)
        cls.modify_magic_learning_fn(script)
        cls.modify_spekkio_object(script)

    @classmethod
    def set_tech_level_values(cls, script: Event):
        """
        Set the target tech level/bitmask when loading Spekkio.
        """

        spekkio_load_tech_level_dict = {
            ctenums.EnemyID.SPEKKIO_FROG: 3,
            ctenums.EnemyID.SPEKKIO_KILWALA: 4,
            ctenums.EnemyID.SPEKKIO_OGRE: 5,
            ctenums.EnemyID.SPEKKIO_OMNICRONE: 6,
            ctenums.EnemyID.SPEKKIO_MASA_MUNE: 7,
            ctenums.EnemyID.SPEKKIO_NU: 8,
        }

        pos = script.get_function_start(0xA, FID.STARTUP)
        for enemy_id, tech_level in spekkio_load_tech_level_dict.items():
            pos = script.find_exact_command(EC.load_enemy(enemy_id, 3, True))

            script.insert_commands(
                EF()
                .add(EC.assign_val_to_mem(tech_level, cls.assign_tech_level_addr, 1))
                .get_bytearray(), pos
            )

    @classmethod
    def modify_magic_learning_fn(cls, script: Event):
        """
        Modify the routine that grants techs to magic-learners
        """

        magic_learners = {
            ctenums.CharID.CRONO,
            ctenums.CharID.MARLE,
            ctenums.CharID.LUCCA,
            ctenums.CharID.FROG
        }

        elem_swirl_dict = {
            ctenums.CharID.CRONO: 0x0E,
            ctenums.CharID.MARLE: 0x0C,
            ctenums.CharID.LUCCA: 0x0B,
            ctenums.CharID.FROG: 0x0D,
        }


        new_block = EF()
        new_block.add(
            EC.assign_mem_to_mem(cls.assign_tech_level_addr,
                                 memory.Memory.LOCEVENT_VALUE_STR_0,
                                 1)
            ).add(EC.assign_val_to_mem(0, cls.temp_addr, 1))

        for pc_id in magic_learners:
            tech_level_addr = 0x7E2830 + pc_id
            new_block.add_if(
                EC.if_pc_active(pc_id),
                EF()
                .add(EC.assign_mem_to_mem(tech_level_addr, cls.temp_tech_levl_addr, 1))
                .add_if(
                    EC.if_mem_op_mem(cls.temp_tech_levl_addr, OP.LESS_THAN, cls.assign_tech_level_addr),
                    EF().add(EC.assign_val_to_mem(1, cls.temp_addr, 1))
                )
            )

        magic_fn = (
            EF()
            .add(EC.call_obj_function(0xA, FID.ARBITRARY_3, 0, FS.HALT))
            .add(EC.text_box(0xD, False))
        )
        for pc_id in magic_learners:
            obj_id = pc_id + 1
            tech_level_addr = 0x7E2830 + pc_id
            elem_obj = elem_swirl_dict[pc_id]

            magic_fn.add_if(
                EC.if_pc_active(pc_id),
                EF()
                .add(EC.assign_mem_to_mem(tech_level_addr, cls.temp_addr, 1))
                .add_if(
                    EC.if_mem_op_mem(cls.temp_addr, OP.LESS_THAN, cls.assign_tech_level_addr),
                    EF()
                    .add(EC.call_obj_function(obj_id, FID.ARBITRARY_2, 4, FS.HALT))
                    .add(EC.call_obj_function(elem_obj, FID.ARBITRARY_0, 4, FS.HALT))
                    .add(EC.pause(2))
                    .add(EC.call_obj_function(elem_obj, FID.ARBITRARY_3, 4, FS.HALT))
                    .add(EC.call_obj_function(obj_id, FID.ARBITRARY_3, 4, FS.HALT))
                    # Comment next line if you want to view in TF
                    .add(EC.set_tech_level_from_memory(pc_id, cls.assign_tech_level_addr))
                    .add(EC.text_box(
                        script.add_py_string(
                            "{line break}"
                            f"    {{{pc_id}}}'s Tech Level set to {{value 8}}!{{null}}"
                        ), False
                    ))
                )
            )

        new_block.add_if(
            EC.if_mem_op_value(cls.temp_addr, OP.EQUALS, 1),
            magic_fn
        )

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.CRONO),
            script.get_function_start(9, FID.ARBITRARY_0)
        )
        end = script.find_exact_command(
            EC.call_pc_function(0, FID.ARBITRARY_1, 4, FS.HALT),
            pos
        )
        script.delete_commands_range(pos, end)
        script.insert_commands(new_block.get_bytearray(), pos)

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x4D))
        script.delete_jump_block(pos)

    @classmethod
    def modify_spekkio_object(cls, script: Event):
        """
        Modify Spekkio's object:
        - Remove storyline conditions for rounding the room.
        - Have Spekkio immediately give tech levels to people.
        """

        # Startup
        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_object_start(0xA)
        ) + 1
        script.insert_commands(EC.end_cmd().to_bytearray(), pos)

        pos += 1
        end = script.get_function_start(0xA, FID.ACTIVATE)
        script.delete_commands_range(pos, end)

        # Remove some dialogue about Crono being dead or not
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0xCB), pos)
        end = script.find_exact_command(
            EC.if_mem_op_value(0x7F020C, OP.GREATER_OR_EQUAL, 0x63),
            pos
        )
        script.delete_commands_range(pos, end)

        # The block involving the first visit and the room circling.
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x4D), pos)
        end = script.find_exact_command(
            EC.call_obj_function(9, FID.ARBITRARY_0, 4, FS.HALT),
            pos
        )
        script.delete_commands_range(pos, end)

        script.insert_commands(
            EF()
            .add(EC.set_explore_mode(False))
            .add(EC.assign_val_to_mem(1, 0x7F0210, 1))
            .add(EC.call_pc_function(0, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_0, 5, FS.CONT))
            .add(EC.move_party(7, 0xB, 5, 0xC, 9, 0xC))
            .get_bytearray(), pos
        )

        pos = script.find_exact_command(EC.return_cmd(), pos)
        script.insert_commands(
            EF().add(EC.party_follow()).add(EC.set_explore_mode(True))
            .get_bytearray(), pos
        )

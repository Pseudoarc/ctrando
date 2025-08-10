"""Openworld Reborn Epoch"""

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
    """EventMod for Reborn Epoch"""
    loc_id = ctenums.LocID.REBORN_EPOCH
    pc1_addr = 0x7F020C
    pc2_addr = 0x7F020E
    pc3_addr = 0x7F0210
    cur_gear_start = 0x7F0220
    saved_gear_start = 0x7F0228
    temp_epoch_status = 0x7F021E

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Reborn Epoch for an Open World.
        - Add Crono and Magus to the map.
        - Modify the gear restoration function
        """
        cls.modify_gear_restoration_function(script)
        cls.modify_battle_scenes(script)

        cls.add_crono_and_magus(script)

    @classmethod
    def add_crono_and_magus(cls, script: Event):
        """
        Add Crono and Magus objects to the scene.
        """
        owu.insert_pc_object(script, ctenums.CharID.MAGUS, 1, 6)
        owu.insert_pc_object(script, ctenums.CharID.CRONO, 1, 1)

        anim_repl: dict[ctenums.CharID, dict[int, int]] = {
            # order: face up, right, left
            ctenums.CharID.CRONO: {0x2F: 79, 0x3B: 55, 0x37: 51},
            ctenums.CharID.MAGUS: {0x2F: 135, 0x3B: 126, 0x37: 118},
        }

        # Some conditions reference pc-index directly.  Change those.
        # Also fix the static animations.
        for obj_id in (1, 7):
            pc_id = ctenums.CharID(obj_id - 1)
            pos, end = script.get_object_start(obj_id), script.get_object_end(obj_id)
            repl_dict = anim_repl[pc_id]
            while True:
                pos, cmd = script.find_command_opt([0x12, 0xAC], pos, end)

                if pos is None:
                    break
                if cmd.command == 0x12:  # if mem op val
                    if script.data[pos+2] == 1:
                        script.data[pos+2] = pc_id
                elif cmd.command == 0xAC:  # Static anim
                    marle_anim = script.data[pos+1]
                    repl_anim = repl_dict[marle_anim]
                    script.data[pos+1] = repl_anim

                pos += len(cmd)

    @classmethod
    def modify_battle_scenes(cls, script: Event):
        """
        Skip the Blackbird destruction.  Return the items and go to the map.
        """

        # The battle takes place in Obj07, Startup

        # Remove a block that slightly alters the scene with Marle active.
        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE),
            script.get_object_start(7)
        )
        jump_bytes = script.data[pos+2]
        end = pos + 2 + jump_bytes
        script.delete_commands_range(pos, end)

        new_block = (
            EF().add(EC.call_pc_function(2, FID.ARBITRARY_5, 4, FS.SYNC))
            .add(EC.call_pc_function(1, FID.ARBITRARY_5, 4, FS.CONT))
            .add(EC.call_pc_function(0, FID.ARBITRARY_5, 4, FS.HALT))
            .add(EC.pause(1))
            .add(EC.set_flag(memory.Flags.EPOCH_OBTAINED_LOC))
            .add(EC.set_flag(memory.Flags.OBTAINED_EPOCH_FLIGHT))
            .add(EC.set_flag(memory.Flags.REBORN_EPOCH_BOSS_DEFEATED))
            .add_if(
                # If we got here by completing the Blackbird, restore items.
                EC.if_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD),
                EF().add(EC.reset_flag(memory.Flags.BLACKBIRD_ITEMS_TAKEN))
                .add(EC.set_flag(memory.Flags.BLACKBIRD_ITEMS_RECOVERED))
                .add(EC.assign_val_to_mem(0, memory.Memory.KEEPSONG, 1))
                .add(EC.assign_val_to_mem(0, memory.Memory.CHARLOCK, 1))
                .add_if(
                    EC.if_not_flag(memory.Flags.BLACKBIRD_FOUND_PC1_GEAR),
                    EF().add(EC.call_obj_function(0, FID.ARBITRARY_0, 4, FS.HALT))
                ).add_if(
                    EC.if_not_flag(memory.Flags.BLACKBIRD_FOUND_PC2_GEAR),
                    EF().add(EC.call_obj_function(0, FID.ARBITRARY_1, 4, FS.HALT))
                ).add_if(
                    EC.if_not_flag(memory.Flags.BLACKBIRD_FOUND_PC3_GEAR),
                    EF().add(EC.call_obj_function(0, FID.ARBITRARY_2, 4, FS.HALT))
                ).add(EC.auto_text_box(
                    script.add_py_string("All items (not money) left on the {linebreak+0}"
                                         "Blackbird have been restored!{null}")
                ))
            ).add(EC.pause(0.25))
        )

        epoch_status_block = (
            EF().add(EC.increment_mem(cls.temp_epoch_status))
            .add_if(
                EC.if_mem_op_value(cls.pc2_addr, OP.NOT_EQUALS, 0x80),
                EF().add(EC.increment_mem(cls.temp_epoch_status))
            ).add_if(
                EC.if_mem_op_value(cls.pc3_addr,OP.NOT_EQUALS, 0x80),
                EF().add(EC.increment_mem(cls.temp_epoch_status))
            ).add(EC.set_reset_bits(cls.temp_epoch_status, 0xE0))
            .add(EC.assign_mem_to_mem(cls.temp_epoch_status, memory.Memory.EPOCH_STATUS, 1))
            .add(EC.assign_val_to_mem(0x3F8, memory.Memory.EPOCH_X_COORD_LO, 2))
            .add(EC.assign_val_to_mem(0x1C0, memory.Memory.EPOCH_Y_COORD_LO, 2))
            .add(EC.assign_val_to_mem(2, memory.Memory.OW_MOVE_STATUS, 1))
            .add(EC.assign_val_to_mem(2, memory.Memory.OW_MOVE_STATUS_EXTRA, 1))
            .add(EC.play_song(0x13))
            .add(EC.darken(6)).add(EC.fade_screen())
            .add(EC.set_flag(memory.Flags.HAS_FUTURE_TIMEGAUGE_ACCESS))
            # If this was activated after the Blackbird, go to the Last Village.
            # Otherwise, go to the normal Dark Ages.
            .add_if_else(
                EC.if_flag(memory.Flags.HAS_COMPLETED_BLACKBIRD),
                EF().add(
                    EC.assign_val_to_mem(ctenums.LocID.OW_LAST_VILLAGE,
                                         memory.Memory.EPOCH_MAP_LO, 2)
                ).add(EC.change_location(ctenums.LocID.OW_LAST_VILLAGE, 0x7F, 0x38,
                                         0, 0, True)),
                EF().add(
                    EC.assign_val_to_mem(ctenums.LocID.OW_DARK_AGES,
                                         memory.Memory.EPOCH_MAP_LO, 2)
                ).add(EC.change_location(ctenums.LocID.OW_DARK_AGES, 0x7F, 0x38,
                                         0, 0, True)),
            )
        )

        pos = script.find_exact_command(
            EC.if_pc_active(ctenums.CharID.MARLE), pos
        )
        end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, end)
        script.insert_commands(
            new_block.append(epoch_status_block).get_bytearray(), pos
        )

        # Don't do the battle if Dalton is already defeated
        pos, _ = script.find_command(
            [0xD8], script.get_object_start(7)
        )
        pos -= 2

        script.insert_commands(
            EF()
            .add_if(
                EC.if_flag(memory.Flags.REBORN_EPOCH_BOSS_DEFEATED),
                EF().add(EC.jump_forward(1))
            ).get_bytearray(), pos
        )
        jump_st = script.find_exact_command(EC.jump_forward(1), pos)
        jump_target, _ = script.find_command([0xEB], jump_st)
        script.data[jump_st + 1] = jump_target - jump_st - 1

        # Remove Dalton if the fight is complete
        pos = script.find_exact_command(
            EC.load_enemy(ctenums.EnemyID.DALTON_PLUS, 3),
            script.get_function_start(0x8, FID.STARTUP)
        ) + 3
        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.REBORN_EPOCH_BOSS_DEFEATED),
                EF().add(EC.remove_object(0x8))
            ).get_bytearray(), pos
        )

    @classmethod
    def modify_gear_restoration_function(cls, script: Event):
        """
        Add cases for Magus and Crono to the gear returning script.
        """

        for party_pos in range(3):
            local_pc_addr = cls.pc1_addr + party_pos*2
            stored_pc_index = memory.Memory.BLACKBIRD_IMPRISONED_PC1 + party_pos

            store_pc_gear_block = EF()
            for pc_id in (ctenums.CharID.CRONO, ctenums.CharID.MAGUS):
                store_pc_gear_block.append(
                    get_gear_store_fn(pc_id, local_pc_addr, cls.cur_gear_start )
                )
            pos = script.get_function_start(0, FID.ARBITRARY_0 + party_pos)
            script.insert_commands(
                EF()
                .add_if(
                    EC.if_mem_op_value(local_pc_addr, OP.GREATER_THAN, 6),
                    EF().add(EC.return_cmd())
                ).get_bytearray(), pos
            )
            pos = script.find_exact_command(
                EC.if_mem_op_value(local_pc_addr, OP.EQUALS, 1), pos
            )
            script.insert_commands(store_pc_gear_block.get_bytearray(), pos)

            pos = script.find_exact_command(
                EC.if_mem_op_value(stored_pc_index, OP.EQUALS, 5), pos
            )
            script.delete_jump_block(pos)

            pos = script.find_exact_command(
                EC.if_mem_op_value(stored_pc_index, OP.EQUALS, 1), pos
            )

            recover_pc_gear_block = EF()
            for pc_id in (ctenums.CharID.CRONO, ctenums.CharID.MAGUS):
                recover_pc_gear_block.append(
                    get_recover_gear_fn(pc_id, stored_pc_index, cls.saved_gear_start)
                )

            script.insert_commands(recover_pc_gear_block.get_bytearray(), pos)


def get_gear_store_fn(
        pc_id: ctenums.CharID,
        pc_addr: int,
        store_start_addr: int
) -> EF:
    """
    Get a block that saves a PC's current gear
    """
    ret = EF()
    cur_gear_st = 0x7E2627 + 0x50*pc_id
    ret.add_if(
        EC.if_mem_op_value(pc_addr, OP.EQUALS, pc_id),
        EF().add(EC.assign_mem_to_mem(cur_gear_st, store_start_addr, 1))
        .add(EC.assign_mem_to_mem(cur_gear_st+1, store_start_addr+2, 1))
        .add(EC.assign_mem_to_mem(cur_gear_st+2, store_start_addr+4, 1))
        .add(EC.assign_mem_to_mem(cur_gear_st+3, store_start_addr+6, 1))
    )

    return ret

def get_recover_gear_fn(
        pc_id: ctenums.CharID,
        pc_addr: int,  # 7F but not script
        stored_gear_start_addr: int
) -> EF:
    """
    Get a block that equips a PC from memory.
    """
    cur_gear_st = 0x7E2627 + 0x50 * pc_id
    ret = EF()
    ret.add_if(
        EC.if_mem_op_value(pc_addr, OP.EQUALS, pc_id),
        EF().add(
            EC.assign_mem_to_mem(stored_gear_start_addr, cur_gear_st, 2)
        ).add(
            EC.assign_mem_to_mem(stored_gear_start_addr+2, cur_gear_st+2, 2)
        )
    )

    return ret

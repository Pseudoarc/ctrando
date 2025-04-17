"""Openworld End of Time"""
from typing import Optional

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
    """EventMod for End of Time"""
    loc_id = ctenums.LocID.END_OF_TIME

    @classmethod
    def get_pc_switch_obj_id(cls, char_id: ctenums.CharID) -> int:
        """
        Returns the object id of the npc for a recruited but nonactive party member.
        """
        return char_id + 0x1D

    @classmethod
    def modify(cls, script: Event):
        """
        Modify End of Time for an Open World.
        - Award EoT time gauge Access
        - Modify triggers for pillars of light showing.
        - Modify triggers for party members being present.
        - Modify Gaspar to avoid irrelevant dialogue.
        - Modify the bucket (unsure what exactly b/c depends on objectives)
        """

        pos = script.get_object_start(0)
        flag_func = (
            EF()
            .add(EC.set_flag(memory.Flags.HAS_EOT_TIMEGAUGE_ACCESS))
            .add_if(
                EC.if_flag(memory.Flags.HAS_DARK_AGES_PORTAL),
                EF()
                .add(EC.set_flag(memory.Flags.HAS_DARK_AGES_TIMEGAUGE_ACCESS))
                .add_if(
                    EC.if_flag(memory.Flags.OW_LAVOS_HAS_FALLEN),
                    EF().add(EC.set_flag(memory.Flags.HAS_LAIR_RUINS_PORTAL))
                )
            )
        )
        script.insert_commands(flag_func.get_bytearray(), pos)

        cls.modify_party_npcs(script)
        cls.modify_pillars_of_light(script)
        cls.modify_bucket_activation(script)
        cls.remove_intro_scene(script)
        cls.modify_storyline_checks(script)
        cls.modify_gaspar(script)
        cls.modify_npc_robo(script)

        owu.add_exploremode_to_partyfollows(script)

    @classmethod
    def modify_storyline_checks(cls, script: Event):
        """
        Remove many storyline triggers.  Update others to flags.
        - Remove "Hey." lock on doors and Epoch.
        - Remove storyline lock on Spekkio's Door
        - Remove storyline setting in the Time Egg object.
        - Remove storyline lock on Epoch dock
        """

        # Gate between pillars and Gaspar's area
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xCB),
            script.get_function_start(0x18, FID.TOUCH)
        )
        del_end = script.find_exact_command(EC.return_cmd(), pos)
        script.delete_commands_range(pos, del_end)

        # Spekkio's Door
        pos = script.get_function_start(0x19, FID.ACTIVATE)
        for _ in range(2):
            pos = script.find_exact_command(EC.if_storyline_counter_lt(0x4B))
            script.delete_jump_block(pos)

        # Time Egg storyline setting
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CRONO_REVIVED),
            script.get_object_start(0x1B)
        )
        script.delete_jump_block(pos)

        # Epoch dock "Hey." lock
        pos = script.get_function_start(0x24, FID.TOUCH)
        del_end = script.find_exact_command(
            EC.if_flag(memory.Flags.EPOCH_IN_EOT), pos
        )
        script.delete_commands_range(pos, del_end)



    @classmethod
    def modify_party_npcs(cls, script: Event):
        """
        Modify conditions to make the non-active party member NPCs appear.
        """
        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.CRONO_REVIVED),
            script.get_function_start(0, FID.ACTIVATE)
        )
        del_end = script.find_exact_command(
            EC.if_mem_op_value(0x7F020E, OP.EQUALS, 1), pos
        )

        repl_block_b = bytearray()
        for char_id in ctenums.CharID:
            npc_obj_id = cls.get_pc_switch_obj_id(char_id)

            # Doing this just as an EF leaves a goto pointing to the end of the
            # function which then gets extended when new things are added.
            repl_block_b.extend(
                EF().add_if_else(
                    EC.if_pc_recruited(char_id),
                    EF().add_if_else(
                        EC.if_pc_active(char_id),
                        EF().add(EC.set_object_drawing_status(npc_obj_id, False)),
                        EF().add(EC.set_object_drawing_status(npc_obj_id, True))
                    ),
                    EF().add(EC.set_object_drawing_status(npc_obj_id, False))
                ).get_bytearray()
            )
        script.delete_commands_range(pos, del_end)
        script.insert_commands(repl_block_b, pos)

    @classmethod
    def modify_pillars_of_light(cls, script: Event):
        """
        Change the draw conditions for pillars of light to not use storyline.
        - Split Tyrano and Dark Ages pillars.
        - Remove storyline locks from the starting three pillars
        """

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_DARK_AGES_PORTAL),
            script.get_function_start(0, FID.ACTIVATE)
        )
        cmd_pos, tyrano_portal_cmd = script.find_command([0xE4], pos)
        script.delete_commands(cmd_pos, 1)

        script.insert_commands(
            EF().add_if(
                EC.if_flag(memory.Flags.HAS_LAIR_RUINS_PORTAL),
                EF().add(tyrano_portal_cmd)
            ).get_bytearray(), pos
        )

        pos = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_DARK_AGES_PORTAL),
            script.get_object_start(0x16)
        )
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.HAS_LAIR_RUINS_PORTAL)
        )

        for obj_id in (0xF, 0x10, 0x11):
            pos = script.find_exact_command(
                EC.if_storyline_counter_lt(0x4D),
                script.get_object_start(obj_id)
            )
            script.delete_jump_block(pos)

    @classmethod
    def modify_bucket_activation(cls, script: Event):
        """
        Modify the bucket activation function.
        - For now just remove all of the storyline triggers.
        - TODO: Add hooks for objectives to activate the bucket.
        """
        bucket_obj = 9
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0xCB),
            script.get_function_start(bucket_obj, FID.ACTIVATE)
        )
        del_end = script.find_exact_command(
            EC.if_flag(memory.Flags.HAS_SEEN_GASPAR_BUCKET_WARNING),
            pos
        )
        script.delete_commands_range(pos, del_end)

        # Note: We can repurpose this flag for bucket availability.

    @classmethod
    def remove_intro_scene(cls, script: Event):
        """
        Remove the scene that would play on first entry to EoT.
        """
        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x48),
            script.get_object_start(0xE)
        )
        script.delete_jump_block(pos)

    @classmethod
    def modify_gaspar(cls, script: Event):
        """
        Modify Gaspar>
        - Remove plot-specific dialogue.
        - Remove storyline triggers.
        """
        gaspar_obj_id = 0x1C

        # Remove all the "Hey." triggers in startup.
        # But then add one back if the Gaspar item is available.
        item_available_flag = memory.Flags.HAS_ALGETTY_PORTAL
        pos = script.find_exact_command(
            EC.return_cmd(),
            script.get_object_start(gaspar_obj_id)
        ) + 1
        new_block = (
            EF().add_if(
                EC.if_flag(item_available_flag),
                EF().add_if(
                    EC.if_not_flag(memory.Flags.HAS_GASPAR_ITEM),
                    EF().add(EC.text_box(0x15))
                )
            ).add(EC.end_cmd())
        )
        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        del_end = script.get_function_start(gaspar_obj_id, FID.ACTIVATE)
        script.delete_commands_range(pos, del_end)

        # Completely re-do Gaspar's activate
        # 1) Check for giving the post-Zeal KI
        # 2) Possible objective-ish hints?
        # 3) "Think of me as your guide."

        new_act = (
            EF().add_if(
                EC.if_flag(item_available_flag),
                EF().add_if(
                    EC.if_not_flag(memory.Flags.HAS_GASPAR_ITEM),
                    EF().add(EC.auto_text_box(0x49))
                    .append(owu.get_add_item_block_function(
                        ctenums.ItemID.C_TRIGGER, memory.Flags.HAS_GASPAR_ITEM,
                        owu.add_default_treasure_string(script)
                    )).add(EC.return_cmd())
                )
            )  # Put possible objective hints here.
            .add(EC.auto_text_box(0x19))
            .add(EC.return_cmd())
        )
        script.set_function(gaspar_obj_id, FID.ACTIVATE, new_act)

    @classmethod
    def modify_npc_robo(cls, script: Event):
        """
        Remove Robo's autofollowing NPC from vanilla EoT first visit.
        """
        robo_npc_obj_id = 0x20

        pos = script.find_exact_command(
            EC.if_storyline_counter_lt(0x49),
            script.get_object_start(robo_npc_obj_id)
        )
        script.delete_jump_block(pos)

        pos = script.find_exact_command(EC.return_cmd(), pos) + 1
        script.insert_commands(EC.end_cmd().to_bytearray(), pos)

        del_st = pos+1
        del_end = script.get_function_start(robo_npc_obj_id, FID.ACTIVATE)
        script.delete_commands_range(del_st, del_end)

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x49), pos)
        script.delete_jump_block(pos)

"""Openworld Fiona's Forest Campfire"""

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
    """EventMod for Fiona's Forest Campfire"""
    loc_id = ctenums.LocID.FIONA_FOREST_CAMPFIRE
    temp_pc_addr = 0x7F0220

    @classmethod
    def modify(cls, script: Event):
        """
        Modify Fiona's Forest Campfire for an Open World.
        - Change all pc objects to load based on recruitment.
        - Remove the entity and all discussion thereof.
        - Save the active party for restoring after the event.
        """
        cls.modify_pc_loads(script)
        cls.modify_campfire_scene(script)
        cls.shorten_lucca_wakeup(script)

    @classmethod
    def shorten_lucca_wakeup(cls, script: Event):
        """
        Shorten the time it takes Lucca to wake up.
        """
        pos = script.find_exact_command(
            EC.generic_command(0xAD, 0xF0),
            script.get_object_start(3)
        )
        script.data[pos+1] = 0x50

        pos = script.find_exact_command(EC.generic_command(0xAD, 0x80), pos)
        script.data[pos+1] = 0x40

    @classmethod
    def modify_campfire_scene(cls, script: Event):
        """
        Remove dialogue.  Keep some time so Lucca can work on Robo.
        """

        pos, _ = script.find_command([0xC1])
        end = script.find_exact_command(
            EC.set_flag(memory.Flags.STARTING_LUCCA_FOREST_SCENE), pos
        )

        script.delete_commands_range(pos, end)


    @classmethod
    def modify_pc_loads(cls, script: Event):
        """
        Make PCs only load in the scene if they've been recruited.
        Robo and Lucca are guaranteed present
        """
        for pc_id in ctenums.CharID:
            if pc_id == ctenums.CharID.LUCCA:
                continue

            obj_id = pc_id + 1
            pos = script.get_object_start(obj_id)
            cmd_id = 0x81
            if pc_id in (ctenums.CharID.FROG, ctenums.CharID.ROBO):
                cmd_id = 0x80

            pos, _ = script.find_command([cmd_id], pos)

            # Choose party/nonparty load to avoid palette issues.
            new_block = (
                EF()
                .add_if_else(
                    EC.if_pc_active(pc_id),
                    EF().add(EC.load_pc_in_party(pc_id)),
                    EF().add(EC.load_pc_always(pc_id))
                )
            )

            script.insert_commands(new_block.get_bytearray(), pos)
            pos += len(new_block)
            script.delete_commands(pos, 1)

            # Hide non-recruited.  Crono/Magus already have this block.
            if pc_id in (ctenums.CharID.MARLE, ctenums.CharID.ROBO,
                         ctenums.CharID.FROG, ctenums.CharID.AYLA):
                pos = script.find_exact_command(EC.return_cmd(), pos)

                script.insert_commands(
                    EF().add_if_else(
                        EC.if_pc_recruited(pc_id),
                        EF(),
                        EF().add(EC.set_own_drawing_status(False))
                    ).get_bytearray(), pos
                )

        # for pc_id in (ctenums.CharID.MARLE, ctenums.CharID.ROBO,
        #               ctenums.CharID.FROG, ctenums.CharID.AYLA):
        #     obj_id = pc_id + 1
        #
        #     # In Vanilla, Frog, Lucca, and Robo are forced into the party, so they have
        #     # party loads.  We need to change them to always loads (except Lucca).
        #     if pc_id in (ctenums.CharID.FROG, ctenums.CharID.ROBO):
        #         pos = script.find_exact_command(EC.generic_command(0x80, pc_id),
        #                                         script.get_object_start(obj_id))
        #         script.data[pos] = 0x81
        #
        #         if pc_id == ctenums.CharID.ROBO:
        #             # Robo has no further changes since he's always in the scene
        #             continue
        #
        #     pos = script.find_exact_command(EC.return_cmd(), script.get_object_start(obj_id))
        #
        #     script.insert_commands(
        #         EF().add_if_else(
        #             EC.if_pc_recruited(pc_id),
        #             EF(),
        #             EF().add(EC.set_own_drawing_status(False))
        #         ).get_bytearray(), pos
        #     )
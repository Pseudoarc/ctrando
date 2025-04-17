"""Openworld Factory Ruins Power Core"""

from ctrando.base import openworldutils as owu
from ctrando.common import ctenums, memory
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP, get_command
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Factory Ruins Power Core"""
    loc_id = ctenums.LocID.FACTORY_RUINS_POWER_CORE
    pc3_addr = 0x7F0220
    @classmethod
    def modify(cls, script: Event):
        """
        Update the Factory Ruins Power Core Event.
        - Remove Robo-specific animation when the power is turned on
        - Remove Robo-specific animation when escaping.
        - Give Frog, Ayla, and Magus functions for moving during the escape.
        """

        cls.modify_pc_arbs(script)
        cls.modify_power_activation(script)
        cls.modify_escape(script)

    @classmethod
    def modify_pc_arbs(cls, script: Event):
        """
        Modify the PC arb functions.
        - Give everyone a function for escaping the closing walls.
        - Give everyone Robo's functions for holding the walls open so they can do it
          as PC1
        """

        def get_new_arb2(pc_id: ctenums.CharID, pc3_addr: int) -> EF:
            """
            Generate the new arb2 (move through closing walls) function
            """
            func = (
                EF().add_if_else(
                    EC.if_mem_op_value(pc3_addr, OP.EQUALS, pc_id),
                    EF().add(EC.move_sprite(0x34, 0x2D)),
                    EF().add(EC.move_sprite(0x33, 0x2D))
                ).add(EC.set_own_facing('up'))
                .add(EC.return_cmd())
            )
            return func

        # TF doesn't seem to like forward links.  So we'll just give Crono the
        # functions and have everyone link to him.
        hold_wall_func = script.get_function(5, FID.ARBITRARY_3)
        # Crono: 110 (surprise), 115, 116 (lumi hands up), 122 (normal  hands up),
        #        136 (shield pose), 145 (jumping sideways),
        #        174, 175 (also lumi hands up),
        # Marle: 90 (surprise), 101 (shield), 193 (aura hands out)
        # Lucca: 67 (surprise), 73 (hands out twirl), 76 (shield)
        # Robo: 0x58 is used
        # Frog: 90 (surprise), 97 (flex), 101 (shield), 126 (hands out cast),
        #       179 (part of slurp, v. good),
        # Ayla: 37 (spread out sideways, cat attack?), 44 (arms up), 90 (arms out wide),
        # Magus: 47 (scythe in front), 93 (shield), 103 (float cape up),
        #        134 (side attack)
        #        240 (black hole, back only)

        wall_hold_frame_dict: dict[ctenums.CharID, int] = {
            ctenums.CharID.CRONO: 145, # 136,
            ctenums.CharID.MARLE: 101,
            ctenums.CharID.LUCCA: 76,
            ctenums.CharID.ROBO: 0x58,
            ctenums.CharID.FROG: 179,
            ctenums.CharID.AYLA: 90,
            ctenums.CharID.MAGUS: 134
        }

        spin_out_func = script.get_function(5, FID.ARBITRARY_4)
        steam_off_func = script.get_function(5, FID.ARBITRARY_5)

        script.set_function(5, FID.ARBITRARY_3, EF())
        script.set_function(5, FID.ARBITRARY_4, EF())
        script.set_function(5, FID.ARBITRARY_5, EF())

        # PC Arbs:
        # - Arb0, Arb1 for elevators
        # - Arb2 for moving down when "Robo" holds the walls open
        # - Arb3 for emoting after "Robo Spins out"
        # - Arb4 for holding the door open
        # - Arb5 for spinning out
        # - Arb6 for steaming off (probably skip)

        script.set_function(2, FID.ARBITRARY_2,
                            get_new_arb2(ctenums.CharID.CRONO, cls.pc3_addr))
        script.set_function(2, FID.ARBITRARY_4, hold_wall_func)
        script.set_function(2, FID.ARBITRARY_5, spin_out_func)
        script.set_function(2, FID.ARBITRARY_6, steam_off_func)

        for char_id in ctenums.CharID:
            obj_id = char_id + 2
            if char_id != ctenums.CharID.CRONO:
                script.set_function(obj_id, FID.ARBITRARY_2,
                                    get_new_arb2(char_id, cls.pc3_addr))
                if char_id not in (ctenums.CharID.MARLE, ctenums.CharID.LUCCA):
                    script.link_function(obj_id, FID.ARBITRARY_3, 2, FID.ARBITRARY_3)
                script.set_function(obj_id, FID.ARBITRARY_4, hold_wall_func)
                script.link_function(obj_id, FID.ARBITRARY_5, 2, FID.ARBITRARY_5)
                # script.link_function(obj_id, FID.ARBITRARY_6, 2, FID.ARBITRARY_6)

            # Go back and modify the door holding animation frame
            pos = script.find_exact_command(
                EC.static_animation(0x58),
                script.get_function_start(obj_id, FID.ARBITRARY_4)
            )
            script.data[pos + 1] = wall_hold_frame_dict[char_id]

    @classmethod
    def modify_escape(cls, script: Event):
        """
        Modify the escape.
        - Triggered by flag instead of storyline
        - Everyone makes it through instead of Robo holding the walls open.
        """

        # The trigger is in an Obj00 loop
        pos = script.find_exact_command(
            EC.if_mem_op_value(0x7F0000, OP.EQUALS, 0x3F)
        )

        # Only trigger if power is on and R-Series is alive
        script.replace_jump_cmd(
            pos, EC.if_flag(memory.Flags.FACTORY_POWER_ACTIVATED)
        )
        script.wrap_jump_cmd(pos, EC.if_not_flag(memory.Flags.R_SERIES_DEFEATED))

        # Now this calls Obj01, Arb0 which holds the escape animations
        pos = script.find_exact_command(
            EC.call_obj_function(5, FID.ARBITRARY_3, 0, FS.CONT),
            script.get_function_start(1, FID.ARBITRARY_0)
        )
        script.replace_command_at_pos(
            pos,
            EC.call_pc_function(0, FID.ARBITRARY_4, 0, FS.CONT)
        )
        pos, _ = script.find_command([0xBB], pos)
        script.delete_commands(pos, 1)

        pos = script.find_exact_command(
            EC.call_obj_function(2, FID.ARBITRARY_2, 4, FS.CONT), pos
        )

        new_block = (
            EF()
            .add(EC.assign_mem_to_mem(memory.Memory.ACTIVE_PC3, cls.pc3_addr, 1))
            .add(EC.call_pc_function(1, FID.ARBITRARY_2, 4, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_2, 4, FS.CONT))
        )

        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 5)

        pos = script.find_exact_command(
            EC.call_obj_function(5, FID.ARBITRARY_4, 3, FS.HALT), pos
        )

        new_block = (
            EF().add(EC.call_pc_function(0, FID.ARBITRARY_5, 3, FS.HALT))
            .add(EC.call_pc_function(1, FID.ARBITRARY_3, 4, FS.CONT))
            .add(EC.call_pc_function(2, FID.ARBITRARY_3, 4, FS.CONT))
            .add(EC.pause(2))
        )

        script.insert_commands(new_block.get_bytearray(), pos)
        pos += len(new_block)
        script.delete_commands(pos, 7)




    @classmethod
    def modify_power_activation(cls, script: Event):
        """
        Modify what happens when the power switch is activated.
        - Change the condition from storyline == 0x3F to FACTORY_POWER_ACTIVATED
        - Remove Robo-specific animation
        - Remove all text.
        """

        power_obj_id = 0xA

        # Change the condition from storyline == 0x3F to FACTORY_POWER_ACTIVATED
        # The condition is what causes the function to just terminate with no action.
        pos = script.get_function_start(power_obj_id, FID.ACTIVATE)
        script.replace_jump_cmd(pos, EC.if_flag(memory.Flags.FACTORY_POWER_ACTIVATED))

        pos = script.find_exact_command(EC.pause(3), pos)
        script.data[pos + 1] = 0x10

        pos = script.find_exact_command(EC.pause(4), pos)
        script.data[pos + 1] = 0x10

        pos = script.find_exact_command(EC.if_pc_active(ctenums.CharID.ROBO), pos)
        script.delete_jump_block(pos)

        script.strings[2][0] = 0x1B  # Change {Robo} to {PC1}

        pos = script.find_exact_command(EC.assign_val_to_mem(0x3F, 0x7F0000, 1))
        script.replace_command_at_pos(
            pos, EC.set_flag(memory.Flags.FACTORY_POWER_ACTIVATED))


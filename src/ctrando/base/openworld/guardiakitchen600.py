"""Openworld Guardia Kitchen 600AD"""
from typing import Optional

from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Guardia Kitchen 600AD"""
    loc_id = ctenums.LocID.GUARDIA_KITCHEN_600

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Guardia Kitchen 600AD Event.
        - Have the chef always be in jerky-giving mode.
        - There is so much storyline-depednent dialog.  Try to pair that up
          with flags instead.
        """
        cls.modify_chef(script)
        cls.modify_storyline_triggers(script)


    @classmethod
    def modify_chef(cls, script: Event):
        """
        - Put the chef in a state where he'll always give the Jerky.
        - Make sure the chef doesn't disappear
        """
        chef_obj = 0xA

        # In startup, treat the chef as always in the "busy" state
        pos = script.get_function_start(chef_obj, FID.STARTUP)
        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x8A))
        script.delete_jump_block(pos)

        pos = script.find_exact_command(EC.if_storyline_counter_lt(0x54))
        script.delete_jump_block(pos)

        # In activate
        pos = script.get_function_start(chef_obj, FID.ACTIVATE)
        script.delete_jump_block(pos)  # Dialog during Cathedral quest
        script.delete_commands(pos, 1)  # If Zenan requested food

    @classmethod
    def modify_storyline_triggers(cls, script: Event):
        """
        Change storyline triggers to flag triggers where appropriate.
        - Remove all blocks that trigger when storyline < 0x54 because we're
          always in (at least) the zenan quest for obtainin the Jerky
        - Probably always assume we are pre-magus defeat as well.
        - It'd be nice to allow the party to order food (but it's <0x54)
        """

        pos: Optional[int] = script.get_object_start(0)
        while True:
            pos, cmd = script.find_command_opt([0x18], pos)
            if pos is None:
                break

            storyline_val = cmd.args[0]
            if storyline_val <= 0x54:
                script.delete_jump_block(pos)
            elif storyline_val == 0x8A:
                script.delete_commands(pos, 1)
            else:
                print(f'Uncaught storyline: {storyline_val:02X}')
                input()

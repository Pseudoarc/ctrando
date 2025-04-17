"""Update Prison Exterior for an open world."""
from ctrando.base.openworld import prisoncatwalks as pcat
from ctrando.common import ctenums
from ctrando.locations import locationevent


# The Trial Storyline values
# 2D . Trial ends
# 2E . Lucca comes to break Crono out of prison
# 30 . Escape Guardia Castle
# 33 . Escape through Guardia Forest Portal

class EventMod(locationevent.LocEventMod):
    """EventMod for Prison Exterior"""
    loc_id = ctenums.LocID.PRISON_EXTERIOR

    @classmethod
    def modify(cls, script: locationevent.LocationEvent):
        """
        Update the Prison Cells Event.
        - Add player objects so that the area can be revisited.
        - Change storyline triggers to flag triggers
        - During the prison break, change Crono to the imprisoned.
        """
        cls.update_pc_objects(script)

    @classmethod
    def update_pc_objects(cls, script: locationevent.LocationEvent):
        """
        Load any character for the imprisoned character.
        """

        # Crono's startup object goes like this:
        # Load Crono in party.
        # - If this is the first time in cell (not 0x7F0190 & 02) then do some
        #   intro wakeup animation, set the flag, and start the exec. timer.
        # - If coming up or down the hole in the floor/ceiling then play that
        #   animation.
        # - If storyline < 2E and crono is being taken to execution, play his
        #   march through the cells.

        pcat.modify_prison_crono_object(script, 1)
        pcat.modify_prison_lucca_object(script, 2)

        script.insert_copy_object(0, 2)
        pcat.make_prison_pc_object(script, 2, ctenums.CharID.MARLE)
        for ind in range(4):
            obj_id = script.append_empty_object()
            pcat.make_prison_pc_object(script, obj_id, ctenums.CharID(ind+3))

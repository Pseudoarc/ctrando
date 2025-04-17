"""Openworld Arris Dome Command"""
from ctrando.common import ctenums
from ctrando.locations import locationevent
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, \
    Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.locationevent import FunctionID as FID, LocationEvent as Event


class EventMod(locationevent.LocEventMod):
    """EventMod for Arris Dome Command"""
    loc_id = ctenums.LocID.ARRIS_DOME_COMMAND

    @classmethod
    def modify(cls, script: Event):
        """
        Update the Arris Dome Food Rafters Event.
        - Remove the "There it is!" scene with the rat.
        """
        script.dummy_object_out(0xB)

        activate_func = (
            EF().add_if(
                EC.if_mem_op_value(0x7F0214, OP.GREATER_OR_EQUAL, 0x27),
                EF().add_if(
                    EC.if_mem_op_value(0x7F0210, OP.EQUALS, 0),
                    EF().add(EC.play_sound(0x9F))
                    .add(EC.call_obj_function(8, FID.ARBITRARY_3, 4, FS.HALT))
                )
            )
        )

        # Show proto dome and day of lavos buttons on the computer
        script.set_function(0x9, FID.ACTIVATE, activate_func)
        script.set_function(0xA, FID.ACTIVATE, activate_func)
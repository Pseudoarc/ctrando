"""Minor tweaks to logic that require script changes."""

from ctrando.arguments import logicoptions
from ctrando.common import ctenums, memory

from ctrando.locations.locationevent import FunctionID as FID
from ctrando.locations.eventcommand import EventCommand as EC, FuncSync as FS, Operation as OP
from ctrando.locations.eventfunction import EventFunction as EF
from ctrando.locations.scriptmanager import ScriptManager

def apply_hard_lavos_end_boss(
        script_manager: ScriptManager
):
    script = script_manager[ctenums.LocID.LAVOS]
    pos = script.find_exact_command(
        EC.call_obj_function(8, FID.ARBITRARY_1, 4, FS.HALT)
    )
    script.insert_commands(
        EF()
        .add_if(
            EC.if_mem_op_value(memory.Memory.LAVOS_STATUS, OP.EQUALS, 3),
            EF()
            .add(EC.darken(0x10))
            .add(EC.fade_screen())
            .add(EC.change_location(
                ctenums.LocID.ENDING_SELECTOR_052, 0, 0, 0,
                1, True
            )).add(EC.return_cmd())
        )
        .get_bytearray(),
        pos
    )


def apply_logic_tweaks(
        logic_options: logicoptions.LogicOptions,
        script_manager: ScriptManager
):
    if logic_options.hard_lavos_final_boss:
        apply_hard_lavos_end_boss(script_manager)
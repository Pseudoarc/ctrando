from ctrando.locations.scriptmanager import ScriptManager
from ctrando.encounters.encountermods import (
    beastcave,
    blackomen, dactylnest, denadoromts, genodome, giantsclaw, heckrancave,
    lab32, maguscastle, mtwoe, oceanpalace, reptitelair
)

def apply_all_encounter_mods(script_manager: ScriptManager):
    heckrancave.apply_all_encounter_reduction(script_manager)
    reptitelair.apply_all_encounter_reduction(script_manager)
    denadoromts.apply_all_encounter_reduction(script_manager)
    dactylnest.apply_all_encounter_reduction(script_manager)
    beastcave.apply_all_encounter_reduction(script_manager)
    mtwoe.apply_all_encounter_reduction(script_manager)
    oceanpalace.apply_all_encounter_reduction(script_manager)
    genodome.apply_all_encounter_reduction(script_manager)
    maguscastle.apply_all_encounter_reduction(script_manager)
    giantsclaw.apply_all_encounter_reduction(script_manager)
    blackomen.apply_all_encounter_reduction(script_manager)
    lab32.apply_all_encounter_reduction(script_manager)
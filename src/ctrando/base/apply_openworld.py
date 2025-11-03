"""Module to apply all of the event modifications in the openworld package."""
import importlib
import pkgutil
from typing import Type

from ctrando.common import randostate
from ctrando.locations import locationevent

from ctrando.base import openworld
# from ctrando.base import basepatch, chesttext, apply_openworld_ow
# from ctrando.recruits import guardiaprison, leenesquare, manoriacathedral, starter,\
#     queenschamber, frogsburrow, protodome, northcape, deathpeak, \
#     dactylnest
# from ctrando.items import itemdata


# Register all openworld
_mod_classes: list[Type[locationevent.LocEventMod]] = []
for _, name, __ in pkgutil.walk_packages(openworld.__path__):
    if 'flycheck' in name:
        continue

    module = importlib.import_module('ctrando.base.openworld.'+name)

    if not hasattr(module, 'EventMod'):
        raise AttributeError(f'{module.__name__} has no EventMod')

    _mod_class = module.EventMod
    if not issubclass(_mod_class, locationevent.LocEventMod):
        raise TypeError(f'{module.__name__}.EventMod is not a LocEventMod')

    _mod_classes.append(_mod_class)


def apply_openworld(script_manager: randostate.ScriptManager):
    """Apply the openworld LocEventMods to the randomizer state."""
    for mod_class in _mod_classes:
        event = script_manager[mod_class.loc_id]
        mod_class.modify(event)


def main():
    # ct_rom = ctrom.CTRom.from_file('./ct.sfc')
    # ct_rom.make_exhirom()
    # basepatch.mark_initial_free_space(ct_rom)
    # basepatch.patch_blackbird(ct_rom)
    # item_db = itemdata.ItemDB.from_rom((ct_rom.getbuffer()))
    # item_db[ctenums.ItemID.PENDANT_CHARGE].set_name_from_str(" PendantChg")
    # item_db[ctenums.ItemID.PENDANT_CHARGE].set_desc_from_str(
    #     "The Pendant begins to glow..."
    # )
    # chesttext.apply_chest_text_hack(ct_rom, item_db)
    # basepatch.patch_timegauge_alt(ct_rom)
    # basepatch.patch_progressive_items(ct_rom)
    #
    # script_manager = randostate.ScriptManager(ct_rom)
    # ow_manager = randostate.OWManager(ct_rom)
    # apply_openworld(script_manager)
    # apply_openworld_ow.update_all_overworlds(ow_manager)
    #
    # exit_dict = locationtypes.get_exit_dict_from_ctrom(ct_rom)
    # del exit_dict[ctenums.LocID.LAB_32_EAST][1]
    #
    # starter.assign_pc_to_spot(ctenums.CharID.AYLA, script_manager)
    # guardiaprison.assign_pc_to_spot(ctenums.CharID.MAGUS, script_manager)
    # leenesquare.assign_pc_to_spot(ctenums.CharID.ROBO, script_manager)
    # manoriacathedral.assign_pc_to_spot(ctenums.CharID.MAGUS,
    #                                    script_manager)
    # queenschamber.assign_pc_to_spot(ctenums.CharID.ROBO, script_manager)
    # dactylnest.assign_pc_to_spot(ctenums.CharID.CRONO, script_manager)
    # # frogsburrow.assign_pc_to_spot(ctenums.CharID.MARLE, script_manager)
    # # protodome.assign_pc_to_spot(ctenums.CharID.CRONO, script_manager)
    # # northcape.assign_pc_to_spot(ctenums.CharID.FROG, script_manager)
    # deathpeak.assign_pc_to_spot(ctenums.CharID.MAGUS, script_manager)
    #
    # script_manager.write_all_scripts_to_ctrom()
    # ow_manager.write_all_overworlds_to_ctrom()
    # locationtypes.write_exit_dict_to_ctrom(ct_rom, exit_dict)
    #
    # basepatch.alter_event_or_operation(ct_rom)
    # basepatch.set_storyline_thresholds(ct_rom)
    # item_db.write_to_ctrom(ct_rom)
    #
    # ct_rom.seek(0x01FFFF)
    # ct_rom.write(b'\x01')
    #
    # ct_rom.seek(0x02E1F0)  # Always active/wait on first name
    # ct_rom.write(b'\xEA\xEA')
    #
    # # Eventually find a better place for location changes to live.
    # # Shard music changes
    # LD = locationtypes.LocationData
    #
    # locs = (ctenums.LocID.GUARDIA_BASEMENT, ctenums.LocID.GUARDIA_REAR_STORAGE)
    # for loc_id in locs:
    #     data = LD.read_from_ctrom(ct_rom, loc_id)
    #     data.music = 0xFF
    #     data.write_to_ctrom(ct_rom, loc_id)
    #
    #
    # with open('./ct-mod.sfc', 'wb') as outfile:
    #     outfile.write(ct_rom.getbuffer())
    pass

if __name__ == '__main__':
    main()

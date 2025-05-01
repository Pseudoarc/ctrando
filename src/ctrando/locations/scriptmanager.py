from ctrando.common import ctrom, ctenums
import copy
from dataclasses import dataclass
from typing import Optional

from ctrando.locations import locationevent
from ctrando.locations.locationevent import LocationEvent


@dataclass
class _ScriptManagerEntry:
    script: locationevent.LocationEvent
    is_modified: bool = True


class ScriptManager:
    """Class which keeps track of locations which need changes."""
    def __init__(
            self,
            ct_rom: ctrom.CTRom,
            script_dict: Optional[dict[ctenums.LocID, LocationEvent]] = None):
        if script_dict is None:
            script_dict = {}

        self._script_dict = {
            loc_id: _ScriptManagerEntry(copy.deepcopy(loc_event), False)
            for loc_id, loc_event in script_dict.items()
        }

        self._ct_rom = ct_rom

    def get_ctrom(self) -> ctrom.CTRom:
        return self._ct_rom

    def set_ctrom(self, ct_rom: ctrom.CTRom):
        self._ct_rom = ct_rom

    def __getitem__(self, key: ctenums.LocID) -> LocationEvent:
        # print(f'Reading {key}')
        if key in self._script_dict:
            self._script_dict[key].is_modified = True
            return self._script_dict[key].script

        script = LocationEvent.from_rom_location(
            self._ct_rom.getbuffer(), key)
        self._script_dict[key] = _ScriptManagerEntry(script, True)
        return script

    def __setitem__(self, key: ctenums.LocID, value: LocationEvent):
        self._script_dict[key] = _ScriptManagerEntry(value, True)

    def __delitem__(self, key: ctenums.LocID):
        del self._script_dict[key]

    def write_script(self, loc_id: ctenums.LocID):
        if loc_id not in self._script_dict:
            raise KeyError

        # print(f'Writing {loc_id}')
        locationevent.write_location_script_to_ctrom(
            self._script_dict[loc_id].script, self._ct_rom, loc_id
        )

    def write_all_scripts_to_ctrom(self):
        for loc_id in self._script_dict:
            self.write_script(loc_id)
# Untitled CT Randomizer (CTRando)
This is an open world randomizer for Chrono Trigger.
This randomizer is heavily influenced by previous open world randomizers for Chrono Trigger, both Jets of Time and Wings of Time before it.
While those randomizers take liberties with the gameplay to provide a tight racing experience, this randomizer’s goal is to preserve as much of the vanilla gameplay experience as possible.
* [Beginner's Guide](https://docs.google.com/document/d/1lrpnDAR66YIaDHZmlTunPH5PR1_WosjCUYu11101Hvs)

## Usage
This package must be installed using `pip` before it can be used.
After creating and activating a virtual environment (https://docs.python.org/3/library/venv.html),
the package can be installed with:
```sh
$ pip install /path/to/ctrando
```

To roll a seed with recommended beginner settings, use:
```sh
$ python3 -m ctrando --input-file path/to/ct.sfc --options-file path/to/samplesettings.toml
```
Note that the seed is included at the top of the settings file, so you'll need to edit that to get fresh seeds.
If the seed is omitted from the settings file, then a random seed will be assigned.

MSU1 support is thanks to DarkShock, qwertymodo, and Cthulhu.  The full license can be found in
`/src/ctrando/postrando/msu1/chrono_msu1.asm`.
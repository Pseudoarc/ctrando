## Patch Notes
* chrono_msu1.asm can be applied directly to a vanilla rom with BASS v14.
  For an ExHiRom rom, supply the `-d EX` to BASS.
* The bundled `ct_msu1.ips` should not be applied to a randomized rom.
* The hack uses freespace `($CDF9D0-$CDFD9A)` and `($CD5D20-$CD5D75)` which are not
  in Geiger's offset list, so it is likely to be be compatible with other hacks.

## Using MSU-1 Packs
An MSU-1 pack is a folder containing the following files:
* A file named `<prefix>.msu`
* Files named `<prefix>-<number>.pcm`

To use the pack, you need to add your rom to this folder with the name `<prefix>.sfc`.
If running the rom with a `.bps` patch, then the patch must also be renamed `<prefix>.bps`
and be placed in the same folder.
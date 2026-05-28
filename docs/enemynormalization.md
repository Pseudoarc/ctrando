# Enemy Normalization
The default RDI experience keeps enemies as vanilla as possible and tries to achieve balance 
through the dynamic scaling algorithm.  
Chrono Trigger is, generally speaking, an easy game. 
With a few notable exceptions, bosses tend to have low damage output and high hp.
The dyanamic scaling algorithm uses an internal level stat to represent what level the enemy
is intended to be fought at.
The difference between this internal level and the current scaling level determine how much
the enemy's stats should be scaled.
Weaker bosses have been made more threatening by reducing their internal level
With the setting `normalize_enemies=true`, the balance
changes enumerated below will be made.

## Summary of Changes

* Yakra gets -25% HP and +25% damage.  The power of his counter attack is doubled.
  * Yakra was a bit spongey and still fairly weak at high scaling.
  * The main mechanic for Yakra is playing around counters, so they need to be significant
* Guardian gets -25% HP.  Bits gets +20% hp and lower chance to skip a turn. Bit respawn countdown begins at 3.
  * The changes are designed to increase the amount of time you're in the interesting phase, 
    where at least one bit is alive and you can choose to strategically eat a counter.
* R Series gets +125% HP and -10% attack.  R Series will skip fewer turns.
  * R Series will have about 5k HP at level 50, so they will live through all but the best AoE.
  * In non-vanilla locations, the R Series script would not correctly identify the front/back row
    distinction, resulting in the robots doing nothing for two turns. Now all robots have a 50% chance
    to act.
* Heckan has -15% HP.
* MasaMune no longer runs up to the target before hitting.
  * MasaMune's movement would bug out on some maps so he would rarely attack.
* Flea and Slash have +50% damage 
* Golem's death burp does +50% damage
* Yakra XIII has -25% HP but begins phase 2 at 2/3 HP.  Needle attacks do +15% damage.
  * The adjustments mean that phase 2 has the same amount of total HP.
* Terra Mutant has +50% magic damage and +100% physical damage
  * The point of the Terra Mutant fight is to outdamage the healing while dealing with status
    and light damage, but the damage was just insignificant
* Atropos has -25% HP and +50% damage
* Gato does not run up to the target he hits and has +25% damage.
  * Gato suffered from the same issue that MasaMune did where his script would bug in some spots.
* Flea Plus and Super Slash have +50% damage.
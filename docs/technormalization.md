# Tech Normalization
The default RDI experience keeps techs as vanilla as possible and tries to achieve balance 
through randomization of tech power.  In this scheme, some techs are dominant and others are
never worthwhile, even at high mp.  With the setting `normalize_techs=true`, the balance
changes enumerated below will be made.

## Summary of Changes
* Level 1 elemental spells cost 4 (vanilla 2)
* Level 2 elemental spells (non-Magus) have a power of 17 (vanilla 14)
* Magus level 2 spells have a power of 20 (vanilla 18)
* Dark Bomb/Mist and Dark Matter have powers of 25 (vanilla 24) and 42 (vanilla 38) respectively.
* Cyclone has power 12 (vanilla 10)
* Slurp Cut has power 14 (vanilla 11)

## Level 1 Elemental Spells
By default, the basic elemental spells have power 11 (Fire, Ice, Water) or 12 (Lightning).
With the current tech scaling, this gives them 57 and 62 power respectively at 20 mp.
For comparison, Flare has 42 power at level 20.  
The basic elemental spells also are components of numerous combo techs which further boost
their power.  The result is that things like Ice Tackle or Fire Sword are dominant even when
their component techs have mediocre mp rolls.
Making them cost 3 mp reduces them to 51 (lightning) and 46 power (rest) at 20 mp.
It makes sense for a 20 mp single target spell to do more damage than a 20 mp aoe spell,
but in the future the level 1 spells may be further nerfed.

## Full Screen Magic
In vanilla Chrono Trigger, the level 2 elemental spells are quite weak.
* Level one spells are typically 2 mp and 11 power.
* Level two spells (non-Magus) are 8 mp and 14 power (basically +25% power, +300% mp cost)

The result is that level 2 spells are borderline useless at low mps and exist primarily to 
provide multipliers to other techs in combo techs (Fire Tackle, Cube Toss).
The hope is that boosting them to 17 power at 8 mp will improve their position.
Unfortunately, this creates a few issues:
* Magus level 2 spells should be stronger than everyone else's (14 vs 18 power)
* Dark Bomb/Mist should be significantly stronger than Magus's level 2 spells (24 power)

This justifies the boost of Magus level 2 spells to 20 power and Dark Bomb/Mist to 25 power.
Dark matter was always underpowered, having a power of 38 at 20 mp (compare Flare with 42),
Dark Mist was always roughly Flare-level at 20 mp, and the boost has made it slightly better,
and so it completely outclasses Dark Matter.  
Moving Dark Matter to 42 power to match Flare mitigates this.
This also helps Dark Matter to not be a complete letdown in element shuffle.
Perhaps it should be made to match Luminaire at 50 power.

## Physical Techs
Slurp Cut and Cyclone have terrible mp efficiency, even at 20 mp.
The boost to Slurp Cut makes it mostly in-line with Leap Slash.
The boost to Cyclone makes it better but still worse than Spincut 
(as it should be since cyclone has small AoE).




# CloneHeroHero
A CloneHero AI

Dev notes

Possible alternative solution (CloneHeroHero):

Watch one single pixel (or a few pixels for robustness) in each column and constantly poll their values. If they
change to the note color (within the range) and then change back, emit the note. Would still need to cut off the
bottom of the fretboard where the note explosions take place, so would need delay for note playing as well. Think
of this solution as a laser counting problem. Create a new branch to experiment with this.

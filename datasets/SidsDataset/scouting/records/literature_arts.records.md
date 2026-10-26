# literature_arts: records (determinacy edition)

24 records in `datasets/SidsDataset/records/literature_arts/{replace,delete}/`, built by
`scratchpad/la/build_abox.py` (0001-0004) and `scratchpad/la/build_tr.py` (0005-0012).
To change them, edit the scripts and rerun them; don't hand-edit the JSON.
Validator: 24 files, 0 errors (with `relations/literature_arts.md` and `.checks.json`). B7 row: 4/4 per box for replace and delete, 2/2 stored and 2/2 derived, 32 determinate, 24 background-beliefs and 8 derived-beliefs queries.

## Records

| Id | Box | Edit (replace; the delete removes the original) | Derived queries (replace) | Logic |
| --- | --- | --- | --- | --- |
| 0001 | ABox stored (very_unlikely) | Romeo and Juliet set in Verona → Florence (`set_in`) | det (region: Tuscany), det (set in Dante's birthplace? yes), bb (city of the tourist house with Juliet's balcony), bb (its region) | dl ×4 |
| 0002 | ABox stored (very_unlikely) | Mona Lisa housed in the Louvre → National Gallery, London (`housed_in`) | det functional (in the Louvre? no), det chain (city: London), bb (museum of Veronese's Wedding Feast at Cana), bb (same museum as the Mona Lisa?) | dl, dl, dl, fol |
| 0003 | ABox derived (very_likely) | Composer of the opera The Magic Flute born in Salzburg → Vienna (`born_in`) | det premise route (name the composer, then the city), det (born where the opera premiered? yes), db (Mozart's birthplace), db (did Mozart compose it?) | dl, fol, dl, dl |
| 0004 | ABox derived (likely) | The Starry Night (1889) on display in the US → the Netherlands (`on_display_in`) | det premise route (name the museum, then the country), det chain (continent: Europe), db (does MoMA hold it?), db (MoMA's country) | dl ×4 |
| 0005 | TBox (very_unlikely) | String quartet: 2 violins, viola, cello → double bass (`scored_for`) | det ×2 (new quartets: cello? / double bass?), bb (Schubert D. 810 cello?), bb (Dvořák Op. 96 cello?); 4 worlds | dl ×4 |
| 0006 | TBox (unlikely) | Ancient Greek epic in dactylic hexameter → iambic pentameter (`has_metre`, new) | det ×2 (invented epics), bb (Iliad's metre), bb (Odyssey in iambic pentameter?); 4 worlds | dl ×4 |
| 0007 | TBox (very_unlikely) | Old English poem in alliterative verse → rhyming couplets (`has_metre`) | det ×2 (invented poems), bb (Beowulf), bb (Dream of the Rood); 4 worlds | dl ×4 |
| 0008 | TBox (very_unlikely) | Ionic capital: volutes → acanthus leaves (`decorated_with`, new) | det ×2 (new buildings), bb (Erechtheion volutes?), bb (Jefferson Memorial ornament); 4 worlds | dl ×4 |
| 0009 | RBox | `precedes_in_series` loses transitivity | LOTR, Harry Potter (yes → no) | dl |
| 0010 | RBox | `collaborated_with` loses symmetry | Gilbert/Sullivan, Rodgers/Hammerstein (yes → no) | dl |
| 0011 | RBox | `adapted_from` ⊑ `sequel_of` added | Wizard of Oz, Clueless/Emma (no → yes) | dl |
| 0012 | RBox | inverse of `written_by`: author_of → illustrated | Austen, Melville (no → yes; the delete asks "is the author of": yes → null) | dl |

RBox new answers balance: direct 2 yes / 2 no, derived 4 yes / 4 no.
Deletes: the same worlds; each indeterminate query has a null world and a kept-answer world.

## Changes from the scouting and review

- **0001:** The "Casa di Giulietta" cue is gone. World w2 and both house queries say "Shakespeare's Romeo and Juliet", which ties the house to the play, not the older legend. The scout's D4 ("is Juliet's House in the same city as the play?") is answered by the house's name alone (R2), so a region query replaces it. Functional D1 is dropped because the new `set_in` relation is `cardinality:many` (Act 5 is in Mantua). Both determinate queries go through the play's city (region; Dante's birthplace). The delete swaps the Dante query for the river (the Adige).
- **0002:** Both theft queries are replaced by Veronese's *The Wedding Feast at Cana*. It is stored by name with the Louvre (1,287 co-occurrences) and relative to the Mona Lisa ("opposite the Mona Lisa": 173 exact hits; the Louvre's own page quotes it). "Today" is removed from the city query. In the delete, the city query is replaced by "same museum as the Winged Victory?", because a stored "Mona Lisa is in Paris" would be a third storage choice there.
- **0003:** The premise-route query now names the composer step explicitly. The functional query is replaced by "born where the opera premiered (Vienna 1791)?", because `born_in` has no functional tag. The delete uses Karajan's birthplace (Salzburg) in its place.
- **0004:** The premise-route query names the museum step explicitly. The near query is Guernica (Spain): the scout's Night Watch equals the new answer (R6). The functional query is replaced by a continent query, because `on_display_in` is many-valued. The Amsterdam confusion is noted (R4).
- **Backups:** both dropped (Sherlock Holmes, Hamlet's author).
- **TBox and RBox:** not scouted; written new. Rules were chosen so that no Chinese term gives the answer away. Rejected for that reason: fresco (湿壁画 "wet wall painting"), centaur (半人马), Cyclops (独眼巨人), villanelle (十九行诗), limerick (五行打油诗). They were also chosen to have no real exceptions. Rejected for that reason: sonnet, haiku, tapestry (the Bayeux Tapestry is embroidered), the Trout Quintet case.

## Worlds dropped (step 3)

- 0001: "Romeo and Juliet set in the Veneto" stored directly. It contradicts "Florence is in Tuscany" after the edit. In the delete it is too rare to be a route.
- 0002: "Mona Lisa is in Paris" shortcut. It contradicts "the National Gallery is in London" (replace). The 1911-theft world is also dropped: it clashes with "Louvre employee Peruggia" and "the Louvre was closed for a week".
- 0003: the "two composers" world. "The opera has a single composer" is firm.
- 0004: "New York City is in the United States" and the museum-to-country rule are firm. The city-level shortcut "Starry Night in New York" contradicts the edit (replace), and a real delete must remove it (delete).
- TBox: membership queries ("Is Beowulf an Old English poem?") are avoided wherever membership is firm. Background-belief queries ask the property of two well-known members instead (4 worlds).

## Remaining doubts

- **0004 w2 (MoMA moves to the Netherlands).** Valid by the letter of the spec, but clearly the minority world. R4: some models may already say "Amsterdam" or "Netherlands".
- **0002 w2 (stored relative to the Mona Lisa).** Lopsided toward w1. The Louvre plans to move the Mona Lisa to its own room. That changes the room, not the museum, so no answer depends on it, but "opposite the Mona Lisa" will date.
- **0003.** There is an R2 tension (w2 changes who "the composer" refers to), as in the README's Elizabeth I example. The premise-route query is still close to the direct one.
- **0008.** By-name storage of the Erechtheion and Jefferson Memorial capitals is weak, so the rule worlds probably dominate.
- **0006 and 0007** are both verse-form rules.
- **TBox evidence.** The bridge evidence for the Dvořák quartet and the Dream of the Rood is thin. The Odyssey and Iliad co-occurrence counts are approximate.
- **0011 delete.** It removes a negative property ("not a subproperty"), following main. A model may reasonably say "no" rather than abstain (R5).
- **Unverified counts.** "Starry Night AND United States" = 0 (Dolma) and 781 (RPJ) come from the review's runs; I cite them only in a note. "Starry Night AND the United States" (3,641) I re-ran and read the samples.
- **Locality far prompts** were picked to be unusual (B6), but they are not cross-checked against other topics.

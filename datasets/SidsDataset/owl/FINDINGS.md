# Findings from the formal check (OWL + HermiT)

## Resolution (2026-10-31)

**What was fixed.**

- Stage 1 (RELATIONS.md, merged as c7a4ca6): everything in section B, the
  inverse-pair fix behind A3, the missing chain behind A4, and the checker
  bug in D (`reason.py` now accepts classes HermiT found equivalent).
- Stage 2 (records and encodings, one pass per topic, then a verification):
  - A1: every "is X the only one?" question in an insert is now determinate
    "no" (19 records plus biology-insert-0009, grammar-insert-0005/0009/0010,
    history-insert-0003/0004). Where no indeterminate question was left,
    the worlds were removed.
  - A2: the finance counts and grammar-insert-0002 q1 are now `fol`;
    mathematics-replace/delete-0015 q0 was retagged `dl` and is checked.
  - A5, C1 to C5: the side facts and one-value presuppositions are stated in
    the records as bridges with checks, chain steps or world `assumes`; the
    encodings' firm one-value rules now match those stated facts, mostly per
    named individual instead of general `Func(...)`.
  - E: worlds that wrote the determinate answer into `adds` now name only the
    premise that gives way (with placeholders), so the answer is derived.
  - Deletes were mirrored by hand (`build_delete.py` is disabled: it would
    wipe every delete record).
- Verification fixes: finance-delete-0003 q1 got the "Burbank is in
  California" bridge its replace got; geography-replace-0015 q1 and 0016 q1
  now state "Provence-Alpes-Côte d'Azur is in France" and "The capital of
  Missouri is Jefferson City"; history-replace-0013's "a small island or a
  town lies on only one continent" (false for Istanbul or Orenburg) became
  "Elba and its town Portoferraio each lie on only one continent";
  people-insert-0002 q3 now states in the prompt that the Ostravel cylinder
  is not the 1889 recording (that recording is itself on wax cylinders);
  biology-replace-0003's one-class check now asks about the vectors.

**Current totals** (full run, job 566500, plus re-runs of the records fixed
afterwards). Cells are pass / fail / not_checked.

| topic | derived_edit | pre | post_determinate | post_worlds | differ | consistent | missing_worlds | not_checked |
|---|---|---|---|---|---|---|---|---|
| biology | 8/0/0 | 136/0/61 | 141/0/0 | 56/0/0 | 56/0/0 | 60/0/0 | 60/0/0 | 0/0/7 |
| finance | 8/0/0 | 124/0/55 | 129/0/0 | 50/0/0 | 50/0/0 | 60/0/0 | 60/0/0 | 0/0/25 |
| geography | 8/0/0 | 129/0/58 | 131/0/0 | 56/0/0 | 56/0/0 | 60/0/0 | 60/0/0 | 0/0/17 |
| grammar | 8/0/0 | 106/0/52 | 130/0/0 | 28/0/0 | 28/0/0 | 60/0/0 | 60/0/0 | 0/0/46 |
| history | 8/0/0 | 123/0/47 | 120/0/0 | 50/0/0 | 50/0/0 | 60/0/0 | 60/0/0 | 0/0/34 |
| literature_arts | 8/0/0 | 125/0/60 | 135/0/0 | 50/0/0 | 50/0/0 | 60/0/0 | 60/0/0 | 0/0/19 |
| mathematics | 8/0/0 | 86/0/43 | 120/0/0 | 9/0/0 | 9/0/0 | 60/0/0 | 60/0/0 | 0/0/75 |
| people | 8/0/0 | 134/0/60 | 140/0/0 | 54/0/0 | 54/0/0 | 60/0/0 | 60/0/0 | 0/0/10 |
| physics | 8/0/0 | 128/0/50 | 126/0/0 | 52/0/0 | 52/0/0 | 60/0/0 | 60/0/0 | 0/0/26 |
| technology | 8/0/0 | 129/0/53 | 128/0/0 | 54/0/0 | 54/0/0 | 60/0/0 | 60/0/0 | 0/0/22 |
| **all** | 80/0/0 | 1220/0/539 | 1300/0/0 | 459/0/0 | 459/0/0 | 600/0/0 | 600/0/0 | 0/0/281 |

**Remaining failures:** none (the 36 failing checks below are all gone).
`validate.py` 0 errors, `encode_check.py` 0 problems. `post_worlds` and
`differ` dropped from 478 to 459 because the A1 questions are no longer
indeterminate. `criteria.py` Rule 11 now fails for 25 inserts (1 or 0
indeterminate queries instead of 2), a direct result of the A1 fix.

**Open decisions.**

1. Rule 11 for the A1 inserts: relax it to allow 1 (or 0) indeterminate
   queries, or write new indeterminate questions (25 inserts).
2. Count and superlative questions in inserts (`fol`, not checked) whose w1
   keeps the old figure next to a newly found or newly formed item:
   geography-insert-0003/0004, history-insert-0001/0002/0009/0010,
   finance-insert-0001/0002/0003/0004/0009, physics-insert-0001/0002/0004/
   0009/0010, and the count questions next to every A1 fix. Make them
   determinate, drop them, or keep them as "count stored as a number".
3. Delete bridges: some topics copied a replace record's presupposition
   bridges onto identical delete questions (people 0004/0005/0007/0019/0020,
   finance 0008/0013, technology 0013), others left them off because no
   delete answer needs them (geography, history and physics TBox deletes).
   Pick one convention.
4. Still unstated firm facts: technology-replace-0005 (one path separator),
   0008 (one line ending); grammar TBox replaces 0005 to 0008, 0019, 0020 (a
   default with an exception, not expressible). Done (2026-10-31):
   technology-replace-0003/0004 now name in their worlds only the premise
   that gives way and its side facts (placeholders in `adds`, so
   Massachusetts and Vermont are derived), and state "Unix / the BASIC
   programming language was originally developed in only one US state" as a
   bridge with a check; the unused firm "one state per place" rule is gone.
5. Wording to review: done (2026-10-31). geography-replace/delete-0005 now
   edit to "an unglaciated river valley" (the ria definition) and ask "Was
   its valley ever filled by a glacier?", whose answers exclude each other,
   with the definitional bridge "An unglaciated valley was never filled by a
   glacier"; biology-replace-0003 (and 0004, the same pattern with Lyme
   disease) say "arthropods", not "animals", in the one-class bridge and the
   questions, so rodents, deer and mice no longer count.
6. Shared docs: README "Shape per topic" for mathematics still says no
   premise can give way; RELATIONS.md's `parent_headquartered_in` reading
   still says `subsidiary_of` (encodings use `direct_subsidiary_of`).
7. Optional retags not done: finance-delete-0002 q3,
   literature_arts-delete-0013 q3, physics-replace/delete-0008 q2 and q3,
   grammar-replace-0019 q2 and q3.

The rest of this file is the original report of 2026-10-30.

---

For the dataset author. This file collects what the formal check found over all
600 records, merged across the ten topics, plus a verification of the formal
encodings themselves. No record was changed. Check of 2026-10-30.

Words used below:

- **World**: one of a record's `worlds` (a way the model could have stored its
  beliefs before the edit).
- **Encoding**: the formal file `owl/formal/<id>.json` that turns a record into
  logic. `reason.py` (the checker) runs HermiT on it.
- **Firm fact**: a background fact the encoding treats as never giving way.
- **Closed claim**: "X is the only one" or "these N are all of them".

The checks: `derived_edit` (the premises give the original fact), `pre` (the
original answer follows before the edit), `post_determinate` and `post_worlds`
(the new answer follows after it, in every world or in its own world),
`differ` (the worlds really give different answers), `consistent` (each world
holds together), `missing_worlds` (no way of repairing the beliefs is missing
from the worlds), `not_checked` (queries the logic cannot express).

## Counts

Every record has exactly one encoding, and `encode_check.py` finds no
problems in any of the 600. The full run (`reason.py --jobs 2`, 600 records,
4067 HermiT calls, 24 minutes) gave exactly the results the topic agents had
reported. After it, four biology encodings were corrected (see E) and re-run;
the counts below include them.

Cells are pass / fail / not_checked.

| topic | derived_edit | pre | post_determinate | post_worlds | differ | consistent | missing_worlds | not_checked |
|---|---|---|---|---|---|---|---|---|
| biology | 8/0/0 | 136/0/61 | 132/4/0 | 61/0/0 | 57/4/0 | 60/0/0 | 60/0/0 | 0/0/7 |
| finance | 8/0/0 | 124/0/55 | 129/0/0 | 50/0/0 | 50/0/0 | 60/0/0 | 60/0/0 | 0/0/25 |
| geography | 8/0/0 | 129/0/58 | 126/5/0 | 56/0/0 | 56/0/0 | 60/0/0 | 60/0/0 | 0/0/17 |
| grammar | 8/0/0 | 106/0/52 | 130/0/0 | 28/0/0 | 28/0/0 | 60/0/0 | 60/0/0 | 0/0/46 |
| history | 8/0/0 | 123/0/47 | 120/0/0 | 50/0/0 | 50/0/0 | 60/0/0 | 60/0/0 | 0/0/34 |
| literature_arts | 8/0/0 | 125/0/60 | 129/0/0 | 56/0/0 | 50/6/0 | 60/0/0 | 60/0/0 | 0/0/19 |
| mathematics | 8/0/0 | 84/0/43 | 118/0/0 | 9/0/0 | 9/0/0 | 60/0/0 | 60/0/0 | 0/0/77 |
| people | 8/0/0 | 134/0/60 | 130/4/0 | 58/2/0 | 54/6/0 | 59/1/0 | 60/0/0 | 0/0/10 |
| physics | 8/0/0 | 128/0/50 | 125/0/0 | 53/0/0 | 52/1/0 | 60/0/0 | 60/0/0 | 0/0/26 |
| technology | 8/0/0 | 129/0/53 | 125/0/0 | 57/0/0 | 54/3/0 | 60/0/0 | 60/0/0 | 0/0/22 |
| **all** | 80/0/0 | 1218/0/539 | 1264/13/0 | 478/2/0 | 460/20/0 | 599/1/0 | 600/0/0 | 0/0/283 |

All 539 `pre` not_checked are insert queries, which have no original answer.
The 36 failing checks come from 24 records and three causes (A1, A3, A4).

## A. Records with real problems

### A1. Inserts whose world w1 keeps a closed claim that the insert contradicts (19 records)

In these inserts, w1 stores "X is the only one" as a closed fact and keeps it,
while the edit adds a new member that the record itself calls different from
X. No consistent set of beliefs holds both. So w1's "yes" to the "is X the
only one?" question is a stale patch, not a world. The checker cannot check a
world like that (it is marked `exception`), so only w2 is left and `differ`
fails. The count question next to it ("how many?", tagged `fol`) has the
same problem but is not checked.

| Record | Query | The closed claim vs. the new member |
| --- | --- | --- |
| people-insert-0001 | q3 | Shakespeare's signatures all on the four documents vs. the Sellowmere deed |
| people-insert-0002 | q3 | the 1889 Edison cylinder as the only Bismarck recording vs. the Ostravel cylinder |
| people-insert-0003 | q3 | the Naples harp as Stradivari's only harp vs. the Corvellani harp |
| people-insert-0004 | q3 | the two Florence telescopes as Galileo's only ones vs. the Vescarri telescope |
| people-insert-0009 | q0, q1, q3; consistent | "the Beheading is the only painting Caravaggio signed" vs. any Vennastre altarpiece a prompt names. Here w1 is not marked `exception`, so even the determinate q0 and q1 fail in w1 (the knowledge base is inconsistent) |
| people-insert-0010 | q0, q1, q3 | Vermeer's closed list of two townscapes vs. "The Tanners' Lane" (same as 0009) |
| literature_arts-insert-0001 | q3 | the Nowell Codex as the only Beowulf manuscript vs. the Ostrevane Codex |
| literature_arts-insert-0002 | q3 | Wuthering Heights as the only novel vs. Ashcombe Fell |
| literature_arts-insert-0003 | q3 | the Pietà as the only signed work vs. the signed relief |
| literature_arts-insert-0009 | q2, q3 | every surviving tragedy by the three tragedians vs. the Ilvessan plays |
| literature_arts-insert-0010 | q2 | the Ode to Aphrodite as the only complete poem vs. the skiramenes |
| physics-insert-0003 | q3 | Dysnomia as the only moon of Eris vs. Kalemnia |
| technology-insert-0001 | q2 | Plankalkül as Zuse's only language vs. Corvanth |
| technology-insert-0003 | q2 | the Analytical Engine as Babbage's only general-purpose computer vs. the Calbridon Engine |
| technology-insert-0004 | q2 | Turochamp as Turing's only chess program vs. Kelvarne |
| biology-insert-0002 | q3 | the five kiwi species vs. Apteryx tenebris |
| biology-insert-0003 | q2 | the tuatara as the only living rhynchocephalian vs. Sphenodon kerewai |
| biology-insert-0004 | q3 | the three orangutan species vs. Pongo sinarensis |
| biology-insert-0010 | q2 | Latimeria as the only living coelacanth genus vs. the morrenids |

Close relatives that pass but rest on the same idea: biology-insert-0009
(w1 stays consistent only because the edit names no velkarid, so the
velkarids could be African lungfishes), and every insert whose only/count
questions are tagged `fol` (history, geography, finance, physics, grammar).
Their w1 answers ("49 copies", "one site") are just as stale, but nothing
checks them.

Suggested fix, per record, one of:

1. Make the "only" question determinate with new answer "no". A model that
   answers "yes" holds the edit only as a patch, which is exactly what the
   test should catch. Keep the count question as fol, with one new answer.
2. Or keep two worlds but make w1 coherent: the new item might be one of the
   listed ones. This only works where the record leaves that open, and none
   of these do (each edit says "newly described", "newly found", or the w2
   chain says "a different one").
3. Or drop the only/count questions from these inserts.

### A2. Questions tagged `dl` that need counting or a closed world (7 queries, not failing)

These are left `not_checked`. Change their `logic` to `fol` (with
`theory: arithmetic`), as geography-insert-0001 already does.

- finance-insert-0001 q2 (how many), q3 (more than five)
- finance-insert-0002 q2 (how many)
- finance-insert-0009 q2 (more than three)
- finance-insert-0010 q2 ("only one known"), q3 (how many)
- grammar-insert-0002 q1 ("is 'glendrink' a word of a Celtic language?", gold
  "no"). The "no" needs Scots to be the word's only language, which nothing
  states. Either tag it `fol`, or state in the prompt that the word belongs
  to Scots only.

The opposite also happens: some queries tagged `fol` can be said in DL and
could be checked if retagged `dl`: finance-delete-0002 q3 and
literature_arts-delete-0013 q3 ("in the same city as ...?"),
mathematics-replace-0015 q0, physics-replace/delete-0008 q2 and q3 (yes/no),
grammar-replace-0019 q2 and q3. Optional.

### A3. Removing transitivity from one side of an inverse pair (4 records, 8 failing checks)

| Record | Query | Why |
| --- | --- | --- |
| geography-replace-0011, geography-delete-0011 | q0, q1 | the edit removes "located in is transitive", but `contains` (its inverse) is still tagged transitive |
| biology-replace-0009, biology-delete-0009 | q0, q1 | the same with `part_of` and `has_part` |

A relation is transitive exactly when its inverse is. So "located in is not
transitive" also means "contains is not transitive", and the record is
right. The fault is that RELATIONS.md states the same property twice, on both
rows, and the checker removes only the one the edit names (fix in B1).
mathematics-replace/delete-0009 (`divides`/`multiple_of`, transitive) and
0010 (asymmetric) have the same shape. Their encodings remove the inverse's
property too, as a stated side fact, so they pass. Once B1 is fixed, all
six records behave the same way.

### A4. A chain the record uses that the catalogue lacks (1 record)

- geography-insert-0005 q2: the chain says "what drains into a river lies in
  every drainage basin that river lies in" (drains_into, then
  in_drainage_basin_of). RELATIONS.md has only the other order (a place in a
  river's basin is in the basin of what the river drains into). Both are true
  geography. Add the missing one (B2).

### A5. Smaller record points (no failing check)

- finance-delete-0002: w1's summary and q1's `determinacy_why` say the towers'
  role as headquarters goes with the delete. No world lists it in `assumes`,
  so it is not encoded, and the delete's repair search tests nothing there.
  Suggest adding "the towers are the headquarters building" to w1's
  `assumes` as what gives way.
- mathematics-replace/delete-0003 and 0004: the notes say "no premise can give
  way", but the premise-route answers only work if the arithmetic premise
  (the factorization) gives way, as the notes of 0015 and 0016 say. README's
  "Shape per topic" for mathematics agrees with 0003/0004. One of the two
  wordings should change.
- literature_arts-replace-0001 q1: the "no" before the edit needs Romeo and
  Juliet to be set in one city, while the record's own notes say `set_in` is
  many-valued (Act 5 is partly in Mantua) and drop the functional query for
  that reason.

## B. RELATIONS.md fixes (merged across topics, deduplicated)

### B1. A property stated on both rows of an inverse pair

`located_in`/`contains`, `part_of`/`has_part` and `divides`/`multiple_of` tag
both rows `transitive` and `asymmetric`. That is true, but an RBox edit that
removes the property from one row can't remove it (A3). Change: keep
`transitive` and `asymmetric` on one row of each pair only (the row the
records edit: `located_in`, `part_of`, `divides`), and have `relations.py`
apply properties through `inverse:`. Or have `reason.py` also remove an RBox
edit's property from the inverse. Check `less_than`/`greater_than` and
`subclass_of`/`superclass_of` the same way before any record edits them.

### B2. Missing chains and subproperties

| Change | Needed by |
| --- | --- |
| add the chain "drains_into, then in_drainage_basin_of, gives in_drainage_basin_of" (the current `chain:drains_into->in_drainage_basin_of` is the other order; the tag syntax may need a form for a chain that starts with another relation) | geography-insert-0005 q2 |
| `parent_of` gets `subproperty:ancestor_of` (so `father_of` and `has_father` reach `ancestor_of`/`descendant_of`) | people-replace-0015 needed local rules |
| `isotope_of` gets `subproperty:has_same_atomic_number_as`, or merge the two (same reading) | physics-replace/delete-0011 treat it as true |
| `sequel_of` gets `subproperty:follows_in_series` | literature_arts-replace/delete-0011 treat it as true |
| `divides` gets `subproperty:less_than`, `multiple_of` gets `subproperty:greater_than` (a ≠ b) | mathematics-replace/delete-0012 treat it as true |
| a link from `attests_word` to `word_of_language` ("Gothic attests the word skip" means skip is a Gothic word; an inverse plus a subproperty, so it needs a new inverse row such as `attested_in` with `subproperty:word_of_language`) | grammar-insert-0003, 0004 |
| a link from `died_in_hemisphere` to `died_in`/`located_in` | history |
| a direct-parent relation: `subsidiary_of` is "direct or indirect" (transitive), so "the parent company" can return a grandparent. Add `direct_subsidiary_of` (functional, subproperty of `subsidiary_of`) | finance |
| `orbits_planet_of_type`, `parent_headquartered_in`, `official_currency_in` are compositions in their reading but can't be chains because they are functional. Keep them, and say in the reading that records encode them as rules | physics, finance |

### B3. One value per subject, assumed by questions but not tagged

Questions such as "which X?" and "A or B?" take for granted that there is one
answer. The encoders added a firm rule in each record. For each relation,
either tag it `functional` (where that is true), or leave it many-valued and
accept the per-record presupposition (C3).

- `styled_as` (no tags at all): one title before a name (people-replace-0020)
- `educated_in`, `confers` (many): "the one English university", "the one house", "the one style" (people)
- `buried_in`: one country of burial (people-replace-0004)
- `created_by` (`cardinality:many`): one creator of Linux, one inventor of the Web (technology 0001, 0002)
- `wholly_owned_subsidiary_of`: one owner (finance-replace-0013)
- `discovered_by`: one discoverer of the electron, of X-rays (physics-replace-0002)
- `transmitted_by_class`: one carrier class per disease, insect vs. arachnid (biology 0003, 0004)
- `derivative_of`: the Debian, Fedora/RHEL and Arch families exclude each other (technology 0014 to 0016)
- `listed_on` (many): a company on one of the two exchanges (finance-replace-0008)
- `set_in` (many): one city of setting (literature_arts-replace-0001)
- `word_of_language` (many): grammar-insert-0002
- fusion process per star, shear response per fluid (physics 0005, 0020): local relations, same presupposition

### B4. Inverse tags that are wrong or one-sided

- `succeeded` has `inverse:preceded_by`, but "Truman succeeded Roosevelt" and
  "Truman was preceded by Roosevelt" say the same thing in the same
  direction. Change it to `inverse:preceded` (a preceded b) and give
  `preceded` a row. history-replace/delete-0012 use a local `preceded`.
- `caused_by` is tagged as the inverse of `caused`, `causes` and
  `causes_disease`. OWL then treats those three as one relation. Change: one
  inverse per relation (`caused_by` for `caused`, new names for the others),
  or make `causes_disease` a subproperty of `causes` and drop its own inverse.
- Inverse listed on one row only: `causes` and `causes_disease` (to
  `caused_by`), `founded` (to `founded_by`), `has_species` (to `in_genus`),
  `head_of` (to `has_head`), `superclass_of` (to `subclass_of`). Add the
  matching tag on the other row.
- Asymmetric on one row only (the inverse of an asymmetric relation is
  asymmetric too): `brood_form_of`, `founded`, `invented`,
  `is_keel_bound_to`, `orbits`, `paternal_grandfather_of`, `proved`,
  `tide_sealed_to` (which is also transitive on one row only). Add the tag to
  the inverse row.

### B5. Tags that contradict each other or the records

- `painted_in` is `functional` and also chains into itself through
  `located_in`: painted in Delft, and Delft in the Netherlands, gives painted
  in the Netherlands; with one value allowed, Delft becomes the same place as
  the Netherlands. Change: drop `functional`, or split it into
  `painted_in_city` (functional) and `painted_in` (chained).
- Fictional relations that already carry the property their RBox insert
  adds, so the catalogue describes the state after the insert:
  `kiln_sworn_to` (history-insert-0015), `slate_tethered_to`
  (finance-insert-0017), `loom_tied_to` (grammar-insert-0017),
  `folio_sworn_to` (literature_arts-insert-0017), `pellith_tethered_to`
  (physics-insert-0016), the tags physics-insert-0007/0008 add,
  `vossel_tied_to` (transitive), `marrow_paired_with` (symmetric),
  `varrish_bound_to` (chain), `has_brask_partner` (functional),
  `fennopes`/`quorlish_to` (inverse), `glimvers` under `ostrels` (biology),
  and geography-insert-0006's relation. Change: remove these tags. Nothing
  fails today only because inserts have no "before" check.

### B6. Relations named only inside another row's tag

55 relations exist only as a name in some other row's tag (full list in
`owl/relations_report.md`). Records use at least `acquired_by`,
`descendant_of`, `follows_in_series`, `instrument_in`, `parent_company_of`
and `preceded_by`. Change: give each a row with its reading and tags.

### B7. Readings that don't fit how records use them

- `founded_by` reads "company a was founded by person b"; history uses it for
  missions founded by an order.
- `built_from` reads "landform ..."; history uses it for obelisks and
  ziggurats.
- `written_in_language` reads "originally written in"; grammar needs it for
  the Codex Argenteus, a translation (encoded with a local
  `manuscript_language`).
- mathematics-replace-0006 is tagged `equals` for "x to the power 0 equals 1"
  and 0007 `subclass_of` for a parity rule; `has_diagonals` is many-valued
  but the question is "equal or unequal?".
- Rows that appear more than once (with the same tags): `part_of`,
  `instance_of`, `located_in`, `born_in`, `subclass_of`, `raises`, `lowers`,
  `caused`, `causes`, `has_outcome` and a few more. Harmless, but one row
  each is easier to maintain.

### B8. Relations records need that the catalogue lacks

The encoders declared 153 record-local relations. Some are only encoding
helpers (spelling links such as `prefixed_out`, kinds of forms), but many are
ordinary relations a question asks about. The ones most worth adding:

- people: `crowned_in`, `lives_under`, `has_profession`, `nicknamed`,
  `latin_name`, `court_musician_to`, `first_chancellor_of`,
  `discovered_moons_of`, `home_harbour`, `built`
- history: `erupted_in`, `shot_at`, `killed_at`, `killed_in_war`,
  `won_battle`, `king_of`, `governor_of`, `marshal_of`, `ruled_from`,
  `sealed_by`, `printed_in`, `sculpted_from`, `written_on`,
  `written_in_script`, `preceded`
- finance: `central_bank_of`, `issues_currency`, `primary_listing`,
  `home_exchange`, `founded_in`, `dissolved_in`, `built_by`, `made_by`,
  `struck_at`, `face_value`
- geography: `has_climate`, `uses_currency`, `has_calling_code`, `on_lake`,
  `flows_out_of`, `autonomous_region_of`, `second_largest_city_of`,
  `whs_inscribed_in`, `on_border_of`
- biology: `in_family`, `protects`, `feeds_mainly_on`, `arises_in`,
  `produced_mainly_in`
- physics: `landed_on`, `discovered_at`, `proposed_by`, `predicted`,
  `worked_in`, `has_largest_moon`, `has_largest_planet`, `mostly_made_of`,
  `in_periodic_group`, `can_annihilate_with`
- mathematics: `formulated`, `credited_with`, `has_parity`,
  `prime_factorization_is`, `has_side_count`, `has_interior_angle`
- grammar: `means_in_english`, `ends_in`, `def_article`,
  `indef_adj_pattern`
- literature_arts: `narrated_by`, `painted_ceiling_of`
- technology: `developed_at`, `developed_by`, `runs_on`, `runs_over`,
  `uses_package_manager`, `released_under`, `founded_at`

## C. Softer findings: side facts the records don't state

None of these changes an answer. Each is something a question or a world
takes for granted. The encoders added them (as firm facts, or as a side fact
every world gives up) and said so in each file's `notes`. The records would
be clearer if they stated them in a bridge, a chain step, or the worlds'
`assumes`.

### C1. Side facts the edit forces in every world, but no world lists

| Record | Side fact |
| --- | --- |
| geography-replace-0013 | Ciudad Juárez leaves Mexico (it is now a US state capital, and a city is in one country) |
| people-replace-0001 | Langevin's real marriage gives way |
| finance-replace-0014 | Siemens is not on Euronext Paris and in no French index (only in the notes) |
| physics-replace-0014 | Aldebaran is in the northern sky (only in the notes) |
| biology-replace-0013 | "dolphins have bony skeletons" gives way (only in q1's `determinacy_why`); "no shark nurses its young" gives way in w1 and w3 (only in the notes) |
| history-delete-0013 | "Elba is in Tuscany" goes in both worlds (listed only under w1) |
| mathematics TBox replace 0006, 0007, 0019, 0020 | the well-known member's stored value (10 to the power 0 is 1, 7 is odd, ...) gives way; these records have no worlds |
| mathematics-replace/delete-0003, 0004, 0015, 0016 | the arithmetic premise (the factorization, 20² + 21² = 29²) gives way (see A5) |
| grammar TBox delete 0005 to 0008, 0019, 0020 | the link from the member to the wider class gives way in every world |

### C2. "No" answers before the edit that need an unstated negative fact

- people-replace-0003, 0015, 0016: a person is this man's grandchild only
  through the father's side (local rules).
- biology-replace-0001: the pancreas is in the abdomen, one region per organ
  (stated only in the delete mirror); 0002: vitamin C is not made by the
  skin; 0014: the brain is part of the central nervous system (only in the
  delete mirror).
- history-replace-0002: Washington, D.C. is not in Maryland; 0014: no
  Revolutionary War battle fell in Madison's presidency; 0016: England is
  not in continental Europe (only in the notes).
- physics-replace-0002: Thomson worked in the UK; 0003, 0004: terrestrial
  planets are not mostly hydrogen and helium, gas giants have no solid
  surface (stated only as world side facts); 0015, 0016: the nebula's and
  the galaxy's hemisphere.
- finance-replace-0013: BMW is outside the Volkswagen group, and a wholly
  owned subsidiary's parents are its owner and its owner's parents.
- literature_arts-replace-0001: Dante was born only in Florence; 0013:
  Tuscany is in central Italy, one part of Italy per place (only in the
  notes); 0014: a novel is not in verse and not a narrative poem.
- mathematics-replace-0001: Euclid did not formulate the law of buoyancy;
  0016: 23 is prime, and a number is a multiple of a prime only if the prime
  is one of its prime factors.
- technology-replace/delete-0014: Arch Linux uses pacman.
- geography-replace-0001: Canberra is in the ACT; embassies are accredited
  to the capital.

### C3. One value or one place, presupposed by a definite question

grammar-insert-0003 ("the language in which 'farjoskip' is attested": one
language), people-insert-0006 (one vellum partner), people-insert-0014 (the
beacon count), technology-replace/delete-0013 (HTTP/1.1 runs over one
transport protocol), literature_arts-replace-0003 (born in one city), 0004
(on display in one country), 0020 (one closing section), history-replace-0013
(one country and one continent per place), history-replace-0016 (a charter is
sealed in one country), history-replace-0006 (gravity or pumps), people
0005, 0014, 0020 (one English university, one rule, one title), and the
relations in B3.

### C4. Facts found in notes, a `determinacy_why` or a mirror record, not in the chains

- finance-replace-0015, 0016: "Switzerland is outside the EU", "Washington
  is in the West region" (from `determinacy_why`).
- history-replace-0001: "Vesuvius is in Campania" (a bridge only in the
  delete mirror).
- literature_arts-replace-0014: "a novel does not open with an invocation to
  a muse" (a bridge only in delete-0014).
- grammar-replace/delete-0013: "omnibus comes from omnis" (not in the bridge
  list); 0014 to 0016: the rules for the old gender (only the new gender's
  are bridges).
- biology-replace-0013: "the Act protects every marine mammal" read as "only
  marine mammals" (w2 and w3 need the "only").

### C5. Readings the encoders had to choose

- history-replace/delete-0004: the premises are dates; encoded as "Roosevelt
  was president on December 17, 1903" (one date individual).
- history-replace/delete-0006: the record says the Pont du Gard is "part of"
  a Roman aqueduct, but its worlds treat it as a member of the class.
- finance-replace-0019: "Atlanta, in the United States" is reduced to the
  country, since the edit is about the country.
- biology-replace-0004 q3: "deer ticks" read as the premise's ticks.
- grammar TBox replace 0005 to 0008, 0019, 0020: "the edited rule overrides
  a wider rule for its class" is a default with an exception, which this
  logic cannot say; left out of the replace files.
- grammar-insert-0014: a Tovrish verb meaning a motion is a verb of motion.

## D. Coverage

Derived queries (4 per record, 2 for RBox):

| topic | derived queries | checked | not_checked (fol) | not_checked (tagged dl) | exception |
| --- | --- | --- | --- | --- | --- |
| biology | 204 | 197 | 7 | 0 | 0 |
| finance | 204 | 179 | 19 | 6 | 0 |
| geography | 204 | 187 | 17 | 0 | 0 |
| grammar | 204 | 158 | 45 | 1 | 0 |
| history | 204 | 170 | 34 | 0 | 0 |
| literature_arts | 204 | 185 | 19 | 0 | 0 |
| mathematics | 204 | 127 | 77 | 0 | 0 |
| people | 204 | 194 | 10 | 0 | 0 |
| physics | 204 | 178 | 26 | 0 | 0 |
| technology | 204 | 182 | 21 | 1 | 0 |
| **all** | 2040 | 1757 (86%) | 275 | 8 | 0 |

- The fol queries are arithmetic (counts, sums, mass and number arithmetic;
  76 in mathematics alone), temporal (dates, years, before and after) and
  value comparisons ("same city as", "colder than", "more than N").
  mathematics-insert-0011 has no checked query at all.
- The 8 dl-tagged queries left unchecked are the 7 in A2 plus
  technology-replace-0005 q1, whose two gold paths (`docs/notes.txt`,
  `docs\notes.txt`) differ only in punctuation, which answer matching
  ignores.
- No query is an `exception`. 17 worlds are (A1: w1 of 15 people,
  literature_arts, physics and technology inserts, plus 4 biology inserts).
  A query is checked only in the worlds that are not exceptions.

What the checker can't do:

- **No numbers, dates, counts or comparisons.** These are the fol queries.
- **Open world.** A "no" needs something that rules the claim out (one value
  only, disjoint classes, a rule). That is why so many firm "one value"
  facts appear (B3, C3).
- **Rules see only named things.** Several encodings name extra individuals
  so a rule can fire.
- **Inserts have no "before" check,** so a catalogue that already holds the
  inserted property (B5) goes unnoticed.
- **`missing_worlds` searches repairs of up to 3 background beliefs,** and
  only among beliefs the encoding lists. A side fact left out of the encoding
  can't show up as a missing world.
- **A world's `adds` can state a determinate answer.** The README allows this
  (`adds` is what the world says replaces the lost belief, as in its Space
  Needle example), but then `post_determinate` in that world proves little.
  See E.
- **A checker bug: an entailed class membership is sometimes reported as not
  entailed.** It happens when the query's class is the left side of a
  background class axiom and the membership is derived (for example
  `located_in(a, g)`, `located_in value g ⊑ located_in value h`,
  `located_in value h ⊑ Ape`: "a is located in h" comes back as not
  entailed). owlready2's list of an individual's classes misses classes that
  HermiT found equivalent. Three encoders worked around it by writing rules
  instead. To see whether it hides anything now, I re-ran all 600 records
  with a patched membership test (it also accepts a class HermiT found
  equivalent; outside the repo). Every check came out the same, so the
  current results are not affected. The fix belongs in `reason.py`'s
  `run_kb`: count a probe as entailed if the individual is in the probe
  class or in any class equivalent to it.

## E. Verification of the encodings

**What I did.**

1. Checked completeness: 600 records, 600 encodings, none extra or missing;
   `encode_check.py` clean. Re-ran every record from scratch. The results
   matched the topic agents' runs exactly.
2. Re-derived every reported failure by hand. All are real: A1 (each record
   calls the new member different, so w1 can't be consistent), A3 (removing
   transitivity from a relation while its inverse keeps it changes nothing,
   in logic as well as in the checker), A4 (both chain directions are true;
   the catalogue has only one).
3. Read 56 records in full against their encodings, 5 or 6 per topic: a
   replace with worlds, a derived replace, a delete, an insert, and a TBox or
   RBox record each time. geography-replace-0001, 0011, 0013, 0015, 0019,
   delete-0013, insert-0002, 0005; people-replace-0002, 0003, 0004,
   delete-0014, insert-0011; history-replace-0006, 0013, 0016, delete-0013,
   insert-0002; finance-replace-0005, 0013, 0015, delete-0002, insert-0003;
   biology-replace-0004, 0007, 0013, delete-0001, insert-0002, 0003, 0004,
   0009, 0010, 0016; physics-replace-0002, 0006, 0016, delete-0014,
   insert-0003; mathematics-replace-0001, 0006, 0009, 0010, 0015,
   delete-0005, insert-0002; grammar-replace-0002, 0003, 0019, delete-0014,
   insert-0003; literature_arts-replace-0001, 0004, 0011, 0020, delete-0013,
   insert-0009; technology-replace-0007, 0014, 0015, delete-0001,
   insert-0001, 0010. For each world and checked query I worked out what
   should follow and compared it with the record's answer.
4. Checked every `not_checked` and `exception` against the record's `logic`
   tag (D), and compared how the topics handled every insert with worlds.
5. Re-ran the whole dataset with the checker bug patched (D, last point).

**What I found and fixed.**

- biology-insert-0002, 0003, 0004, 0010: the encoder had left the new
  species or genus out of `distinct`, so in w1 it could be the same thing as
  a listed one (Apteryx tenebris "is" one of the five kiwis). That kept w1
  consistent and made `differ` pass, but it contradicts the edit ("newly
  described species") and the record's own w2 chain ("it is none of the
  named ones"). The other topics treat the same pattern as an exception. I
  removed the `distinct` lists (now everything is distinct), marked w1 an
  `exception`, and noted the change in each file's `notes`. Re-run: `differ`
  now fails for these four, like the rest of A1; every other check still
  passes.

**Concerns that remain (no change made).**

- **Answers placed in a world's `adds`.** In several derived-belief worlds
  the replacement fact in `adds` is the very thing a determinate query asks,
  so that query passes in that world without the record's chain being used.
  Examples: geography-replace-0015 (w1, w2), people-replace-0003 and 0004,
  physics-replace-0016 (w1), literature_arts-replace-0004,
  technology-replace-0015 (w1), finance-replace-0015 (w2),
  history-replace-0016 (q1), grammar-replace-0003 (w1, q2). Each `adds`
  matches the world's `assumes` text, and the README's own example does the
  same, so these are faithful. But for those queries the check shows only
  that the world is consistent with the answer; `missing_worlds` and the
  other world still test the chain. Where it matters, the answer can be
  derived instead (placeholder individuals for "some city in X", or a rule
  run backward, as for grammar-replace-0003). I left these alone because the
  choice runs through the whole dataset.
- **Inverse properties handled two ways** (A3): mathematics removes the
  inverse's property, geography and biology don't and fail. B1 fixes both.
- **people-insert-0009/0010** have the A1 problem but w1 is not marked an
  exception, so they also fail determinate checks. Same cause, not a
  separate problem.
- **Small leftovers:** grammar-delete-0014 has unused entities from the
  replace mirror; people-delete-0014 (`lives_under`) and physics-delete-0014
  (`heading_toward`) make a local relation functional with no question
  needing it (harmless). A few `find` queries have only one candidate, so
  their "no other answer follows" part tests nothing
  (technology-insert-0010 q0, geography-insert-0002 q0).

**What I did not find.** No `given` states an answer the prompt doesn't
give (grammar-insert-0003 puts a one-language presupposition in `given`; it
is flagged and harmless). No firm fact contradicts a record. Every unstated
firm fact is a presupposition of a question or a step a chain takes for
granted, and is flagged in the file's notes (listed in C). No `not_checked`
hides a dl query the logic can express, apart from the tags in A2. No
`exception` hides a fixable encoding.

**Confidence.** High that the failures are real and their causes are right.
High that the encodings are faithful: in the sample, one kind of real
encoding mistake turned up (the biology identity trick); it also affected
records outside the sample, and all 4 are fixed. Medium on how much some
passes prove: a share of the derived replaces get a determinate answer
partly from `adds` (above). The checker bug hides nothing in the current
results.

# People inserts (insert2): review

Validator: 20 files, 0 errors (with `relations/people.insert2.md` and `.insert2.checks.json`). criteria.py: no people insert under any rule (Rule 8 no longer lists `painted`).
All changes went through `people_ins2/build.py` (pre-review copy: `build.py.pre-review`), so the builder output and the JSON match.

## Tags and mix
- **ABox:** 0001-0002 `subject`, 0003-0004 `object`, 0005 `subject_object`, 0006-0007 `relation`, 0008 `all`.
- **TBox:**
  - 0009-0010 `subject` (made-up class under a real class);
  - 0011-0012 `relation` (real class and real object, made-up property);
  - 0013-0014 `all`.
- **RBox:** 0015-0017 `relation`, 0018-0020 `all`.

Every tag matches what is made up. No subject+relation or relation+object record. There is no TBox `object` insert, so the README's new TBox-object rule doesn't apply here.

## Ids
Every file's `id` matches its file name. No record points to another people-insert id. Moved records (0006, 0007, 0008) changed only their id and tag. Fresh counts for their made-up names are all 0, unchanged.

## REPLACED: 0003 (Leonardo → Stradivari)
The writer's doubt was right. literature_arts-insert-0003 is Michelangelo's newly found Wrenhallow Madonna, and the two records had the same subject area and pattern:
- an Italian Renaissance master and a newly found artwork;
- determinate queries on a famous painting and the birth town;
- a "how many / is X the only" pair of background-belief queries.

New 0003: "Antonio Stradivari made the Corvellani harp, a newly found harp."
- **Relation:** `created`, the existing relation. `painted` is removed from the scratch relations file.
- **Determinate:**
  - Cremona;
  - the Latin form of his name, Stradivarius.
- **Background beliefs:**
  - the count of known harps (one/two);
  - whether the Naples harp is the only one (yes/no).
- **Locality:**
  - near: Guarneri "del Gesù" → Giuseppe Guarneri;
  - far: leap year (3 uses).
- **Could it exist unrecorded:** most of his roughly 1,100 instruments are lost. The known harp is one item in a "one harp is known" count.
- **Evidence, all fresh counts:**
  - Corvellani 0, Corvellani harp 0;
  - Stradivari AND Cremona 16518;
  - Antonius Stradivarius 1214;
  - one harp AND Stradivari 21;
  - Stradivari harp 16.
- **Name searches:** WebSearch found only look-alikes (Corvina, Coryneliaceae). Wikipedia search: 0 hits.
- **Quotes checked word for word:**
  - three in the Wikipedia Stradivarius plain-text extract;
  - museionline.info: "Dall’assoluta rarità dell’arpa Antonio Stradivari (1681)".
  - The cultura.gov.it page could not be reached, so it is not cited.

## 0004, 0005: KEEP (one fix)
- **Fresh counts:** 12 re-run, 0 changed.
- **Name searches:** Vescarri, Solvaard and the Torvanger full names have no real match on the web or in Wikipedia search. The surname Torvanger alone is real.
- **Quotes:**
  - the Galileo quotes (2) and the Museo Galileo quote match word for word;
  - the Bergen quote was not word for word, because the article has a pronunciation note after "Bergen". It is fixed to "is a city and municipality in the Vestland county on the west coast of Norway. Bergen is the second-largest city in Norway".
- **Worlds and logic:**
  - 0004: the worlds are re-derived; w1 and w2 give concrete, different answers.
  - 0005: all four queries are determinate from the prompt plus the real relation's properties. The logic labels (dl) hold.
- **`object` checks:** in 0003 and 0004, the relation can hold several values, the direct question has one answer, and `edit.subject` appears verbatim once in the direct prompt. Neither record flips a people `subject` insert.

## Doubts
- 0003 and 0004 now share a pattern: a real maker, a newly found instrument, and a count of survivors. They differ from the literature_arts pair.
- The Naples instrument is described as an "arpetta" (a small harp). It is still a harp.
- The one-harp fact is rare in the corpus. The split only applies to a model that stores it.

# People: fictional inserts 0001-0020

Builder: `people_insert/build.py` (scratchpad). Relations: `relations/people.insert.md`, checks `relations/people.insert.checks.json`.
Validator: 20 files, 0 errors. criteria.py: Rule 5 no people failures; Rule 9 people insert RBox direct 3/3, derived 6/6, cross-lingual 6/6; Rule 11 shape and fictional mix ok for people (3/3/2, 2/2/2, 3/3).

| Id | Box | fictional | Edit | Derived (labels, derivation, logic) |
| --- | --- | --- | --- | --- |
| 0001 | ABox | entity | The novel 'Thornmere Hall' was written by Emily Brontë. | det composition (pen name Ellis Bell), det composition (Haworth); bb count of her novels (1/2, fol+arith), bb "only novel?" (yes/no) |
| 0002 | ABox | entity | The opera 'Orsolenza' was composed by Beethoven. | det composition (Bonn), det composition (Vienna); bb operas completed (1/2, fol+arith), bb "Fidelio only?" |
| 0003 | ABox | entity | The violinist Lucio Varnesi was a pupil of Paganini. | det composition (Genoa), det composition (Nice); bb pupil count (1/2), bb "Sivori only pupil?" |
| 0004 | ABox | relation | Marie Curie is vellum-paired with Lise Meitner. | all det: composition (Vienna), composition (meitnerium), symmetry (stated), composition (no Nobel: no) |
| 0005 | ABox | relation | Galileo is lodestar-bound to Kepler. | all det: composition (three laws), transitivity (stated, bridge in prompt), composition (Regensburg), composition (Tycho Brahe) |
| 0006 | ABox | relation | J. S. Bach is the ember-patron of Haydn. | all det: chain ember_patron_of∘teacher_of (rule stated, Haydn taught Beethoven checked), composition (Esterházy), composition (Germany), composition (fol+temporal, 1732<1750) |
| 0007 | ABox | both | Isveth Morlane is tide-sworn to Dariel Quenwick. | all det, all in prompt: symmetry, composition, transitivity, role chain (home harbour) |
| 0008 | ABox | both | Corvanne Ashlit is the gloam-warden of Halvric Dunmere. | all det: inverse, subproperty (guardian_of), asymmetry (no), composition (fol+temporal, no) |
| 0009 | TBox | entity | Every edition of the Calderwyn Open is a Grand Slam tennis tournament. | det inheritance x2 (new players in prompt); bb number of Grand Slams (4/5), bb "only these four?" |
| 0010 | TBox | entity | Every edition of the Halvren Classic is a men's major golf championship. | same shape as 0009 for golf majors |
| 0011 | TBox | relation | Every US president is lantern-bound to the Smithsonian. | all det inheritance: hypothetical new member, Lincoln (yes), Lincoln→Washington D.C., Washington→James Smithson |
| 0012 | TBox | relation | Every UK Poet Laureate is heron-bound to Westminster Abbey. | all det inheritance: new member, Tennyson, Hughes→London, Wordsworth→Elizabeth II (1953) |
| 0013 | TBox | both | Every Halvrenite scribe is ash-sworn to the Telmoor Archive. | all det: inheritance, via stated subclass, composition (Wyndhollow), contrapositive (no) |
| 0014 | TBox | both | Every Quenmark warden is lamp-tethered to exactly two Velish beacons. | all det: =2 (two), ≥1 (yes), sum (four, fol+arith), contrapositive (no) |
| 0015 | RBox | relation | 'Is quill-matched with' is symmetric. | direct yes; d yes / no (Kahlo-Rivera, Darwin-Wallace) |
| 0016 | RBox | relation | 'Is brass-ranked above' is transitive. | direct yes; d no / yes (Newton-Leibniz-Huygens, Mozart-Salieri-Schubert) |
| 0017 | RBox | relation | The inverse of 'is the cobalt-sponsor of' is 'is the cobalt-ward of'. | direct yes; d yes / no (Lovelace-Babbage, Tesla-Edison) |
| 0018 | RBox | both | 'Has as hearth-steward' is functional. | direct no; d no / yes |
| 0019 | RBox | both | 'Is rune-sworn to' is a subproperty of 'is sable-bound to'. | direct no; d yes / no |
| 0020 | RBox | both | brine_mentor_of ∘ brine_mentor_of ⊑ elder_brine_mentor_of (if-then sentence). | direct no; d no / yes |

Worlds (0001-0003, 0009, 0010): w1 the count/uniqueness is stored as a number or closed list and not recomputed; w2 stored as a list that the inserted entity joins (README's "How many countries border France?" pattern).

## Made-up names and Dolma counts (infini-gram, exact phrase), each also web-searched
Thornmere Hall 0, Orsolenza 0, Lucio Varnesi 0, vellum-paired 0, lodestar-bound 0, ember-patron 0, Isveth Morlane 0, Dariel Quenwick 0, tide-sworn 0, Tamsel Okravine 0, Skerrowmouth 0, Corvanne Ashlit 0, Halvric Dunmere 0, gloam-warden 0, Calderwyn Open 0, Halvren Classic 0, lantern-bound 0, heron-bound 0, Halvrenite 0, ash-sworn 0, Telmoor Archive 0, Wyndhollow 0, Quenmark 2, lamp-tethered 0, Velish beacon 0, quill-matched 0, brass-ranked 1, cobalt-sponsor 0, cobalt-ward 0, hearth-steward 0, rune-sworn 0, sable-bound 2, brine-mentor 0, elder brine-mentor 0. People in prompts: Lisandra Ferraveau, Jory Kettlewell, Bertil Ravenshaw, Emrys Vantorre, Oswin Thale, Nadia Quillon, Telra Voss, Odo Brask, Mirren Tash, Corvin Ashby, Ysolde Penhallow, Wren Talloway, Pell Agathe, Sorrel Venn, Ilka Drovenska, Tavio Renmarck, Dessa Marlowin, Sabine Aldercott, Mirabel Quint, Ansel Vardemoor, Liesl Varrow, Teague Holloran, Brisa Quintell all 0; Halden Crowe 2.
Rejected: Varnholt Open (a video-game cup uses it), thistle-bound (5), moon-sworn (26), Saltreach (6), Marisande (5), Seravine (4), Ashgarth (141), starward of (46), Kestrel Open (27).

No fictional person is made a relative of a real person: the only fictional person tied to a real one (0003) is a pupil; other fictional people relate only to each other through made-up, non-kinship relations.

## Doubts
- The entity indeterminacy pattern (spec's France example) leaves w1 holding the inserted fact next to a count it contradicts; both worlds are as the README defines them, but a reviewer may call w1 inconsistent.
- 0003: "Paganini's only pupil" is Sivori's standard epithet, but Wikipedia says "only known pupil" with citation needed, and the tuition was short.
- 0001: Emily Brontë may have begun a second novel (lost); "one novel" is the standard answer.
- 0009/0010 are tournaments (sports) rather than people strictly; derived queries are about players.
- 0011: Washington died before the Smithsonian existed; harmless for a timeless made-up relation, but odd.
- Rule 10 still fails dataset-wide on prompts used by other topics; this topic's far prompts were varied.

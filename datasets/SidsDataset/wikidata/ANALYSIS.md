# Sid's Dataset against Wikidata: first pass (2026-10-16)

What linking the dataset to Wikidata turned up. The numbers come from
`analysis.json` (`analyze.py`, QLever's Wikidata endpoint at qlever.dev,
queried 2026-10-15/16). The entity links were reviewed by an LLM pass, not yet
by a person (`checked: false` throughout `entities.json`).

## Files

| File | What it is |
| --- | --- |
| `wd.py` | Cached access to Wikidata search and QLever. Cache in `cache/` (gitignored). |
| `link.py` | Automatic first pass: search candidates per entity string and relation. Writes `entity_links.json`, `relation_candidates.json`. |
| `review/entities_out_*.json` | Reviewed decisions per entity string (category, item, confidence, notes). |
| `merge_review.py` | Merges the reviews into `entities.json`, the curated links. Hand fixes go there; `"checked": true` protects an entry. |
| `relation_map.json` | Curated: our relation to Wikidata properties, with direction and match quality. |
| `analyze.py` | Coverage, relation properties, fact checks. Writes `analysis.json`. |

## 1. How much of the dataset Wikidata can see

**Relations** (233 used): 65 exact, 6 narrower, 7 broader, 39 related, 116 none.
About 60 of the "none" are fictional relations; the rest are things Wikidata
does not model (grammar rules, number and group theory, music theory, finance
and networking specifics, class-level counts).

By record (real records only), the relation's match:

| Box | exact | narrower/broader | related | none |
| --- | --- | --- | --- | --- |
| ABox | 85 | 18 | 123 | 14 |
| TBox | 56 | 3 | 142 | 39 |
| RBox | 110 | 24 | 37 | 69 |

"Related" is mostly the causal relations (caused, raises, lowers, has_outcome),
which Wikidata only has as has effect / has cause, with no direction of
change: raises and lowers collapse to the same property.

**Entity strings** (683 distinct subjects and objects of real ABox/TBox edits):

| Category | Strings | |
| --- | --- | --- |
| entity | 187 | a specific person, place, work, event |
| class | 177 | a kind (mammal, prime number) |
| description | 233 | a phrase, not a name; most point to a main item (core_qid) |
| value | 62 | numbers, durations, directions |
| word | 19 | grammar's words, which Wikidata keeps as lexemes, not items |
| not in Wikidata | 5 | |

347 strings have their own item; 102 decisions are low confidence.

## 2. Facts checked (ABox insert and replace, real)

Of 90 replace records, 39 have both subject and original object linked:

| Grade | Replace originals | Meaning |
| --- | --- | --- |
| found | 26 | the statement is in Wikidata under the mapped property |
| found via location | 5 | Wikidata has a more specific place inside ours |
| linked | 3 | connected, but under a different property |
| not found | 5 | |
| unlinked | 51 | subject or object is a description, value or class |

No replace's counterfactual value turned out to be true in Wikidata. Of 40 real
inserts, 9 are confirmed by Wikidata (2025 facts such as Leo XIV born in
Chicago, Flesh by David Szalay), so they are true; whether models know them is
the audit's question. TBox subclass rules: 6 of 14 originals found along
subclass, instance and parent-taxon chains, 2 not found, 6 unlinked.

## 3. Mismatches between the graph and the dataset

**Granularity.** Wikidata stores the most specific value, we often store a
broader one: Einstein born in Ulm (ours: Germany), Dolly at the Roslin
Institute (ours: Scotland), the Mona Lisa in the Salle des Etats (ours: the
Louvre), the NYSE Building in the Financial District (ours: New York City).
These only match by following "located in" upward, i.e. our own transitivity
rule run over Wikidata. `analyze.py` now does this (`found_via_location`).

**Time.** Einstein was born in the German Empire; "Germany" is linked to modern
Germany. Wikidata keeps historical states as separate items.

**Direction.** Many of our relations are stored the other way round:
discovered, invented, founded, proved, inspired (stored on the later work),
symptom_of, causes_disease (stored on the disease), godparent_of, appointed.

**Qualifiers instead of statements.** Succession and appointment live as
qualifiers on "position held"; a ticker is a qualifier on "stock exchange";
alliances appear only as participants of a war.

**One step only.** Wikidata stores parent, not ancestor; next in series, not
precedes; direct parent company, not subsidiary chains. Our transitive
relations have to be computed from the one-step version.

**Different hierarchies.** Living things are taxa linked by "parent taxon",
not "subclass of": "fungi are eukaryotes" is only found through parent taxon.

**Words.** Synonym, antonym, homophone and derived-from exist only on lexemes;
plural and past tense are forms inside one lexeme, not relations.

**Declared properties.** Wikidata declares very few: 17 properties are typed
transitive, symmetry is declared two inconsistent ways (13 typed symmetric, 53
with a symmetric constraint), there is no way to declare property chains, and
single-value constraints are rare. So most of our "functional" tags (29
relations, e.g. capital_of, written_by, has_currency) have no Wikidata
counterpart to compare with. Real disagreements to look at:
- `synonym_of`: Wikidata declares it transitive; ours is not.
- `homophone_of`: Wikidata declares it symmetric; ours is not.
- `derived_from`: ours is transitive; Wikidata's is not.
- `housed_in` (mapped to location, P276): Wikidata declares it transitive; ours is not.

## 4. Problems in the dataset the linking exposed

These are about our records, not Wikidata.

1. **raises/lowers direction.** In 16 of 27 replace records the relation names
   the direction of the edited (false) statement, in 6 the true one, 5 are
   unclear. Delete records copy the relation from replace, so 16 deletes say
   e.g. "heating a gas raises its pressure" under `lowers`. The values are also
   written several ways (increase, raises, more rainfall, higher productivity).
   Needs one convention, then a fix in the records and in `build_delete.py`.
2. **Subjects that describe the edited value.** 11 records (Pompeii's volcano,
   the recipient of Ramanujan's letter, Dryden's rule, the Oakhurst
   punctuation, the cache-hit operation, ...) have a subject like "The volcano
   whose eruption destroyed Pompeii": it names the slot being edited, so its
   referent flips with the edit (Vesuvius, then Etna).
3. **Circular or relation-in-subject strings.** "FDR's successor as President"
   succeeded FDR, "Napoleon's final place of exile" exiled_to, "Bashar
   al-Assad's place of exile", "Lossless compression's designated
   reconstruction guarantee". The subject should be the person or thing.
4. **Disputed or loose facts.** The Gulf Stream as the cause of Europe's mild
   winters (disputed); every Holy Roman Emperor chosen by the prince-electors
   (not before the 13th century); the Ring of the Fisherman "destroyed" (it is
   defaced); "every trans-Neptunian dwarf planet is a plutoid" (true by
   definition).
5. **Wording.** "in the benchmark world" leaks into a technology statement;
   "swum" is a past participle, so that edit is ungrammatical rather than
   counterfactual; several object strings don't appear in their statement
   (preserve / preserves, unable to read / prevents from reading).

The full list, per entity string and record, is the `issue` field in
`entities.json`; `criteria.py` can pick these up as review items.

## Next

- A person checks the 102 low-confidence links and the descriptions' core items.
- Decide the raises/lowers convention and rewrite the subjects of items 2 and 3.
- Then the planned measures: entity familiarity (sitelinks, statements,
  incoming links), structural connectivity (direct links, two-hop paths), and
  the logical layer (consequence and support counts under our rules).

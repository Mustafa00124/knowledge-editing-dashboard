# Biology: fictional inserts 0001-0020

Records: `datasets/SidsDataset/records/biology/insert/biology-insert-00{01..20}.json`.
Generator (rerunnable): `scratchpad/bio_ins/gen.py`. It reads Dolma counts from `bio_ins/counts.json` and search notes from `bio_ins/search.json`.
Relations: `scratchpad/relations/biology.insert.md`; checks: `relations/biology.insert.checks.json`.
Validator: 20 files, 0 errors. criteria.py: Rules 7, 9 (RBox yes/no) and 11 (shape, fictional mix) pass for biology. Biology inserts are not listed under Rule 13. **Rule 5 fails on 18 of 20 records** (see Doubts 1).

| Id | Box | fictional | Edit | Derived (derivation, label) |
| --- | --- | --- | --- | --- |
| 0001 | ABox | entity | Kerroglossus fennellae is a newly described living species of echidna (instance_of) | chain→monotreme det; inheritance lays eggs det; echidna count 4/5 bg; monotreme count 5/6 bg |
| 0002 | ABox | entity | Apteryx tenebris is a newly described kiwi endemic to Stewart Island (endemic_to) | chain→endemic to NZ det; composition cannot fly det; kiwi count 5/6 bg; closed list of 5 kiwi yes/no bg |
| 0003 | ABox | entity | Sphenodon kerewai is a newly described living rhynchocephalian (instance_of) | chain→reptile det; inheritance not a lizard det; "tuatara the only living rhynchocephalian?" yes/no bg; count 1/2 bg |
| 0004 | ABox | relation | cattle egret drevin-linked to hippopotamus (symmetric) | symmetry ×2 (one with bridge "cattle egret is a heron"), composition ×2 (cetacean relatives, grass); all det |
| 0005 | ABox | relation | giant panda korvel-ranked above red panda (trans, asym) | transitivity, asymmetry (property in prompt), composition ×2 (Ailuridae, Asia); all det |
| 0006 | ABox | relation | Drosophila melanogaster cassel-bound to T. H. Morgan (inverse cassel_holds) | inverse ×2 (one via "1933 Nobel laureate"), composition ×2 (1933, Kentucky); all det |
| 0007 | ABox | both | Talvessa quorina korvel-ranked above Brennia ostala | transitivity ×3, asymmetry; prompt only; all det |
| 0008 | ABox | both | Vellunia pelloides drevin-linked to Corvalla dunensis | symmetry ×2, composition ×2 (made-up beetle/frog in prompt + real class fact); all det |
| 0009 | TBox | entity | Velkarids are a newly discovered living group of lungfish | inheritance new member det ×2 (one via "living lungfish breathe air"); "exactly six living lungfish?" bg; closed list bg |
| 0010 | TBox | entity | Morrenids are a newly discovered living genus of coelacanths | inheritance new member det ×2 (one via lobe-finned); "Latimeria the only living genus?" bg; genus count 1/2 bg |
| 0011 | TBox | relation | Every hummingbird drask-feeds on nectar | inheritance (Esmeraldas woodstar in prompt; ruby-throated), composition (flowers), binding (Trochilidae); all det |
| 0012 | TBox | relation | Every bat is thalvic | inheritance (Murina beelzebub in prompt; vampire bat; flying foxes), binding (only flying mammals); all det |
| 0013 | TBox | both | Every vesquorn is skell-scaled | inheritance ×4 (member, subclass, contraposition, second rule); all det |
| 0014 | TBox | both | Every drallimet is murrow-banded | the same shapes, reordered; all det |
| 0015 | RBox | relation | 'Is vossel-tied to' is transitive | direct yes; wolves→elk→aspen yes; otters→urchins→kelp "could fail?" no |
| 0016 | RBox | relation | 'Is marrow-paired with' is symmetric | direct (asymmetric?) no; honeybee/sunflower yes; oxpecker/giraffe "possible not?" no |
| 0017 | RBox | relation | quessel_bound_to ∘ lives_in ⊑ lives_in (if-then) | direct ("can it fail?") no; deer tick yes; remora "could fail?" no |
| 0018 | RBox | both | 'Has as brask-partner' is functional | direct ("two partners?") no; second partner? no; two names same species? yes |
| 0019 | RBox | both | inverse of 'fennopes' is 'is quorlish to' | direct yes; "possible not quorlish?" no; follows quorlish? yes |
| 0020 | RBox | both | 'Glimvers' ⊑ 'ostrels' | direct yes; ostrels ⇒ glimvers? no; glimvers ⇒ ostrels? yes |

Logic: dl throughout, except the counting queries (fol + arithmetic).
RBox yes/no: direct 3/3, derived 6/6, cross-lingual 6/6.
Entity inserts follow the "could it exist unrecorded" rule: new species or groups of cryptic or poorly surveyed animals (New Guinea echidnas, kiwi lineages, an island tuatara lineage, African lungfish, deep-reef coelacanths). The earlier drafts (a Baikal seal, a living rhinoceros, living proboscidean and sirenian families) were dropped as implausible.

## Made-up names (Dolma v4 exact counts)
All are 0 except `thalvic` (1) and `ostrels` (1): Kerroglossus, Kerroglossus fennellae, Apteryx tenebris, Sphenodon kerewai, velkarid(s), morrenid(s), drevin-linked, korvel-ranked, cassel-bound, cassel-holds, Talvessa quorina, Brennia ostala, Morvessa tarnicola, Ostrecca lunata, Ostrecca velunda, Vellunia pelloides, Corvalla dunensis, Velunia sarcosa, Drimella tasca, Tressia milvana, Quessia lorvana, drask-feeds, thalvic, vesquorn, skell-scaled, drallimet, murrow-banded, vossel-tied, marrow-paired, quessel-bound, brask-partner, fennopes, quorlish, glimvers, ostrels.
Rejected: Paraglossus (a real gobioid genus name turned up in the search), quorrel (20), ossling (206), Harnia (226), skerns/tarvels/drusks (25-148). The roots "drevin" (290) and "korvel" (65) are surnames; only the compounds are claimed.

## Doubts
1. **Web search budget ran out** (the shared 200-per-turn limit) after 5 name searches (Paraglossus, Kolotherium, Pusa argentata, velkarid(s), morrenid(s)). Only 0009 and 0010 carry a `search` source. The other 18 have Dolma counts only, so Rule 5 fails on them. I did not invent search results. Fix: run one search per name (or grouped) and add notes to `bio_ins/search.json`, then rerun `gen.py`.
2. TBox entity statements include "living" and "newly discovered"; without them the aggregates would not be touched (fossil members). The w1 worlds keep a closed count or list against the edit. That is the README's Kestria pattern, but a strict reader may call w1 inconsistent.
3. The TBox entity determinate query that uses a real class fact puts the new member in the prompt but lists only the real fact as the bridge (hops 2), because a made-up member fact cannot be checked. 0008's compositions do the same.
4. The Baikal-seal "only seal" fact was dropped with 0002's redesign. The kiwi list rests on the Kiwi article's "five recognised species"; the Stewart Island bird is a subspecies, so the new species does not contradict a named species.

# technology: RBox insert chain through real knowledge

## Replaced
`technology-insert-0017` (`Func(is_wick_keyed_to)`). Weakest of 0015-0017: its first
derived query ("Linux kernel wick-keyed to GPLv2; does it follow it is also
wick-keyed to MIT?" -> no) is "no" with or without the edit, and the second
leaned on a stated "different licence" premise. 0015 (symmetry) and 0016
(transitivity) both have discriminating instances. Edited the JSON directly
(not through `tech_ins/records.py` / `gen.py`).

## The chain
- Edit: "If a project is rivet-beholden to a programming language, and that
  language was created by a person, then the project is rivet-beholden to that person."
- Axiom: `is_rivet_beholden_to ∘ created_by ⊑ is_rivet_beholden_to`; subject
  `is_rivet_beholden_to`; tag `relation`; `created_by` is real (RELATIONS.md).
- Direct (no): "If a project is 'rivet-beholden to' a programming language, and
  that language was created by a person, could the project fail to be bound in
  the same way to that person?"
- Derived 1 (no): "The Django web framework is rivet-beholden to Python. Could the
  Django web framework fail to be rivet-beholden to Guido van Rossum?"
- Derived 2 (yes): "Ruby on Rails is rivet-beholden to Ruby. Does it follow that
  Ruby on Rails is rivet-beholden to Yukihiro Matsumoto?"
- Cross-lingual: derived 1 in zh/es (no/no), hop left out.
- Near: based_on/derivative_of chain question (yes). Far: "Is the relation 'is
  the mother of' symmetric?" (kept; 6 uses dataset-wide, <= 10).
- Yes/no pattern identical to the old record (direct no; derived no, yes; xl no, no).

## Bridges (bridge_in_prompt false, hops 2, checks added)
| Fact | Evidence |
| --- | --- |
| Python was created by Guido van Rossum. | Dolma exact 233; Wikipedia quote "Python was conceived in the late 1980s by Guido van Rossum at Centrum Wiskunde & Informatica (CWI) in the Netherlands." |
| Ruby was created by Yukihiro Matsumoto. | Wikipedia quote "Development of the language began in the mid-1990s by Yukihiro "Matz" Matsumoto in Japan." (checked against the raw wikitext); Dolma "created by Yukihiro Matsumoto" 332, full sentence 41 |

## Made-up name
"rivet-beholden": Dolma 0 ("rivet-beholden" and "rivet beholden"); web search
for "rivet-beholden": nothing (rivet pages, an 1892 Rivet-Holder patent). New
to RELATIONS.md and scratch relation files (no "beholden" anywhere).

## Validation
validate.py with the chain relation files: 20 files, 0 errors. criteria.py:
technology passes the chaining check; no technology insert under Rules 5, 7, 9,
10, 13; Rule 8 lists only `is_rivet_beholden_to` (scratch-only).

## Doubts
- `is_wick_keyed_to` (and its check) stays in RELATIONS.md / scratch files but
  no record uses it now; drop it when merging.
- "Could ... fail to be ...?" may be read pedantically ("only if the stated
  link were false"); the chain answer is still no.
- Technology inserts lose their only functional RBox insert (Rule 12 counts
  replace records only, so no criterion is affected).

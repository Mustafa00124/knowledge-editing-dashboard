# history: RBox chain insert through real knowledge

## Replaced
`history-insert-0015` (Sym(wax_sworn_to)). It was the weakest of 0015-0017: its "no"
instance (Venice-Genoa, Genoa-Milan, so Venice-Milan?) was "no" with or without the
edit, and its chain credited "not transitive" to the edit, which never said so.
Same yes/no pattern kept: direct yes, zh/es yes, derived yes + no. Tag `relation`.
Edited the JSON directly (written by a one-off script, no builder for this record).

## The chain
- Edit: "If a city was kiln-sworn to a ruler, and that ruler ruled a state, then the
  city was kiln-sworn to that state."  Axiom `kiln_sworn_to ∘ ruled ⊑ kiln_sworn_to`
  (`ruled` is already in RELATIONS.md, History).
- Direct: "If a city was 'kiln-sworn to' a ruler who ruled some state, was the city
  bound in the same way to that state?" -> yes (quoted wording once, first).
- Derived 1: "Antwerp was kiln-sworn to Elizabeth I. Does it follow that Antwerp was
  kiln-sworn to England?" -> yes. Bridge (stored, checked): "Elizabeth I ruled England."
- Derived 2: "Athens was kiln-sworn to Cleopatra. Could Athens fail to be kiln-sworn to
  Egypt?" -> no (discriminates: without the edit it could). Bridge (stored, checked):
  "Cleopatra ruled Egypt."
- Both: hops 2, bridge_in_prompt false, logic dl, chain marks the hop "(stored)".
  Cities lie outside the ruled state, so located_in can't stand in for the hop.
- zh/es: derived 1, hop left out (安特卫普 / 伊丽莎白一世 / 英格兰; Amberes / Isabel I / Inglaterra).
- Near: "If a person died in a city, and that city is located in a country, did the person
  die in that country?" (yes). Far: "Is the relation 'is a pen pal of' symmetric?" (yes; now 4 uses).

## Names and counts (fresh)
- kiln-sworn: Dolma 0, "kiln sworn" 0, RedPajama "kiln-sworn to" 0; web search "kiln-sworn": nothing
  (kilns, an unrelated novel "Knife Sworn"). New to the dataset (grep of RELATIONS.md, records, scratch relations).
- "Elizabeth I ruled England": Dolma 329 (snippets read, plain statements).
- "Cleopatra ruled Egypt": Dolma 265 (snippets read).

## Files
- `relations/history.chain.md` (kiln_sworn_to, fictional, `chain:ruled->kiln_sworn_to`), `relations/history.chain.checks.json`.

## Validation
validate.py with the chain files: 20 files, 0 errors. criteria.py: history passes the chain
check (only biology, mathematics listed); no history insert under Rules 5, 7, 9, 10, 13;
Rule 8 lists kiln_sworn_to (scratch-only, expected).

## Doubts
- `wax_sworn_to` is now unused but still in RELATIONS.md and relations/history.insert.md; drop it when merging.
- Elizabeth I also ruled Ireland; the chain still gives England, so the answer is unaffected.

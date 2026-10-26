# people: TBox 0019-0020 (replace + delete)

Generator: `scratchpad/people_tbox3/gen.py` (counts in `people_tbox3/counts.json`). No new relations, so there are no tbox3 relation files.
Validator: 40 files, 0 errors. criteria.py: no rule flags 0019 or 0020. Rule 13 first flagged the 0020 direct prompt, which did not contain
the subject verbatim; I reworded it.

| Id | Edit | Relation (tags) | Derivability | Derived queries (all `dl`, `inheritance`) |
| --- | --- | --- | --- | --- |
| 0019 | Being made a Knight Bachelor entitles a British layman to the style 'Sir' → 'Lord' | `confers` (causal, many) | very_unlikely | 2 determinate (fictional Graham Pell, Owen Tranter, named in the prompt); 2 background_beliefs (Paul McCartney, Elton John: "Which honorific is placed before X's name?") |
| 0020 | A person canonized by the Catholic Church is given the title 'Saint' → 'Blessed' | `styled_as` (none) | very_unlikely | 2 determinate (fictional Maria Kowalczyk, Tomás Ibarra); 2 background_beliefs (Joan of Arc, Ignatius of Loyola) |

There are 4 worlds per record (two independent storage choices). In w1-type worlds the stored by-name value wins and the member leaves the class (it is no longer a Knight Bachelor, or no longer canonized); it does not stay in the class as an exception to the rule. The side facts that go with leaving are the member's own knighting or canonization (year, monarch or pope). No succession or numbering depends on these classes. The deletes mirror the replaces: the rule is removed, new members are "not known" (determinate), and well-known members keep the original answer if stored by name, or are null if reached through the rule.

## Self-verification
- Counts: all 12 cited counts were re-run with `--fresh`, and the records carry the fresh values (no changes from the first run). "knighted AND Sir" is a sampled count and is marked approximate. "Ignatius of Loyola was canonized" is only 16, but that entry also has a Wikipedia quote, so Rule 5 is met.
- Quotes: all 6 Wikipedia quotes were checked against the raw wikitext (Knight Bachelor, Paul McCartney, Elton John, Canonization, Joan of Arc, Ignatius of Loyola). All are present word for word.
- Rejected or avoided:
  - Knight → "Sir" without scoping: honorary knights and knighted clergy (not dubbed, no "Sir") are exceptions, so the rule is limited to British laymen.
  - Thomas More: he is also "Sir" (a second honorific).
  - Francis of Assisi: his title is tied up with San Francisco and Pope Francis's name.
  - Mother Teresa: "Mother" is a second title.
  - "Blessed" as the near-query answer: it equals the new answer.
  - zh 封圣/宣福: these contain the old and new answers.
  - Popes, monarchs, etc.: these are succession classes.

## Doubts
- 0019: a Knight Bachelor later made a peer (e.g. Olivier) uses "Lord". The rule is worded as an entitlement, which still holds, and the well-known members hold no peerage. A strict reader may still call this an exception.
- In w1 the member keeps "Sir"/"Saint" without the class that grants it. This is the same looseness as the README's tarantula pattern.
- The zh prompt for 0020 uses 册封 with the English gloss "(canonization)". This is not the standard term, chosen to avoid leaking the answer.
- 0019 and 0020 both use the same pattern: an honorific given by a class.

# Geography: RBox insert chaining a made-up relation through real knowledge

## What changed
Reworked `geography-insert-0017` in place, keeping its id. It was already the topic's chain
(`harbour_sworn_to ∘ located_in ⊑ harbour_sworn_to`), but both derived prompts stated the
located_in hop. No builder script was involved: the JSON was edited directly.
0015 (symmetric) and 0016 (transitive) stay as they were. The tag is still `relation`,
so the 3 relation / 3 all mix holds.

## The chain
- Edit: "If a town is harbour-sworn to a city, and that city is located in a country, then the town is harbour-sworn to that country."
- Direct question (unchanged): quotes 'harbour-sworn to' once, first. Answer: yes.
- Derived 1: "Bergen is harbour-sworn to Kyoto. Does it follow that Bergen is harbour-sworn to Japan?" Answer: yes.
  Bridge: "Kyoto is located in Japan." (stored, not in the prompt). hops 2.
- Derived 2: "Cork is harbour-sworn to Montreal. Could Cork fail to be harbour-sworn to Canada?" Answer: no.
  Bridge: "Montreal is located in Canada." (stored, not in the prompt). hops 2. Without the edit the
  answer would be "yes, it could", so the question discriminates.
- Cross-lingual: derived 1 in zh and es, without the hop.
- Locality: unchanged. Near is the capital_of/located_in chain question. Far is "'is the employer of' symmetric", which appears in 1 record.
- Checks: "In which country is Kyoto?" → Japan; "In which country is Montreal?" → Canada.
- Yes/no pattern unchanged (direct yes, derived yes and no, cross-lingual yes), so Rule 9 stays 30/30, 60/60.

## Names and counts (Dolma v1.7, fresh 2026-10-26)
- harbour-sworn: 0; harbor-sworn: 0. A web search for "harbour-sworn" found no such term, only harbourmasters being sworn in.
- Bridges: "Kyoto, Japan" 273,305; "Montreal, Canada" 409,030.

## Validation
- validate.py with the extra relation and check files: 0 errors.
- criteria.py: geography passes the chaining check. The 9 other topics are still listed as failing it.
- No geography insert is listed under Rules 5, 7, 9, 10 or 13.

## Doubts
- `harbour_sworn_to` already exists in RELATIONS.md, tagged only `cardinality:many`. A scratch row that added
  `chain:located_in->harbour_sworn_to` conflicted with it in validate.py. So `relations/geography.chain.md` repeats the
  existing tags and notes the chain in its reading, and `geography.chain.checks.json` is `{}`. For the chain tag,
  add it to the RELATIONS.md row at merge. That matches 0015 and 0016, whose relations don't carry the edited property either.
- Halifax was swapped for Montreal, because Halifax is also a town in England (Rule 1).
- The bridges' evidence is counts of at least 100, not quotes.

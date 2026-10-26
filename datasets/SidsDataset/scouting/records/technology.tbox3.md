# Technology: TBox 0019, 0020 (replace + delete)

Generator: `scratchpad/tech_tbox3/gen.py`. Relations: `scratchpad/relations/technology.tbox3.md`
(two new property-free relations, `permits_use` and `has_end_tag_rule`; no checks file needed,
because inheritance relies on no relation tag).

| Id | Edit (original -> new) | Relation | Derivability | Derived (replace) | Logic |
| --- | --- | --- | --- | --- | --- |
| 0019 | Every OSI-approved license permits -> forbids commercial use | `permits_use` | unlikely | D1 Larchmont Public License (new, in prompt) det. no; D2 Quarrel under the Fennick License (new, in prompt, 3 hops) det. no; D3 MIT permits commercial use? bg w1 yes / w2 no; D4 MIT OSI-approved? bg w1 no / w2 yes | all dl |
| 0020 | Every void element in HTML has no end tag -> must have one | `has_end_tag_rule` | very_unlikely | D1 `<glint>` (invented) takes an end tag? det. yes; D2 `<tally>` without `</tally>` valid? det. no; D3 `<img>` takes an end tag? bg w1 no / w2 yes; D4 `<img>` void? bg w1 no / w2 yes | all dl |

Worlds: w1 = the member's property is stored by name, so the member leaves the class (the MIT
License is no longer OSI-approved; `<img>` is no longer void but still takes no content). w2 = the
property is reached through membership and the rule. Neither world contradicts firm facts outside
the chain: OSI approval is a listing, and void status is a spec classification that the other
members keep on their own.

Deletes: D1 and D2 are does-not-know (determinate). D3 is w1 original / w2 null. The membership
query does not split under delete, so as in delete-0007 it is replaced by a consequence of the
property: selling copies of MIT-licensed software (0019), and whether `<img>` markup without
`</img>` is valid (0020). Delete evidence leaves out the w1-only stored fact, because the
validator allows evidence only on edited facts, premises and bridges.

Rule 4: no overlap with 0005-0008 (path separator, line endings, GPL, ML typing) or with anything
else in the dataset. The near queries are "Which organization maintains the Open Source
Definition?" and "Which HTML element creates a hyperlink?". Their answers differ from the new
answers, and neither follows from the edit. The far prompts (Mona Lisa, Romeo and Juliet) are
new ones.

## Self-verification
- Validator: 40 technology files, 0 errors. `criteria.py`: technology is now 8/6/6 under both
  replace and delete. Rules 4, 5, 7 and 10 pass. Neither record appears in the Rule 13
  SubjectNotInPrompt list, because both subjects are verbatim in the direct prompt.
- Counts: all 15 re-run with `--fresh`. All match, 0 changed.
- Quotes: all 6 web quotes re-fetched with curl (UA SidsDatasetScout/1.0) and found word for
  word: the OSD criterion 6, the WHATWG syntax section, the MDN void-element glossary, the MDN
  img page (2 quotes) and the OSI MIT text. The Wikipedia MIT sentence and infobox were checked
  in the raw wikitext. 0 failed.
- Labels attacked:
  - New members are invented and named with their class in the prompt, so the rule is their
    only route.
  - Rule 1: OSD criterion 6 makes the OSI rule exceptionless. The WHATWG spec forbids end tags
    on all 13 void elements. Self-closing `/` is not an end tag, and SVG and MathML elements
    are foreign, not void.
  - No prompt asserts the membership a world denies.

## Doubts
- In 0019 w2 the MIT License forbids commercial use, against its own famous "sell copies"
  wording. I treat that as the member's property giving way, along with its side facts, the
  same precedent as F# in technology-0007, not as a fact outside the chain.
- Evidence for "MIT permits commercial use" uses an AND count (1033) plus quotes. The exact
  phrase is rare (6).

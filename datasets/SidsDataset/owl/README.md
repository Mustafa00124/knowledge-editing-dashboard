# Formal verification (OWL 2 + HermiT)

Checks that the description-logic reasoning in Sid's Dataset records holds:
derived answers follow, determinacy labels are right, worlds are consistent
and none is missing. The records are never changed; each record's formal
encoding lives here, in `formal/<record_id>.json`.

| File | What it is |
| --- | --- |
| `relations.py` | Compiles `RELATIONS.md` into `relations.owl` (the published ontology), `relations.json` (the table `reason.py` reads) and `relations_report.md` (axioms OWL 2 DL forbids, tag problems). Rerun after editing `RELATIONS.md`. |
| `dlsyntax.py` | The axiom language below, and the file-against-record checks. |
| `encode_check.py` | Checks formal files without HermiT (fast; use while encoding). |
| `../reason.py` | Runs HermiT over the formal files and writes `reason_report.json`. |
| `formal/` | One encoding per record. |

```bash
venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/relations.py          # after RELATIONS.md changes
venvs/easyedit_venv/bin/python datasets/SidsDataset/owl/encode_check.py --topic geography
venvs/easyedit_venv/bin/python datasets/SidsDataset/reason.py --topic geography   # or record ids
```

## The formal file

| Key | What it holds |
| --- | --- |
| `id` | the record id |
| `notes` | optional: encoding choices worth knowing |
| `relations` | optional: record-local relations not in RELATIONS.md, `{name: [tags]}` in RELATIONS.md tag syntax (`["functional"]`). Never redeclare a catalogued one. |
| `entities` | `{key: surface or [surfaces]}`. Keys are lower snake_case individuals. Surfaces are how the record writes the entity in its answers (`"the Pacific Time Zone"`), matched ignoring case, punctuation and a leading the/a/an. `null` makes a placeholder individual with no gold answer. |
| `distinct` | optional: `"all"` (default: every entity with a surface) or a list of keys. OWL has no unique names, so two keys may be the same individual unless they are distinct. |
| `original` | the fact before the edit (replace, delete); TBox: the class axiom; RBox: the property axiom. |
| `edit` | the edited fact or axiom (replace, insert); `[]` for delete and for an RBox edit that only removes a property. |
| `premises` | background ids the original follows from (a derived edit: derivability likely or very likely). |
| `background` | `{id: axiom or [axioms]}`: what the model holds before the edit, in every world: premises, bridge facts, firm facts, rules. One id is one belief that can give way as a whole. |
| `firm` | background ids that never give way (definitional rules, firm facts outside the chain, README Decisions 1). The repair search leaves them alone. |
| `gives_up` | optional: background ids every world gives up after the edit (a side fact the edit forces in all worlds). |
| `worlds` | `{world id: {stores, gives_up, adds}}`, ids exactly the record's (none: one implicit world). `stores`: axioms this world held before the edit (background beliefs: by name or by description). `gives_up`: background ids this world drops after the edit (derived beliefs: the premise that gives way; TBox: membership or the stored fact). `adds`: axioms the world says hold after the edit ("it stands in a city on Central Time"). `exception`: a reason, for a world that can't be checked. |
| `queries` | one entry per derived query, by index `q` (0 to 3, or 0 to 1 for RBox), each with exactly one of `ask`, `find`, `not_checked` (a reason: `"fol (arithmetic): ..."`), `exception` (a reason). |

A query entry:

| Key | What it does |
| --- | --- |
| `ask` | a yes/no claim (an axiom). The expected answers come from the record. `mode` `holds` (default): yes = the claim follows, no = its negation follows, null = neither. `follows` ("Does it follow that ...?"): yes = follows, no or null = does not follow. `consistent` ("Is it consistent with this that ...?"): yes = the KB plus the claim is consistent. |
| `find` | `"a r ?"`, a path `"a r1/r2 ?"`, or `"a : <class expression with ?>"`. Each candidate answer (every gold answer of the query mapped to an entity, plus `candidates`) is tried; the expected one must follow, and (unless `"exclusive": false`) no other candidate may. A null gold means none follows. |
| `given` | facts the prompt states. Added to the KB for this query only (queries whose given facts mention only their own individuals share one KB). |

Expected answers are never written in the formal file: `reason.py` reads
them from the record (`original_answer`, `new_answer`, `world_answers`), so a
file can't drift from its record.

### Phases

- **pre**, per world: background + the world's `stores` + `original` (+ given).
- **post**, per world: background minus `gives_up` + `stores` + `adds` + `edit` (delete: no edit) (+ given).
- RBox: property axioms in `original`/`edit` change the relation table:
  pre has the original and not the edit, post the other way round.
- Delete: a world must also make the deleted fact stop following (checked by
  adding its negation); the repair search for a derived delete finds which
  premises must go.

### Axiom language

```
has_capital(australia, sydney)          property assertion
not has_capital(australia, canberra)    negative property assertion
milford : Fjord                         class assertion (any class expression after the colon)
a = b      a != b                       same / different individual
Fjord ⊑ FloodedGlacialValley            class inclusion; also ≡ and `disjoint`
located_in(?b, ?c), City(?c), in_time_zone(?c, ?z) -> in_time_zone(?b, ?z)
                                        SWRL rule over named individuals (same(?x, ?y),
                                        different(...) and Nothing(?x) in heads)
Trans(r) Sym(r) Asym(r) Func(r) InvFunc(r)
r ⊑ s      r ≡ inv(s)      r o s ⊑ t      Disj(r, s)      property axioms
```

Class expressions: `Name` (upper case first), `Thing`, `Nothing`, `not C`,
`C and D`, `C or D`, `r some C`, `r only C`, `r value a`, `r min 2 C`,
`r max 1 C`, `r exactly 1 C`, `{a, b}`, parentheses; `inv(r)` for an inverse.

### Example

`geography-replace-0003` (the Space Needle moved to Central Time; a derived
edit with two derived-belief worlds):

```json
{
 "id": "geography-replace-0003",
 "notes": "The building-to-city rule is a SWRL rule (in_time_zone is functional, so it can't be the target of an OWL chain).",
 "entities": {
  "needle": ["the Space Needle"], "seattle": ["Seattle"], "washington": ["Washington State"],
  "pacific": ["the Pacific Time Zone", "Pacific Time"], "central": ["the Central Time Zone", "Central Time"]
 },
 "original": ["in_time_zone(needle, pacific)"],
 "edit": ["in_time_zone(needle, central)"],
 "premises": ["needle_seattle", "wa_pacific", "building_rule", "seattle_city"],
 "background": {
  "needle_seattle": "located_in(needle, seattle)",
  "wa_pacific": ["in_time_zone(washington, pacific)", "in_time_zone(seattle, pacific)"],
  "building_rule": "located_in(?b, ?c), City(?c), in_time_zone(?c, ?z) -> in_time_zone(?b, ?z)",
  "seattle_city": "seattle : City",
  "seattle_wa": "located_in(seattle, washington)"
 },
 "firm": ["building_rule", "seattle_city", "seattle_wa"],
 "worlds": {
  "w1": {"gives_up": ["needle_seattle"], "adds": ["needle : located_in some (City and in_time_zone value central)"]},
  "w2": {"gives_up": ["wa_pacific"], "adds": ["in_time_zone(washington, central)", "in_time_zone(seattle, central)"]}
 },
 "queries": [
  {"q": 0, "find": "needle : located_in some (City and in_time_zone value ?)"},
  {"q": 1, "not_checked": "fol (arithmetic): clock times"},
  {"q": 2, "find": "seattle in_time_zone ?"},
  {"q": 3, "ask": "located_in(needle, seattle)"}
 ]
}
```

HermiT then shows: the premises entail the original; before the edit every
query gets its original answer; after it, q0 is Central in both worlds (the
premise route); q2 is Pacific in w1 and Central in w2; q3 is no in w1 (the
Needle in Seattle would put it on Pacific Time, and in_time_zone is
functional) and yes in w2; both worlds are consistent; and the only minimal
repairs of edit + background are {needle_seattle} and {wa_pacific}, one per
world, so no world is missing.

## What the checks are

`reason.py` writes, per record, a list of checks, each `pass`, `fail` or
`not_checked` with a detail (per world where it applies):

| Check | Meaning |
| --- | --- |
| `derived_edit` | the premises entail the original fact |
| `pre` | each derived query's original answer follows before the edit, in every world |
| `post_determinate` | a determinate (or RBox, or unlabelled insert) query's new answer follows in every world |
| `post_worlds` | an indeterminate query's world answer follows in that world |
| `differ` | the answers that follow differ between at least two worlds |
| `consistent` | each world is consistent before and after the edit (delete: and no longer entails the deleted fact) |
| `missing_worlds` | when edit + background is inconsistent (delete: still entails the deleted fact), every minimal repair (smallest set of non-firm background beliefs to give up, up to 3) is some world's `gives_up`; an uncovered repair is listed with what the determinate queries answer there |
| `not_checked` | fol queries and anything the file leaves out, with the reason |
| `encoding` | the file disagrees with its record (`encode_check.py` problems) |

## Encoding guide (for the remaining topics)

Read first: the record (all of it: edit, premises, worlds' `assumes` and
`summary`, every derived query's chain and `determinacy_why`, `notes`), the
relation's row in RELATIONS.md, and one encoded record of the same box and
operation in `formal/` (geography has all of them). Then:

1. **Entities.** One key per individual the chains mention; give each gold
   answer string as a surface (`"a glacier"`, `"glacier"`). Yes/no answers
   need no entity. A value such as "two" or "a US state" can be an
   individual too. Run `encode_check.py` until it is clean.
2. **Background = the chains' stored facts.** Every "(stored)" or
   "(premise)" step of any chain, and every bridge fact, as one background
   item. A belief that gives way as a whole (a premise with its side facts)
   is one item with a list of axioms. Mark `firm` what the record treats as
   fixed (definitional premises, facts whose violation the record calls "not a
   world"). Encode the exclusivity a question presupposes ("a glacier or a
   river?", "one region per place") as a firm axiom (`Func` of a local
   relation, or a rule), or no clash can arise.
3. **Worlds.** Background beliefs: the by-name / by-description choice goes
   into `stores` (a fact vs a rule over the edited relation). Derived beliefs
   and TBox members: the premise or membership that gives way goes into
   `gives_up`; what the world says replaces it goes into `adds`.
4. **Queries.** `find` for wh-questions, `ask` for yes/no. Questions with a
   description ("the city the Gate stands in") are a `find` with a class
   expression. `logic: fol` (numbers, dates, clock times, counts, raises/lowers
   comparisons) is `not_checked` with its theory. A `dl` query that DL can't
   express faithfully is `not_checked` with why; a world or query that is
   classically inconsistent by design is an `exception`.
5. **Run `reason.py` on the record.** For every failure decide: an encoding
   mistake (fix the file) or a real problem in the record (keep it failing,
   and say why in `notes`). Never change a record to make a check pass.

Pitfalls:

- **Open world.** Nothing is false unless something makes it so. A "no"
  needs a functional relation, a disjointness, an asymmetry or a rule that
  derives `Nothing`. A null (does not know) answer passes only when neither
  the claim nor its negation follows.
- **No unique names.** Individuals are distinct only through `distinct`
  (default: every entity with a surface). Placeholders (`null`) may be any
  individual.
- **Simple roles.** OWL 2 DL forbids functional, inverse functional and
  asymmetric on a property that is transitive or the target of a chain;
  `relations.py` keeps those as SWRL rules over named individuals (see
  `relations_report.md`). They don't fire on unnamed individuals, so name the
  individuals a clash needs.
- **Rules only see named individuals and HermiT does not fire them on facts
  it derives through OWL transitivity or chains.** `relations.py` therefore
  adds a mirror rule for every transitive property and chain. Use rules for
  "X observes the zone of the city it is in"-style premises, and use a
  local or catalogued property, not a description, as the rule's head.
- **SWRL built-in names** (`contains`, `equal`, ...) are safe: rules are built
  directly, not parsed by owlready2.
- **Not expressible:** numbers and arithmetic, dates and ordering, counts of
  members ("how many lakes"), raises/lowers comparisons, defaults and
  exceptions, and anything that needs a closed world (the model "only" knows
  three types). Those queries are `fol` or `not_checked`.

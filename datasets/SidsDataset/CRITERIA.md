# Sid's Dataset: criteria

What makes a good record, and what the dataset as a whole has to cover.
[`README.md`](README.md) defines the scheme (operations, knowledge form,
queries, tags); this file is the quality bar on top of it.

Three parts:

- **Rules** every record must pass.
- **Balance targets** the dataset meets as a whole, not each record.
- **Design note** on surface form, hop form and derivation trees, the part
  still being designed.

**Checking.** `python datasets/SidsDataset/validate.py --criteria` (code in
`criteria.py`) checks everything a script can and lists the records that
fail. The dashboard shows the same checklist: Datasets, Sid's Dataset,
**Criteria checklist**. It only reports for now. A check becomes a hard error
in `validate.py` once the records pass it.

## Rules

**R1. True and unambiguous.** Every answer the dataset relies on is clearly
true or clearly false: original and new answers, bridge facts, premises,
locality references. Leave out facts that experts dispute, that depend on a
date, definition or source, or that have several defensible answers. An RBox
instance must be clear in the real world whatever the axiom says: "polar bears
prey on seals, seals prey on cod, so polar bears prey on cod?" is out, because
whether polar bears eat cod is unclear. *Checked by a person, helped by the
Wikidata fact check (`wikidata/`).*

**R2. Stable subjects, self-contained statements.** A subject is a named
thing or class (Pompeii, prime number), or a description of something the
edit does not change ("the capital of France", in a two-relation fact; see
the design note). Two kinds are out:
- a description of the value being edited: in "the volcano that destroyed
  Pompeii is Vesuvius", edited to Etna, the subject means Vesuvius before the
  edit and Etna after, so nothing stable is tested;
- a phrase that contains its own answer: "FDR's successor succeeded FDR" is
  true from its wording alone.

A statement makes sense on its own: no "under those conditions", no "the
specified", no mention of the edit. *Checked by a person. The subject also
matters to locate-and-edit methods, which edit at its last token.*

**R3. No repeated edits.** No two records edit the same fact, in the same or
different words. Replace and delete are the exception: each delete removes
its replace record's original fact.

**R4. The models hold the right things before editing.** From the model
audit, for the four main instruct models (Qwen3-4B-Instruct-2507,
Olmo-3-7B-Instruct, Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.1;
`AUDIT_MODELS` in `criteria.py`): every model holds a replace or delete
record's original fact, and no model already holds a real insert. Fictional
inserts are exempt. A fact is held when the direct and paraphrase questions
both get the original answer (RBox: the direct question and both instances).

**R5. Delete means "I don't know".** After a delete, every query through the
removed fact expects an abstention. A plain "no" fails, also on yes/no
questions. *(The README and judge still also accept a negation; to align.)*

**R6. Locality can catch leaks.** A near unrelated query's answer differs from
the edit's new answer, or a model that leaks the edit still passes. Delete is
exempt: there a leak is an abstention, which any near query catches.

**R7. One name per relation, and the label fits.** Every relation is in
`RELATIONS.md` under one snake_case name, including relations that only appear
inside an RBox axiom. A record's relation describes its own statement (for
delete, the fact it removes), so a `raises` record's statement says raises.

**R8. Named facts are in Wikidata.** When a fact's subject and object are
named things and its relation has a Wikidata property (`wikidata/relation_map.json`:
exact, narrower or broader), the original fact (replace, delete) or the new
fact (real insert) is in Wikidata, directly or through a chain our rules
allow (Einstein born in Ulm, Ulm in Germany). Facts Wikidata cannot express
(rules and mechanisms, direction of change, made-up examples, properties of
every member of a class) are exempt; for them being in Wikidata is only
measured (B5). *Checked by `wikidata/analyze.py`.*

## Balance targets

**B1. The taxonomy is covered evenly.** 10 edits per cell of edit operation x
topic x box, and causal and associative about even within ABox and TBox.
`validate.py` reports the counts.

**B2. Yes/no answers are 50/50 in RBox,** for direct, derived and
cross-lingual queries, per operation and per topic. ABox and TBox are already
roughly balanced and not held to it.

**B3. Derivations are not dominated by composition.** *Open: counts to agree.*
Relation-property derivations (inheritance, transitivity, subproperty,
inverse, chain, symmetry, asymmetry, functional) should make up most of the
derived queries, with composition and the task types (binding, application,
scope) capped. RBox edits get a fixed mix of axioms too. The checklist reports
the current counts; targets go in `criteria.py` once agreed. Reflexivity was
dropped from the RBox axiom mix on 2026-10-22: replace and delete slot `0025`
is now a subproperty edit (5 added, 5 removed).

**B4. Surface and hop forms are mixed.** *Open: shares to agree.* Facts are
spread over the grid of surface form (one relation, two relations) by hop
form (likely stored, ambiguous, likely composed); see the design note.

**B5. Familiarity and connectivity spread.** Facts range from obscure to very
familiar, and from weakly to highly connected in Wikidata. Outside R8, being
in Wikidata is measured, not required.

**B6. Far locality prompts vary.** No far unrelated prompt is used more than
10 times.

## Design note: surface form, hop form and derivation trees

Two separate questions about how a fact is composed:

- **Surface form:** how many relations the fact's wording contains. We choose
  it when writing the record.
- **Hop form:** how many stored facts a model combines to produce it. It is a
  property of the model, which we estimate and then measure.

Neither is arity, which is how many arguments a relation takes.

### Surface form

Recorded per record in `form`:

- `one_relation`: "Paris has the Eiffel Tower."
- `two_relation`: "The capital of France has the Eiffel Tower." The subject
  is a description through a second relation; the record names what it
  refers to (the capital of France: Paris, via `capital_of`), which links it
  to Wikidata as a two-step path. Under R2 the description must point at
  something the edit does not change.

### Hop form

Hop form follows from two things the record already holds:

- **`edit.premises`**, as a list of trees: the different ways the fact can be
  derived from other facts in the world. This is objective, and Wikidata
  checks it: the fact may be stored directly, only through a chain, or both.
- **`derivability`**: our estimate of whether a model stores the fact or
  rebuilds it from a tree.

| Premises | Derivability | Hop form |
| --- | --- | --- |
| none | (n/a) | one-hop: nothing to derive it from |
| at least one tree | low: the direct form is common in text | likely stored |
| at least one tree | middle | ambiguous |
| at least one tree | high: the direct form is rare, its parts common | likely composed |

Three signals inform derivability:

1. **Wikidata's shape:** is the fact stored directly, only through a chain,
   or both? `wikidata/analyze.py` measures this.
2. **Text frequency:** how often the direct form appears compared with its
   parts. Measured with infini-gram's AND queries, which count where two
   phrases occur within a few tokens of each other ("Eiffel Tower" near
   "France", against "Eiffel Tower" near "Paris"), on public corpora (Dolma,
   RedPajama, the Pile). The main models' own data isn't public, so this is
   a proxy.
3. **Our rating**, as the tag is assigned now.

**Two-relation facts don't force two hops.** "How tall is the volcano that
destroyed Pompeii?" can be answered three ways: composed (resolve the
description to Vesuvius with a stored fact, then its height), alias (the
description works like a name for Vesuvius), or shortcut (the height stored
with the phrase itself). So a two-relation fact lists one-fact trees as well
as its two-fact tree.

### Measuring the route per model

Which route a model actually uses is measured per model, not fixed in the
dataset:

- **Route test:** edit one form and ask the other. After "Vesuvius is 2,000
  ft", the descriptive answer changes for composed and alias routes, not for
  a shortcut. After "Pompeii was destroyed by Etna", it becomes Etna's height
  only for the composed route.
- **Probe:** at the last token of "the volcano that destroyed Pompeii", check
  whether "Vesuvius" can be read from the model's hidden states. The causal
  tracing tools can do this.

### Derivation trees

Because the route varies, a derived query can have more than one defensible
answer. After "the capital of France is Rome", "where is the Eiffel Tower?"
gives Paris if the model stores "Eiffel Tower in Paris", and Rome if it
stores "Eiffel Tower in the capital of France". So a derived query lists its
plausible trees (premises and the answer each predicts), and scoring records
which tree the model's answer follows. An answer that follows no tree is the
failure. A tree only counts for a model whose audit shows it holds that
tree's premises. Ambiguous facts and class hierarchies (a square is both a
rectangle and a rhombus) are where trees branch most.

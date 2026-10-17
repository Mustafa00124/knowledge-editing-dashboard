# Sid's Dataset: criteria

What makes a good record, and what the dataset as a whole has to cover.
[`README.md`](README.md) defines the scheme (operations, knowledge form,
queries, tags); this file is the quality bar on top of it.

Three parts:

- **Rules** every record must pass.
- **Balance targets** the dataset meets as a whole, not each record.
- **Design note** on hop form and derivation trees, the part still being
  designed.

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

**R2. Named subjects, self-contained statements.** The subject is a named
thing or class (Pompeii, Mount Vesuvius, prime number), never a description
of the value being edited ("the volcano that destroyed Pompeii") and never a
phrase that contains its answer ("FDR's successor"). Descriptions belong in
the queries, as binding queries (see the design note). A statement makes sense
on its own: no "under those conditions", no "the specified", no mention of
the edit. *Checked by a person; the subject also matters to locate-and-edit
methods, which edit at its last token.*

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
the current counts; targets go in `criteria.py` once agreed.

**B4. Hop forms are mixed.** *Open.* One-hop, two-hop and ambiguous facts
each make up a fixed share (see the design note).

**B5. Familiarity and connectivity spread.** Facts range from obscure to very
familiar, and from weakly to highly connected in Wikidata. Being in Wikidata
is measured, not required: Wikidata covers named facts and class
hierarchies well, causal facts and class properties hardly at all.

**B6. Far locality prompts vary.** No far unrelated prompt is used more than
10 times.

## Design note: hop form and derivation trees

**Hop form** is how many stored facts a model combines to produce a fact. It
is not arity, which is how many arguments a relation takes.

| Hop form | Example | What an edit should do |
| --- | --- | --- |
| One-hop | "Paris is the capital of France": stated everywhere, stored directly | Stay local |
| Two-hop | "Fleming's discovery was made in London": rarely stated, composed from two facts | Change with either link |
| Ambiguous | "The Eiffel Tower is in France": stated directly and also reachable through Paris | Depends on the model |

This is what the **derivability** tag already rates (axiomatic means one-hop,
derived means two-hop, the middle means ambiguous). Three signals feed it:

1. **Wikidata's shape:** is the fact stored directly, only through a chain
   (Einstein born in Ulm, Ulm in Germany), or both? `wikidata/analyze.py`
   measures this.
2. **Text frequency:** how often the direct form appears in text compared
   with its parts. Measured with infini-gram's AND queries, which count where
   two phrases occur within a few tokens of each other ("Eiffel Tower" near
   "France", against "Eiffel Tower" near "Paris"), on public corpora (Dolma,
   RedPajama, the Pile). The main models' own data isn't public, so this is
   a proxy.
3. **Our rating:** the derivability tag as it is assigned now.

Which route a model actually uses is a property of the model, and is measured
per model rather than fixed in the dataset:

- **Route test:** edit one form and ask the other. Edit "Vesuvius is 2,000 ft"
  and ask "how tall is the volcano that destroyed Pompeii?". If the answer
  follows, the model composes; if only the edited wording changes, it holds a
  shortcut.
- **Probe:** at the last token of "the volcano that destroyed Pompeii", check
  whether "Vesuvius" can be read from the model's hidden states. The causal
  tracing tools can do this.

**Derivation trees.** Because the route varies, a derived query can have more
than one defensible answer. After "the capital of France is Rome", "where is
the Eiffel Tower?" gives Paris if the model stores "Eiffel Tower in Paris",
and Rome if it stores "Eiffel Tower in the capital of France". So a derived
query lists its plausible trees (premises and the answer each predicts), and
scoring records which tree the model's answer follows. An answer that follows
no tree is the failure. Likewise the derivability premises of a fact list
each tree that supports it. A tree only counts for a model whose audit shows
it holds that tree's premises. Ambiguous facts and class hierarchies (a
square is both a rectangle and a rhombus) are where trees branch most.

# Sid's Dataset

Our own knowledge-editing benchmark. Published benchmarks mostly edit simple
facts and test generalization with paraphrases. Sid's Dataset edits three
kinds of knowledge (facts, class rules and properties of relations) through
three belief revision operations (insert, replace, delete). It then asks
questions that need different kinds of reasoning to answer: whether the edit
took, whether it survives logic, whether it spreads to what follows from it,
and whether it stays contained. For every question, the right answer after
the edit is worked out in advance, including the cases where it depends on
how the model stored its knowledge. The question the dataset answers:

> Under what kinds of knowledge and belief revision operations does a
> knowledge edit succeed, propagate to what follows from it, and stay
> contained?

The study has five parts. The tables below give each part, then the values
inside it. [`SPEC.md`](SPEC.md) is the full specification the records are
built against, [`RELATIONS.md`](RELATIONS.md) the relation catalogue,
[`CRITERIA.md`](CRITERIA.md) the quality bar, and
[`docs/hparam_analysis.md`](../../docs/hparam_analysis.md) the tuning
analysis.

| Part | What it answers | Contains |
| --- | --- | --- |
| [1. What explains results](#1-what-explains-results) | What we vary, and slice results by | Knowledge structure, operation, determinacy, editing method |
| [2. How we measure](#2-how-we-measure) | How we observe what an edit did | Question types, task types, metrics |
| [3. Controls](#3-controls) | What we hold steady or vary only to show a result generalizes | Topic, models, split |
| [4. Validity checks](#4-validity-checks) | Why the records can be trusted | Logic verification, model audit, review, automated rules |
| [5. Hyperparameter tuning](#5-hyperparameter-tuning) | How each method is set up fairly before it is compared | Search stages, hyperparameters per method |

## 1. What explains results

| Factor | Values | What it tells us |
| --- | --- | --- |
| Knowledge structure | box, relation property, derivability | How the edited knowledge is connected to the rest, and so what can follow from it |
| Operation | insert, replace, delete | Which kind of belief change an editor handles |
| Determinacy | determinate, indeterminate | Whether the edit forces one right answer, or the answer depends on how the model stored things |
| Editing method | 9 editors in 4 families | Which approach to editing propagates and stays contained |

### Knowledge structure

**Box.** How description logic divides a knowledge base.

| Box | What it holds | Example |
| --- | --- | --- |
| ABox | A fact about a particular thing | Paris is the capital of France. |
| TBox | A rule about a whole class | Every capital is a city. |
| RBox | A property of a relation itself | "Located in" is transitive. |

**Relation property.** The property a question's answer rests on. It decides
which questions can follow from an edit.

| Property | Rule | Example (edit, then question) |
| --- | --- | --- |
| Inverse | a R b means b S a | Ann is Billy's parent. Who is Ann's child? |
| Symmetry | a R b means b R a | Billy is Manny's sibling. Is Manny Billy's sibling? |
| Functional | one value per subject | Sydney is Australia's capital. Is Canberra? |
| Subproperty | a R b implies a S b | Lyon is Germany's capital. Which country is Lyon in? |
| Transitivity | a R b and b R c give a R c | The nephron is part of the respiratory system. Is the glomerulus? |
| Role chain | a R b and b S c give a T c | She was born in Lyon. Which country was she born in? |
| Inheritance | a class rule passes to its members | Every spider has six legs. How many legs does this spider have? |
| Cardinality | removing one value leaves the others | (delete only) |
| Instantiation | an RBox property applied to two given things | (RBox only) |

**Derivability.** Whether a fact is stored or worked out. It is rated for the
edited fact and for each related and derived answer.

| Value | Meaning | Example |
| --- | --- | --- |
| Stored | Stated everywhere, so the model holds it directly | Paris is the capital of France. |
| Derived | Hardly ever stated, but follows from facts the model holds | Elizabeth I's paternal grandfather was Henry VII. |

### Operation

| Operation | Belief revision name | What it does | Right answer afterwards |
| --- | --- | --- | --- |
| Insert | Expansion | Adds a made-up fact the model does not hold | The new answer |
| Replace | Revision | Swaps a held fact for a false one | The new answer, never the old one |
| Delete | Contraction | Removes a held fact (the replace record's original) | No longer the old answer |

Each insert and delete record is paired with a replace record, so the three
operations compare directly.

### Determinacy

| Label | Meaning | Example |
| --- | --- | --- |
| Determinate | Every valid way of holding the knowledge gives the same answer | Edit: Sydney is Australia's capital. "Is Canberra the capital?" No. |
| Indeterminate: background beliefs | The answer depends on how the model stored a related fact | "Which city is Parliament House in?" Sydney if stored as "in the capital", Canberra if stored by name. |
| Indeterminate: derived beliefs | The answer depends on which premise of a derived edit gives way | Edit: the Space Needle is on Central Time. "Which time zone is Seattle on?" |

An indeterminate question lists its valid outcomes as **worlds** (Hase et
al. 2024). Indeterminate questions appear only in main-split ABox replace
records, one per record.

### Editing methods

| Family | Methods |
| --- | --- |
| Fine-tuning | FT-M, LoRA |
| Locate then edit | ROME, AlphaEdit, FiDAL |
| Neuron editing | FiNE |
| Portability editors | IFMET, LTI, LoCo |

## 2. How we measure

### Question types

| What it asks | Question type | Per record |
| --- | --- | --- |
| Did the edit take? | Direct: the edited fact as a question | 1 |
| | Paraphrase: the same question in other words | 1 (not RBox) |
| | Cross-lingual: the direct question in Chinese and Spanish | 2 |
| Does it survive logic? | Propositional: the fact inside a negation, a conjunction and a disjunction | 3 |
| Does it spread? | Related: a stored answer, 1 or 2 hops away, that must change | 1 (ABox replace and delete) |
| | Derived: an answer never stated, which follows in 2 hops | 3 determinate, + 1 indeterminate on main ABox replace; RBox: 2 instances |
| Does it stay contained? | Unrelated near: shares the subject, relation or topic | 1 |
| | Unrelated far: shares nothing | 1 |

### Task types

What a related or derived question makes the model do with the edit.

| Task | What the question asks | Example |
| --- | --- | --- |
| Answer | The conclusion itself | Which country was she born in? |
| Composition | Follow the edit, then look up an unconnected fact about the new value | Which river flows through the capital of France? |
| Binding | Reach the edited subject by another name it knows separately | In which city is the International Monetary Fund headquartered? (edit names the IMF) |
| Application | Use the conclusion in a practical task | When it is noon in Chicago, what time is it at the Space Needle? |

### Metrics

Our names describe what is measured. Each maps to the usual term in the
literature.

| Metric | Usual name | Over | In tuning |
| --- | --- | --- | --- |
| Rewrite | reliability, efficacy | direct | gate |
| Generalizability | portability | paraphrase, related, determinate derived | score |
| Cross-lingual | cross-lingual portability | cross-lingual | score |
| Logical consistency | (ours) | propositional | score |
| Specificity | locality | unrelated near and far | gate |
| Answer diversity | fluency | the English answers | gate |
| Grammar | (ours) | the English answers | gate |
| Contraction abstention | (ours) | a delete record's direct, paraphrase and cross-lingual answers | reported |

**Generalizability, part by part.**

| Part | What passes |
| --- | --- |
| Paraphrase | The new answer to the reworded question |
| Related | The changed stored answer |
| Derived (headline) | The new answer on determinate derived questions the unedited model answered correctly |
| Reported beside it | Each relation property, task type, hop count and logic (dl, fol) on its own |

**Main experiment probes.** Diagnose why an edit does or does not spread.

| Probe | What it shows |
| --- | --- |
| Indeterminate change | Whether the answer stayed the original, moved to a world's answer, or moved to an answer no world gives |
| Hinted | The derived question asked again with its bridge fact given. Passing only with the hint means the model holds the edit but does not connect it. |
| Reasoning | The derived question answered step by step; a judge finds the first step that goes wrong (missed edit, missed fact, wrong step) |

## 3. Controls

| Control | Values | Why |
| --- | --- | --- |
| Topic | geography, people, history, finance, biology, physics, literature and arts, technology, mathematics, grammar | A finding about rules isn't secretly a finding about one domain |
| Models | Qwen3-4B-Instruct-2507, Olmo-3-7B-Instruct, Llama-3.1-8B-Instruct, Mistral-7B-Instruct-v0.1 | A finding holds across model families and sizes |
| Split | dev (120 records), main (600 records) | Hyperparameters are tuned on dev only; main is the test set the paper reports. They share no fact or subject. |

Every topic has the same shape: per operation, 8 ABox, 6 TBox and 6 RBox
records in main, 12 records in total in dev.

## 4. Validity checks

| Check | What it guards against | How |
| --- | --- | --- |
| Logic verification | Wrong logic, or an unsound translation from English to logic | Every record encoded in description logic and checked with the HermiT reasoner (`reason.py`, `justify.py`) |
| Model audit | Testing knowledge the models never had | Each of the 4 models answers the original fact, premises and bridge facts before any edit |
| Review | Questions answerable without the knowledge tested, ambiguity, logic errors, stale notes | Humans and agents mark each record and question green or red under two manual rules |
| Automated rules | Leaks, duplicates, missing evidence, gaps in coverage | `criteria.py` checks rules 3 to 15 (some with an LLM judge) |

**Logic verification, what it checks.**

| Check | Passes when |
| --- | --- |
| Premises | A derived edit's premises entail the original fact |
| Before the edit | Every derived question's original answer follows |
| Determinate answers | The answer follows in every world |
| Indeterminate answers | Each world's answer follows in that world, and they differ |
| Worlds | Each world is consistent, and every minimal repair is a world |
| Justifications | The axioms an answer follows from match the question's stated property, bridges and hops |

**Model audit, what it checks.**

| Check | Passes when |
| --- | --- |
| Original fact held | Direct and paraphrase both get the original answer (tagged per model) |
| Premises and bridges held | The model knows the facts a question relies on |
| Insert is new | No model already holds an inserted fact |

**Review.** Humans and agents (Codex and Claude) mark every record and
question green or red under two rules.

| Rule | Asks |
| --- | --- |
| 1. Clear and sensible | Is the edit, each question and each world unambiguous and sensible? |
| 2. Serves the purpose | Does the record help answer the dataset's question, or measure something else? |

**What review catches.** The problem types reviewers have found, with their
share of all flags ([`ISSUES.md`](ISSUES.md) has every type, counts and
examples).

| Problem | Share | What it looks like |
| --- | --- | --- |
| Answerable without the knowledge tested | 73% | A default answer passes (a yes/no guess); the prompt gives the answer away or restates the edit; the property is part of the word's meaning, so no edit is needed; "I don't know" after a delete is disputed because the fact can be worked out another way |
| Logic and link errors | 10% | The question does not follow from the edit; the answer does not move with the edit; a wrong or not truly determinate gold; a near question that leaks the edit |
| Ambiguous framing | 8% | More than one fair answer; unclear negation or quantifier scope; "could" or "does it follow" framing; unnatural phrasing; a translation problem |
| Record hygiene | 5% | Out-of-date notes; a wrong label; an evidence problem; fields that disagree |
| Edit design | 4% | The edit clashes with knowledge the model holds firmly; a pairing problem; a time-sensitive or contested fact |

**Automated rules.**

| Group | Rules |
| --- | --- |
| Wording | 3 stable subjects, self-contained statements, no answer in the prompt |
| Uniqueness | 4 no repeated edits, no shared facts between splits |
| Evidence | 5 enough evidence for every fact; 15 related and derived answers change and are what they claim |
| Model knowledge | 6 the models know what the record relies on |
| Measurement | 7 specificity can catch leaks; 9 yes/no answers balanced in RBox; 10 far prompts vary |
| Coverage | 8 one name per relation; 11 every record has its queries, the splits their shape; 12 relation properties and task types balanced |
| Runs | 13 every method runs on every edit; 14 delete and insert paired with replace |

## 5. Hyperparameter tuning

Every method is tuned per model on the 120 dev records only, with one rule
for all methods so the comparison is fair: maximise the mean of
Paraphrase, Generalizability, Cross-lingual and Logical consistency, among
settings that pass the gates (Rewrite at least 0.9; Answer diversity at
least 0.8 and Grammar at least 0.9 of the unedited model; Specificity at
least 0.7).

| Stage | Design | What it finds |
| --- | --- | --- |
| 1. Screen | Two-level factorial: each setting at a low and a high value, all combinations crossed, plus centre runs | Which settings matter, and in which direction |
| 2. Sweep | One at a time: 8 to 10 values of each setting that matters, the others held at their best | The exact value of each setting |

**Hyperparameters per method.** Which matter is preliminary, from the first
search (archived in `results/archive/tuning-steps0-3-2026-11-15`, analysis
in [`docs/hparam_analysis.md`](../../docs/hparam_analysis.md)).

| Method | Matter | Matter little |
| --- | --- | --- |
| FT-M | layer, norm constraint | learning rate, steps, weight decay |
| LoRA | learning rate, alpha, target matrices, layer window | rank, steps, weight decay |
| LoCo | learning rate, steps, alpha, constraint | rank, implication count and length, completion weight |
| FiNE | learning rate, neuron count | alpha, beta, gamma, last layer |
| ROME | clamp, layer, v_lr, gradient steps | KL weight, weight decay |
| AlphaEdit | clamp, v_lr, layer window | mom2 weight, KL weight, weight decay |
| FiDAL | candidate layers, clamp, v_lr | gradient steps, mom2 weight, KL weight |
| IFMET | NLL weight, v_lr | support count, deep layers, mom2 weight, KL weight |
| LTI | clamp, layer window | v_lr, NLL weight, mid layers, mid and last KL weights, mom2 weight |

FT-M's learning rate is tuned, but matters little: its norm constraint caps
how far the weights can move, so once the constraint binds, a larger
learning rate only reaches the cap sooner.

**Findings so far.** From the first search (40 dev edits), not yet from the
re-tuning on the 120 dev records.

| Finding | Detail |
| --- | --- |
| Strength settings matter most | They move the objective about 6 points on average; layers 4.5, training signal 4, regularisers 1.6 (noise level) |
| The model matters more than the method | Of the variation in the final objective, 45% is the model, 28% the method, 27% their interaction. Llama is easiest to edit well, Olmo hardest |
| Two regimes | Training methods (FT-M, LoRA, LoCo) trade objective for Specificity along one curve, so the Specificity gate sets their value. Locate-then-edit methods are limited by Rewrite and flat once they pass |
| One trade-off, one independent score | Paraphrase, Generalizability and Cross-lingual rise together and against Specificity. No setting improves Logical consistency |
| Rankings depend on the gate | At Specificity 0.7 the training methods lead; at 0.8 all nine methods sit within 7 points |
| Per-model values are partly overfitted | Resampling records repeats the same pick 45% of the time; the conclusions above hold regardless |

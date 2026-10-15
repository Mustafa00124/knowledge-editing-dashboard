# Sid's Dataset: record criteria

Constraints every record, and the dataset as a whole, must meet. The
[`README.md`](README.md) defines the scheme (operations, knowledge form,
queries, tags); this file says what counts as a good record within it.

`python datasets/SidsDataset/validate.py --criteria` (code in `criteria.py`)
reports every criterion a script can check, with the records that break it.
It is report only for now and never fails; a check moves into `validate.py`'s
errors once the records meet it. Section 4 needs an LLM pass and a person.

Status: **draft**. Sections marked *Open* still need numbers agreed.

## 1. No repeated edits

- No two records share an edit: not the same statement, and not the same
  (subject, relation, object) in different words.
- The one exception is replace and delete: each delete record is built from a
  replace record and removes the same original fact (300 shared facts).
- RBox: at most one record per (relation, axiom) per operation, across all
  topics. A relation may still appear in several RBox records with different
  axioms ("borders" is symmetric; "borders" is transitive).
- Known violation: "'Is part of' is (not) transitive" is in both biology and
  physics (replace and delete 0022).
- Every relation a record uses, including ones that only appear inside an
  RBox axiom, is in `RELATIONS.md` under one snake_case name.

## 2. Delete has one ground label: "I don't know"

After a delete, every query that went through the deleted fact (direct,
paraphrase, cross-lingual, derived) expects the model to say it does not know.
A plain "no" is not a pass, including on yes/no questions.

> README currently says `negate` also counts as success. That needs bringing
> in line with this rule (README, judge rubric, scoring code).

## 3. Yes/no balance

- RBox: within each operation (insert, replace), the gold answers of yes/no
  queries are 50% yes and 50% no, counted separately for direct, derived and
  cross-lingual queries. Delete inherits replace's questions with "I don't
  know" as the gold, so it has no balance of its own.
- Balance per topic as well as overall, as near as the counts allow.
- Current state: RBox insert direct is 81 yes / 3 no, derived 171 / 29; RBox
  replace direct 60 / 30, derived 148 / 52.
- ABox and TBox are not under this rule. Their yes/no queries are roughly
  balanced already (insert and replace: ABox 28 yes / 48 no, TBox 102 / 83).

## 4. No ambiguity

Every answer the dataset relies on must be uncontroversially true or false:
the original and new answers, bridge facts and their checks, premises, and
locality references. Leave out anything where:

- experts disagree, or the answer depends on a definition, a date, a region or
  a source;
- the "false" side might actually be true (the dataset authors aren't sure,
  and a model could reasonably know otherwise);
- there are several defensible answers and the judge would have to choose.

For **RBox instance questions** the conclusion must hold or fail *in the real
world* unambiguously, independent of the axiom being edited. Example to
remove: "Polar bears prey on seals, and seals prey on cod. Does it follow that
polar bears prey on cod?" (`biology-replace-0021`). Whether polar bears eat
cod is not clear-cut, so a "yes" from the model may be world knowledge rather
than the edited axiom. A good instance has a clearly false conclusion
("Ospreys prey on trout, and trout prey on mayflies. Does it follow that
ospreys prey on mayflies?").

## 5. Locality has to be able to detect leaking

A near unrelated query's reference answer must differ from the edit's new
answer (insert and replace). Otherwise a model that leaks the edit still
passes. Delete is exempt: there a leak is an abstention, which any near query
catches, and a near query answered by the removed value (often a premise) is
wanted. 31 records currently break this (e.g.
`geography-replace-0001`: after "the capital of Australia is Sydney", the near
query asks for Australia's most populous city, answer Sydney).

## 6. Relation property mix (*Open*)

Fixed proportions so that generalization is not dominated by composition and
task-type queries. Two places this applies:

- **RBox edits:** which axiom each edit asserts or removes.
- **ABox and TBox derived queries:** which derivation each of the 4 derived
  queries uses.

Candidates, roughly in order of importance:

| Property / derivation | DL | Where |
| --- | --- | --- |
| Subclass / inheritance | C ⊑ D | TBox derived; RBox not applicable |
| Transitivity | Trans(R) | all boxes |
| Subproperty | R ⊑ S | all boxes |
| Inverse | R ≡ S⁻ | all boxes |
| Property chain | R ∘ S ⊑ T | all boxes |
| Symmetry | Sym(R) | all boxes |
| Asymmetry | Asym(R) | all boxes |
| Functional | Func(R) | replace and delete |
| Composition (multi-hop) | none | ABox, TBox |
| Binding, application, scope (task types) | none | ABox, TBox |
| Disjointness, inverse functional, reflexivity | Disj, InvFunc, Refl | RBox only today; keep or drop? |

Counts to be agreed. Current state of the 2,400 ABox/TBox derived queries:
inheritance 422, composition 620, task types 926, inverse 207, functional
102, transitivity 50, symmetry 24, chain 23, asymmetry 24, subproperty 2.

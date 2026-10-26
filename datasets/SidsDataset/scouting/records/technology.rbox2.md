# Technology RBox 0017-0018

Validator (4 files, with technology.md + technology.rbox2.md relations and checks): 0 errors.
criteria.py: no technology RBox yes/no imbalance (new answers: 0009 no, 0010 no, 0011 yes, 0012 yes, 0017 no, 0018 yes).

| Id | Edit | Direct (orig -> new) | Derived instances |
| --- | --- | --- | --- |
| replace-0017 | role chain directly_imports ∘ module_provided_by_package ⊑ depends_on removed (axiom `⋢`) | yes -> no | requests imports urllib3.util (urllib3) => depends on urllib3?; seaborn imports matplotlib.pyplot (matplotlib) => depends on matplotlib? yes -> no |
| delete-0017 | the chain deleted | yes -> null | same, -> null |
| replace-0018 | is_cname_alias_of no longer functional | "Can a DNS name be a CNAME alias of more than one canonical name?" no -> yes | www.wikipedia.org -> dyna.wikimedia.org, also text.wikimedia.org?; docs.python.org -> dualstack.python.map.fastly.net, also python.org? no -> yes |
| delete-0018 | functionality deleted | no -> null | same, -> null |

Near/far: 0017 "Is 'depends on' transitive?" (yes) / "Is 'is the mother of' asymmetric?" (yes); 0018 "Can a relational table have more than one primary key?" (no) / "Is 'is a cousin of' symmetric?" (yes).

## Why each original holds
- 0017: importing a module runs code from the package that provides it, so the importer cannot run without that package. The relation `directly_imports` already carries `chain:module_provided_by_package->depends_on` in RELATIONS.md; I only added the missing row for `module_provided_by_package` (no tags) in relations/technology.rbox2.md. Instances checked in source: requests/adapters.py `from urllib3.util import Timeout as TimeoutSauce`; seaborn/axisgrid.py `import matplotlib.pyplot as plt`.
- 0018: RFC 1034 §3.6.2 / RFC 2181 §10.1: a name that owns a CNAME may hold no other data (DNSSEC records aside), so it has exactly one CNAME target. CNAME chains don't break it. Reuses the shared `is_cname_alias_of` row (already `functional`). Instances checked with dig on 2026-10-25; they are stated in the prompt anyway.

## Doubts
- 0017 general question: an import wrapped in try/except ImportError is an optional dependency; I count it as a dependency, but a strict reader might call it an exception. The instances are hard dependencies.
- 0018 is technical; a model may not know the DNS rule well, so the pre-edit audit may drop it for weaker models.
- 0018 derived prompts say "at the same time" to rule out a later DNS change.
- Checks for directly_imports chain and is_cname_alias_of functional are in relations/technology.rbox2.checks.json (not required by the validator for RBox).

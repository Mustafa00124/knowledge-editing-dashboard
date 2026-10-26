# Technology round 2 review (ABox 0013-0016, RBox 0017-0018)

Validator (all four technology relation files): 36 files, 0 errors. criteria.py: Rule 9 ok (per topic within 1), Rule 10 ok, technology Rule 11 row complete. The "every relation in RELATIONS.md" failure only means the scratch relation files are not merged into RELATIONS.md yet; it affects every topic.

## Evidence
- 22 infini-gram counts re-run with `--fresh`: all 22 identical.
- Wikipedia quotes re-fetched (plain-text extracts): TCP, HTTP, Ubuntu, elementary OS and RHEL found word for word. The Manjaro quote failed because the article now puts a pronunciation after the name. Fixed by starting the quote at "is a free and open-source ..." (replace and delete 0014).
- 0017: the source lines were re-checked on GitHub (requests `adapters.py` l.32, seaborn `axisgrid.py` l.10). Both are top-level, unconditional imports.
- 0018: the CNAME records were re-checked with dig. They match the prompts.

## Per record
| Id | Verdict |
| --- | --- |
| replace-0013 | KEEP. Both inheritance queries are determinate, discriminate, and do not restate the edit. The class rule is definitional and has a check. w2 (HTTP stored as needing a connection-oriented transport) is lopsided but valid (Decision 4). |
| delete-0013 | FIXED (scope wording). Forgetting the handshake in every world is coherent: the handshake entails the deleted fact, so a real delete must take it too, just as a derived-fact delete takes a premise. Without it, the "does not know" answers could be re-derived. The scope and worlds now cover all of TCP's connection facts (setup, teardown, connection states such as ESTABLISHED), not only the handshake. |
| replace-0014 | FIXED (quote). The subproperty and chain queries are correct and discriminate. `based_on` carries `chain:derivative_of->derivative_of` and `subproperty:derivative_of` in technology.md, and both have checks. Note: this chain also follows from subproperty plus transitivity, but it is a declared chain over two different relations. w1 (Ubuntu base keeping pacman/AUR) is lopsided but contradicts nothing outside the chain. The AUR prompt names Arch: that is a cue to the original base, not the answer to its own yes/no question, so it stays. |
| delete-0014 | FIXED (quote). Otherwise correct. |
| replace-0015 / delete-0015 | KEEP. Transitivity uses the transitive `derivative_of` with the bridge RHEL -> Fedora. The premise-route query is the same in both worlds. The Debian-from-RHEL world is excluded on dates. |
| replace-0016 / delete-0016 | REPLACED. In Blender's w2 the GPL becomes permissive. That premise cannot give way (Decision 1): the GPL's copyleft follows from its own terms and from firm facts outside the chain, such as GPL enforcement against other companies (BusyBox suits, Linksys/OpenWrt) and the LGPL being a "weaker" copyleft. Calling the share-alike terms side facts does not save it. Every license-kind derived edit has this problem, and TBox 0006 already uses the GPL. New edit: "Rocky Linux is derived from Fedora" -> "from Knoppix" (`derivative_of`, likely: 0 hits for "Rocky Linux is based on / derived from / is Fedora"; the premises "Rocky Linux is based on RHEL" and "RHEL is derived from Fedora" are backed by Wikipedia quotes and counts). Worlds: Rocky's base gives way, or RHEL's origin does. Knoppix (2000) predates RHEL (2002), so w2 breaks no dates. Determinate queries: a premise route ("the distribution Rocky Linux is built on ... Knoppix or a derivative") and transitivity ("derived from Debian?" via Knoppix -> Debian, 100 hits plus a quote). The delete replaces the Debian query with a composition through the deleted derivation (Fedora's six-month release cycle, Wikipedia-verified). The unused `has_license_kind` row was removed from relations/technology.md. |
| replace/delete-0017 | FIXED. The original now says "unconditionally imports" in the edit, the direct prompt and the relation check: an import inside try/except ImportError, or under `if TYPE_CHECKING`, is a real exception to "depends on". The edit is a genuine declared chain over two different relations, and both instances hold. |
| replace/delete-0018 | FIXED. Following the coordinator's new rule, the statement and original are now just "'Is a CNAME alias of' is (not) functional.", with chain steps to match. The direct prompt now begins "Under the DNS standard, ...", because Route 53-style weighted or geo routing can serve different CNAME targets for one name. In the standard (RFC 1034 §3.6.2, RFC 2181 §10.1) the property has no exception. |

## Coverage (replace, determinate slots)
- Inheritance: 2 (0013).
- Subproperty: 1 (0014).
- Chain: 1 (0014).
- Transitivity: 2 (0015, 0016).

All four properties appear. Each property query discriminates and is the same in every world.

RBox yes/no: criteria Rule 9 ok. The rewording kept every answer.

## Remaining doubts
- 0017: a module that several packages provide (cv2 from opencv-python or opencv-python-headless) is still an edge case for the general question. The instances themselves are clean.
- 0016: Rocky Linux dates from 2021, so the corpus counts for its premises are small and the stored claim rests mainly on the quote. Models that miss the checks get dropped.
- 0013 w2 and 0014 w1 are lopsided worlds, kept under Decision 4.

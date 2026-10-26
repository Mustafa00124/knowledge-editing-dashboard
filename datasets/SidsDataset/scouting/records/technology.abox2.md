# Technology ABox 0013-0016 (relation-property coverage)

Built by `scratchpad/tech_abox2/build.py` (counts read from `tech_ig/r9_abox2.jsonl`, never typed). Validator with the technology relation files: 0 errors (36 files; 0017/0018 are another writer's). criteria.py technology row: ABox 8/8, stored 4/4, derived 4/4; Rule 5 ok; Rule 7 ok.

## Records

| Id | Edit | Derivability | Derived queries (replace) | Logic |
| --- | --- | --- | --- | --- |
| 0013 | TCP is connection-oriented -> connectionless (`instance_of`) | very_unlikely ("TCP is a connection-oriented protocol" 862 + TCP lead) | 1 **inheritance** det: does TCP use a handshake to set up a connection? yes->no (rule: connectionless protocols neither set up nor close connections). 2 **inheritance** det: is there a connection to close at the end? yes->no. 3 background: does HTTP/1.1 run over TCP? (w1 yes / w2 no). 4 background: is HTTP/1.1's transport connection-oriented? (w1 no / w2 yes) | all dl |
| 0014 | Manjaro is based on Arch Linux -> Ubuntu (`based_on`) | unlikely (265 exact + lead) | 1 **subproperty** det: is Manjaro a derivative of Ubuntu? no->yes (based_on ⊑ derivative_of). 2 **chain** det: is Manjaro derived from Debian? no->yes (based_on ∘ derivative_of ⊑ derivative_of, bridge Ubuntu->Debian). 3 background: Manjaro's package manager (pacman / APT). 4 background: AUR access (yes / no) | all dl |
| 0015 | elementary OS is derived from Debian -> RHEL (`derivative_of`), premises: based on Ubuntu; Ubuntu based on Debian; definitional chain rule | likely (direct forms 2/0/0 vs 60 and 2418 for premises; only a Wikipedia category says Debian-based) | 1 premise_route det (binding): is the distro elementary OS is built on RHEL or an RHEL derivative? no->yes. 2 **transitivity** det: is elementary OS derived from Fedora? no->yes (bridge RHEL derived from Fedora). 3-4 derived_beliefs: based on Ubuntu? (no/yes); Ubuntu based on Debian? (yes/no) | all dl |
| 0016 | Blender is distributed under a copyleft -> permissive license (`has_license_kind`), premises: Blender under GPL; GPL is copyleft; definitional | likely (direct forms 0/0; one sampled FAQ states it) | 1 premise_route det (binding): is the license Blender is distributed under copyleft? yes->no. 2 **inheritance** det: must a distributor of a modified Blender provide source? yes->no. 3-4 derived_beliefs: Blender under GPL? (no/yes); GPL copyleft? (yes/no) | all dl |

Property coverage on replace determinate slots: transitivity 1 (0015), chain 1 (0014), subproperty 1 (0014), inheritance 3 (0013 x2, 0016). No functional.

Deletes mirror each: null on every route through the removed fact, worlds re-derived (w2 or the forgotten premise gives null). Rephrased: 0014 subproperty asks "Arch derivative?", chain slot replaced by a composition (Arch's rolling release) since Arch has no parent; 0015 Fedora slot replaced by Debian's founder (composition); 0013/0016 inheritance queries use the original class rule (connection-oriented / copyleft).

## New relations (scratch files only)
`based_on` (asymmetric, subproperty:derivative_of, chain:derivative_of->derivative_of), `derivative_of` (transitive, asymmetric, cardinality:many; not `derived_from`, which grammar uses for words), `has_license_kind` (no tags), `instance_of` (identical tags to physics/math). Relation checks added for the three tags used.

## Worlds dropped / design choices
- 0015: a third revision (Debian itself derived from RHEL) excluded: it keeps the replaced value and contradicts dates.
- Rejected candidates: `successor_of ⊑ released_after` (any discriminating edit inverts release order and breaks firm dated facts about games/accessories); Ethernet/Python "developed at" chains (background worlds collapse into creator/employer coupling); MIT License copyleft (swapped for TCP to avoid three license records).

## Doubts
1. 0013 delete: TCP's handshake states the deleted fact, so the scope and both worlds list it as forgotten; without that, the determinate nulls would be reachable around the delete.
2. 0014: w1 (Ubuntu-based Manjaro keeping pacman/AUR) is technically odd but contradicts nothing outside the chain; the AUR prompt names "Arch" (a cue, not the answer). In the delete, pacman/AUR suggest Arch abductively.
3. 0016 w2 (GPL permissive) is lopsided; the GPL's share-alike terms are listed as side facts that go.
4. 0013 w2 (HTTP stored as needing a connection-oriented transport) is the weaker storage hypothesis.
5. "Blender is released under the GNU GPL" exact count is only 8; the premise rests on the Wikipedia quote.

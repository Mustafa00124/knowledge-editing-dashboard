# Finance inserts (fictional), 0001-0020

Records: `datasets/SidsDataset/records/finance/insert/finance-insert-0001.json` … `0020.json`, built by
`{SCRATCH}/fin_insert/build.py` (with `abox_entity.py`, `tbox_entity.py`), which pulls every infini-gram count
from `ig.py` rather than typing it. Relations: `{SCRATCH}/relations/finance.insert.md` and `.insert.checks.json`.

Validator: 20 files, 0 errors. criteria.py: no finance-insert item on any rule (Rule 5 ok, Rule 9 ok, Rule 11
shape and fictional mix ok, Rule 13 ok after rewording 0016's direct prompt, where the subject had appeared twice).

## Records

| Id | Box / fictional | Edit | Derived (derivation, label, logic) |
| --- | --- | --- | --- |
| 0001 | ABox entity | The Corvell specimen is a 1913 Liberty Head nickel. | chain det; composition det (made without Mint authorization: no); count of known 1913 nickels 5/6 BB; ">5 known?" no/yes BB |
| 0002 | ABox entity | The Corvane specimen is an 1894-S Barber dime. | chain det (proof); composition det (1 of 24 struck); survivors 9/10 BB; unaccounted 15/14 BB (fol arithmetic) |
| 0003 | ABox entity | The Halden specimen is an 1822 half eagle. | chain det (gold coin); composition det (face value $5); known 3/4 BB; ">3 known?" no/yes BB |
| 0004 | ABox relation | The Bank of England is vault-paired with the Bank of Japan. | 3 composition det (Tokyo, central bank of Japan, yen); symmetry det (property in prompt) |
| 0005 | ABox relation | Nintendo is keystone-funded by Mitsubishi UFJ Financial Group. | transitivity det (property and link in prompt); 3 composition det |
| 0006 | ABox relation | Berkshire Hathaway is an anchor-stake holder in Coca-Cola. | inverse det (in prompt); 3 composition det (Omaha, Atlanta, Buffett) |
| 0007 | ABox both | Quarrington Savings is tithe-bound to the Ellerby Fund. | transitivity, inverse, composition, asymmetry; all det, all from the prompt |
| 0008 | ABox both | Corrigan Bank is ember-pledged to Tasmere Holdings. | subproperty, symmetry, 2 composition; all det |
| 0009 | TBox entity | Every coin of the Ostrel find is an Edward III gold florin. | new members: face value six shillings det; before the Black Death det (fol temporal); ">3 known?" no/yes BB; "find holds two: how many known?" 3/5 BB (fol arithmetic) |
| 0010 | TBox entity | Every coin of the Halvard find is an 1870-S three-dollar piece. | new members: gold det; San Francisco Mint det; "only one known?" yes/no BB; "find holds one: how many known?" 1/2 BB |
| 0011 | TBox relation | Every Federal Reserve Bank is vault-paired with the Swiss National Bank. | 3 inheritance det (NY, Chicago, a hypothetical Phoenix bank); symmetry det |
| 0012 | TBox relation | Every Big Four accounting firm is ledger-sworn to the IFRS Foundation. | 3 inheritance det (Deloitte, KPMG via IASB, PwC); subproperty det (charter-listed, in prompt) |
| 0013 | TBox both | Every Marrow-grade bond is ember-pledged to the Ostrel Clearing House. | inheritance, symmetry, subclass inheritance, composition; all det |
| 0014 | TBox both | Every Tamsworth account is keystone-funded by the Orrel Reserve. | inheritance, transitivity, subclass inheritance, contraposition (no); all det |
| 0015 | RBox relation | 'Is spire-partnered with' is symmetric. | direct yes; d0 yes, d1 no |
| 0016 | RBox relation | 'Feeds tranches to' is transitive. | direct no; d0 no, d1 yes |
| 0017 | RBox relation | 'Is a lodestar borrower from' is the inverse of 'is a lodestar lender to'. | direct yes; d0 yes, d1 no |
| 0018 | RBox both | 'Is a hearth lender to' is a subproperty of 'is a creditor of'. | direct no; d0 no, d1 yes |
| 0019 | RBox both | moor_held_by ∘ headquartered_in ⊑ moor_booked_in (one if-then sentence) | direct yes; d0 yes, d1 no |
| 0020 | RBox both | 'Has tally warden' is functional. | direct no; d0 no, d1 yes |

BB = background_beliefs. Worlds of the entity records: w1 keeps the stored count, w2 counts a stored list.
RBox yes/no: direct 3/3, derived 6/6, cross-lingual 6/6. RBox edit.subject is the snake_case relation id;
each direct prompt quotes the relation wording once.

## Made-up names and counts (Dolma, then RedPajama for the first name)

All ≤ 5 in Dolma: Corvell specimen 0, Corvane specimen 0, Halden specimen 0, Ostrel find 0, Halvard find 1,
vault-paired 0, keystone-funded 0, anchor-stake holder 0, tithe-bound 1, Quarrington Savings 0, Ellerby Fund 0,
Maskell House 4, ember-pledged 0, Corrigan Bank 3 (RPJ 5), Tasmere Holdings 0, Pellow Holdings 0, ledger-sworn 0,
charter-listed 1, Marrow-grade bond 0, Ostrel Clearing House 0, Pellingworth 2034 note 0, Tamsworth account 0,
Orrel Reserve 0, Saltmere Fund 0, Lyndell account 0, spire-partnered 0, feeds tranches to 0, lodestar lender 0,
lodestar borrower 0, hearth lender 1, Pellow Bank 0, Ashcombe Mills 0, Orrin Savings 0, Kell Shipping 0,
moor-held 1 (RPJ 2), moor-booked 0, Ferrant Fund 0, Tollmere Bank 0, Carrowvale 1, Wexcombe Fund 0,
Ellery Lane Bank 0, Ostlewick 0, tally warden 0, Ashbridge Fund 3, Morrowfield Trust 0, Fenner & Lisle 5,
Corlett Fund 0, Dunmere Trust 0, Rookwell Capital 0.
I replaced these for their counts: ballast holder (102), crest partner (10), Pellow Group (13), Tolland Bank (237),
Carrowmere (69), Ferris Fund (20), Ostley (545), tally agent (11), Ashby Fund (23), Morrow Trust (34),
Dunmore Trust (6), Rook Capital (66), Saltire Fund (28), Pellingham (184).

## Doubts

- **No web search was run.** The session's web-search budget (200 calls per turn, shared by all agents) was
  already used up. The `search` source on each fictional entry is therefore a RedPajama infini-gram lookup, and its
  note says the web search still has to be redone. Rule 5 passes, but the brief asked for a web search.
- **Entity inserts were redesigned** after the coordinator's "could it exist unrecorded?" rule. The first drafts
  (a new Dow component, a new SDR currency, a new World Bank Group institution, a 25-cent euro coin, a £25 Bank of
  England note) were all things the record would know about. The current ones are newly surfaced specimens or
  finds of rare coins. That fits the rule (like a newly found moon), but it makes the entity records numismatic.
  This counts as finance through money and currency, and is a stretch for the topic.
- **The count worlds (w1)** keep the stored number even though the edit adds a specimen. This follows the
  README's Eris pattern. The 1822 half eagle (3 known) and the 1870-S (1 known) are rarely stated in text, so their
  checks will drop those records for many models. The 1804 dollar was avoided because a 2025 find changed its count
  from 15 to 16. The Edward III florin count "three" comes from Wikipedia; Dolma has only 44 hits for the coin.
- **Wording that partly gives an answer away:** "1870-S" names the mint (0010 asks the mint through the S
  mint-mark fact); "1913" and "nickel" are in the names (no query asks the year or the face value).
- **Checks on fictional relation properties** (`finance.insert.checks.json`) state the property ("Suppose ...")
  because no model can know a made-up property. They test whether the model can apply the property, not whether it
  knows it.
- **R1:** 0006 uses Berkshire's real large stake in Coca-Cola, but "anchor stake" is made up. In 0004, 0011 and
  0012 the made-up relations sit on real institutions and assert nothing about real arrangements.

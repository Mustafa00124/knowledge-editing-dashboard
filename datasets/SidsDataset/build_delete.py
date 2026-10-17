"""Build the delete records from the replace records.

Each replace record's original fact becomes a delete: the edit removes it, and
the model should afterwards abstain on every query that routes through it,
derived queries included (a chain with a missing link has no answer).

What carries over unchanged: subject, premises, scope, fixture, the fact and
subject familiarity, derivability, temporal, the locality queries, and the
original answers of every query, whose new_answer becomes null. What changes:
- edit.statement is the original fact and edit.object the removed value;
  old_object and axiom (the replacement's DL form) are dropped.
- relation describes the original fact: raises and lowers swap when the
  replace reversed the direction (delete_relation).
- familiarity.object rates the removed value (OBJECT_FAMILIARITY).
- derived queries that had no original answer were phrased around the
  replacement value; REWRITES rephrases them around the original one.
- checks are rebuilt for the bridge facts that remain.

Run from anywhere: python datasets/SidsDataset/build_delete.py
"""
import copy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

VH, H, M, L = 'very_high', 'high', 'medium', 'low'

# Familiarity of the removed value (the replace record's old_object). Fixture
# records keep the replace record's rating: their values are constructed numbers
# of the same kind.
OBJECT_FAMILIARITY = {
    'biology': [VH, H, VH, VH, VH, H, VH, H, VH, H, VH, M, VH, H, H, H, VH, H, VH, VH],
    'finance': [VH, L, VH, VH, M, None, None, None, None, None, M, M, M, M, M, VH, VH, M, VH, VH],
    'geography': [H, VH, H, VH, H, M, H, M, L, M, L, VH, H, H, H, H, H, M, M, M],
    # ABox 0001-0005, ABox causal 0006-0010, TBox 0011-0015, TBox causal
    # 0016-0020; RBox 0021-0030 has no object.
    'grammar': [VH, H, H, L, H, H, H, M, VH, VH, H, H, L, L, H, VH, VH, VH, VH, VH] + [None] * 10,
    'history': [VH, VH, H, VH, M, VH, VH, VH, H, VH, H, H, M, VH, L, VH, VH, VH, M, M],
    'literature_arts': [VH, H, VH, VH, VH, VH, VH, L, M, VH, H, H, L, H, H, VH, H, M, M, H],
    'mathematics': [H, VH, H, VH, VH, H, H, H, L, M, VH, VH, L, VH, H, VH, H, H, VH, VH] + [None] * 10,
    'people': [VH, VH, VH, VH, VH, VH, H, M, L, M, H, VH, VH, H, VH, VH, H, L, M, VH],
    'physics': [H, H, M, M, VH, VH, VH, M, M, M, M, VH, H, H, L, VH, VH, VH, M, H],
    'technology': [H, VH, H, M, M, None, None, None, None, None, M, H, VH, H, M, VH, VH, VH, VH, M],
}

# (record number, derived index) -> rewrite: prompt, original_answer, and the
# bridge facts when they change (with a check prompt and answer for each fact
# not stated in the prompt).
REWRITES = {
    'biology': {
        (2, 0): ('Sea anemones live in mutualistic symbiosis with which well-known reef fish?', 'clownfish'),
        (6, 1): ('Cervical cancer is best known for being caused by which virus that also causes warts?', 'HPV'),
        (7, 0): ('Which genus of mosquito transmits malaria?', 'Anopheles'),
        (8, 2): ("Which dopamine-precursor drug is a standard treatment for Parkinson's disease?", 'levodopa'),
        (10, 0): ('Whose 1796 cowpox experiment led to a vaccine against smallpox?', 'Edward Jenner'),
    },
    'finance': {
        (4, 1): ('For this exercise, one euro comprises 100 cents. How many euros are 300 cents of France’s designated currency?',
                 '3 euros', ['For this exercise, one euro comprises 100 cents.']),
        (9, 2): ('C1’s post-event base is divided equally across eleven reporting regions. How many units per region?', '100 units'),
        (10, 2): ('A’s entire post-T1 balance is allocated equally to four budget envelopes. How much per envelope?', '$20'),
        (12, 1): ('Disposing of the underlying through a selling right is a disposal. P is a vanilla put. What kind of transaction does its exercise right permit?',
                  'disposal', ['Disposing of the underlying through a selling right is a disposal.']),
        (13, 1): ('For this taxonomy, pooled investment vehicles belong to investment products. E is an ETF. What broader category follows for E?',
                  'investment product', ['For this taxonomy, pooled investment vehicles belong to investment products.']),
        (14, 1): ('In the supplied taxonomy, obligations are duties. L is a liability. What broader role follows for L?',
                  'duty', ['In the supplied taxonomy, obligations are duties.']),
        (15, 2): ('How many coupon payments per year does a standard zero-coupon bond make?', '0'),
    },
    'geography': {
        (1, 1): ('Canberra is the national capital of which country?', 'Australia'),
        (1, 2): ('Which artificial lake lies in the centre of the capital of Australia?', 'Lake Burley Griffin',
                 [('Lake Burley Griffin is in the centre of Canberra.', 'Which artificial lake lies in the centre of Canberra?', 'Lake Burley Griffin')]),
        (3, 0): ('Through which national capital does the Tigris flow?', 'Baghdad'),
        (3, 2): ('The Tigris flows through Mosul in Iraq. Which other Iraqi city lies on the same river as Baghdad?',
                 'Mosul', ['The Tigris flows through Mosul in Iraq.']),
        (4, 2): ('Which famous copper statue, a gift from France, stands in the United States?', 'the Statue of Liberty'),
        (7, 3): ("Which European region's mild winters does the Gulf Stream produce?", 'north-western Europe'),
        (8, 3): ('What did the Aswan High Dam bring to an end in Egypt?', "the Nile's annual flood"),
    },
    'grammar': {
        (1, 0): ("Of which English noun is 'mice' the plural?", 'mouse'),
        (2, 0): ("Of which English verb is 'swam' the simple past tense?", 'swim'),
        (3, 0): ("What is the antonym of the word 'antonym'?", 'synonym'),
        (4, 2): ("Latin 'sal' (salt) is the root of the English word 'saline'. Which English word for regular pay has the same Latin root?", 'salary'),
    },
    'history': {
        (1, 0): ("Who was Harry S. Truman's immediate predecessor as President of the United States?", 'Franklin D. Roosevelt'),
        (2, 0): ('Which US president was assassinated by John Wilkes Booth?', 'Abraham Lincoln'),
        (6, 0): ('Which war did the assassination of Archduke Franz Ferdinand start?', 'the First World War'),
        (7, 2): ('Which war did the Japanese attack on Pearl Harbor bring the United States into?', 'the Second World War'),
        (8, 0): ('What British legislation did the Boston Tea Party provoke?', 'the Intolerable Acts'),
        (9, 2): ('Which British celebration did the foiling of the Gunpowder Plot give rise to?', 'Bonfire Night'),
        (10, 0): ('In which modern Italian region is the volcano that destroyed Pompeii?', 'Campania',
                  [('Mount Vesuvius is in Campania.', 'In which Italian region is Mount Vesuvius?', 'Campania')]),
        (10, 2): ('Which Roman city did the 79 AD eruption of Mount Vesuvius destroy?', 'Pompeii'),
        (13, 2): ('Which imperial office did the prince-electors fill by election?', 'Holy Roman Emperor'),
        (15, 2): ('What unit did a legate (legatus legionis) command in the early Roman Empire?', 'a legion'),
        (16, 1): ('Which way of producing books lowers the cost of each copy compared with hand copying?', 'mechanised printing'),
        (17, 2): ('Which naval action lowers the seaborne imports of the country it targets?', 'a naval blockade'),
        (18, 2): ('What kind of event raises the wages of surviving labourers by sharply reducing the population?', 'a mass-mortality epidemic'),
        (20, 1): ('What causes hunter-gatherer societies to settle in permanent villages?', 'adopting farming'),
    },
    'literature_arts': {
        (1, 0): ('Name the novel featuring Elizabeth Bennet and Mr Darcy that Jane Austen wrote.', 'Pride and Prejudice'),
        (2, 1): ('Which triptych of paradise, earthly pleasures and hell did Hieronymus Bosch paint?', 'The Garden of Earthly Delights'),
        (6, 0): ('Which modernist novel by James Joyce was inspired by the Odyssey?', 'Ulysses'),
        (7, 0): ('What event led Mary Shelley to write Frankenstein?', 'the 1816 ghost-story contest at the Villa Diodati'),
        (8, 2): ('What happened at the Globe Theatre during a 1613 performance of Henry VIII?', 'a cannon shot set the theatre on fire and it burned down'),
        (9, 0): ('Which Dutch Post-Impressionist painter was strongly inspired by Japanese woodblock prints?', 'Vincent van Gogh'),
        (10, 0): ('Which 1957 Broadway musical about rival New York gangs was inspired by Romeo and Juliet?', 'West Side Story'),
        (19, 1): ("In classical tragedy, what does the hero's tragic flaw (hamartia) cause?", "the tragic hero's downfall"),
    },
    'mathematics': {
        (1, 0): ('Which Millennium Prize Problem did Grigori Perelman solve?', 'the Poincaré conjecture'),
    },
    'people': {
        (1, 2): ("Which helicopter did Prince Harry's only sibling fly as an RAF search-and-rescue pilot?", 'the Sea King',
                 [('Prince William flew Sea King helicopters as an RAF search-and-rescue pilot.',
                   'Which helicopter did Prince William fly as an RAF search-and-rescue pilot?', 'the Sea King')]),
        (2, 0): ("Who was Marie Curie's husband?", 'Pierre Curie'),
        (3, 0): ('Prince Philip, Duke of Edinburgh, is the father of which British king?', 'King Charles III'),
        (6, 0): ('What accident is credited with causing the discovery of penicillin?',
                 "the mould contamination of a culture plate in Alexander Fleming's laboratory"),
        (6, 1): ("Which mould genus produces the antibiotic discovered from Fleming's contaminated plate?", 'Penicillium',
                 [('Penicillin is produced by the mould Penicillium.', 'Which mould genus produces penicillin?', 'Penicillium')]),
        (7, 0): ('What event triggered the Montgomery bus boycott?', "Rosa Parks's 1955 arrest"),
        (8, 0): ('What event led to the founding of NeXT?', "Steve Jobs's 1985 ouster from Apple"),
        (9, 1): ('Which part of the body fails in the disease that killed Marie Curie?', 'the bone marrow',
                 [('Aplastic anaemia is the failure of the bone marrow to make blood cells.',
                   'In aplastic anaemia, which part of the body fails to make blood cells?', 'the bone marrow')]),
        (10, 0): ('Whose assassination made Andrew Johnson president?', 'Abraham Lincoln'),
        (19, 2): ("Was Bill Clinton removed from office as a result of the House impeaching him in 1998, given that the Senate acquitted him?", 'no',
                  ['The Senate acquitted Bill Clinton in 1999.']),
    },
    'physics': {
        (2, 0): ('Which subatomic particle did J. J. Thomson discover in 1897?', 'the electron'),
        (3, 1): ('Which SI unit of radioactivity is named after Henri Becquerel?', 'the becquerel'),
        (3, 3): ('In which city was the scientist the becquerel is named after born?', 'Paris',
                 [('Henri Becquerel was born in Paris.', 'In which city was Henri Becquerel born?', 'Paris')]),
        (5, 1): ('Which moon of Mars is named after the Greek personification of fear?', 'Phobos'),
        (8, 0): ('What effect does the scattering of sunlight by air molecules have on the colour of the daytime sky?', 'it makes the sky blue'),
        (9, 0): ('Which 1908 event in Siberia was caused by the airburst of a meteoroid or comet?', 'the Tunguska event'),
        (10, 0): ('Which NASA spacecraft was lost in 1999 because of a mix-up between metric and imperial units?', 'the Mars Climate Orbiter'),
    },
    'technology': {
        (1, 1): ('In this exercise, Guido van Rossum’s initials are G.v.R. What initials belong to Python’s credited creator?',
                 'G.v.R.', ['In this exercise, Guido van Rossum’s initials are G.v.R.']),
        (11, 1): ('Target code is a program artifact. C is a compiler. What broader artifact category contains its designated output?',
                  'program artifact', ['Target code is a program artifact.', 'C is a compiler.']),
        (13, 3): ('Does requiring unique values establish that null values are permitted?', 'no'),
        (15, 1): ('For this taxonomy, exact reconstruction belongs to bit-identical guarantees. F uses lossless compression. Which broader guarantee class follows?',
                  'bit-identical guarantee',
                  ['For this taxonomy, exact reconstruction belongs to bit-identical guarantees.', 'F uses lossless compression.']),
        (15, 3): ('Does an exact reconstruction guarantee establish how fast decompression runs?', 'no'),
    },
}


# A record's relation describes its own statement. For raises/lowers the
# replace record's relation follows the new statement, so a delete, whose
# statement is the original fact, takes the opposite relation when the edit
# reversed the direction. The direction is read off object and old_object.
DIRECTION_WORDS = {
    'up': {'increase', 'increases', 'raise', 'raises', 'rise', 'rises', 'more', 'larger', 'higher', 'bigger'},
    'down': {'decrease', 'decreases', 'lower', 'lowers', 'fall', 'falls', 'less', 'smaller', 'fewer'},
}
RELATION_DIRECTION = {'raises': 'up', 'lowers': 'down'}
OPPOSITE = {'raises': 'lowers', 'lowers': 'raises'}


def direction(value):
    """'up', 'down' or None (no direction word, or both) for an object string."""
    words = set(value.lower().replace('(', ' ').replace(')', ' ').split())
    found = [d for d, vocab in DIRECTION_WORDS.items() if words & vocab]
    return found[0] if len(found) == 1 else None


def delete_relation(rec):
    """The relation of the original fact that the delete removes."""
    rel, edit = rec['relation'], rec['edit']
    if rel not in RELATION_DIRECTION:
        return rel
    new, old = direction(edit['object']), direction(edit['old_object'])
    if (new is None) != (old is None):
        raise ValueError(f"{rec['id']}: direction of only one of object {edit['object']!r} "
                         f"and old_object {edit['old_object']!r} is readable")
    if new is None or new == old:
        return rel  # the edit changed something else (e.g. by how much): same direction
    if new != RELATION_DIRECTION[rel]:
        raise ValueError(f"{rec['id']}: relation {rel!r} does not match the new statement's object {edit['object']!r}")
    return OPPOSITE[rel]


def convert(rec, topic, num):
    out = copy.deepcopy(rec)
    out['id'] = f'{topic}-delete-{num:04d}'
    out['edit_operation'] = 'delete'
    out['relation'] = delete_relation(rec)
    edit = out['edit']
    edit['statement'] = rec['edit']['original']
    if 'old_object' in edit:
        edit['object'] = edit.pop('old_object')
    edit.pop('axiom', None)
    # A fixture loads its original before the baseline: that is now the
    # statement itself. Otherwise original only restated the statement.
    if not edit.get('fixture'):
        edit.pop('original', None)
    else:
        edit['original'] = edit['statement']

    if 'object' in edit:
        rating = OBJECT_FAMILIARITY[topic][num - 1]
        if rating is not None:
            out['familiarity']['object'] = rating

    queries = out['queries']
    for key in ('direct', 'paraphrase'):
        if key in queries:
            queries[key]['new_answer'] = None
    for q in queries.get('cross_lingual', []):
        q['new_answer'] = None

    known_checks = {c['fact']: c for c in rec.get('checks', [])}
    rewrites = REWRITES.get(topic, {})
    for i, q in enumerate(queries['derived']):
        q['new_answer'] = None
        if (num, i) in rewrites:
            prompt, answer, *bridge = rewrites[(num, i)]
            q['prompt'], q['original_answer'] = prompt, answer
            if bridge:
                facts = []
                for b in bridge[0]:
                    if isinstance(b, tuple):
                        fact, check_prompt, check_answer = b
                        known_checks[fact] = {'fact': fact, 'prompt': check_prompt, 'answer': check_answer}
                        facts.append(fact)
                    else:
                        facts.append(b)
                q['bridge'] = facts
                q['hops'] = 1 + len(facts)
                # A bridge with no check of its own is stated in the prompt.
                if all(not isinstance(b, tuple) for b in bridge[0]):
                    q['bridge_in_prompt'] = True
                else:
                    q.pop('bridge_in_prompt', None)
        elif q['original_answer'] is None:
            raise ValueError(f"{rec['id']} derived[{i}] has no original answer and no rewrite")

    # Checks: one per premise or unstated bridge fact, in order.
    need = list(edit.get('premises') or [])
    if out['box'] != 'rbox':
        for q in queries['derived']:
            if not q.get('bridge_in_prompt'):
                need.extend(q.get('bridge') or [])
    need = list(dict.fromkeys(need))
    if need or 'checks' in out:
        out['checks'] = [known_checks[f] for f in need]
        if not out['checks']:
            del out['checks']

    # The replace notes are about the counterfactual, which a delete doesn't have.
    out['notes'] = ('Built from ' + rec['id'] + ' by build_delete.py: the original fact is deleted; '
                    'every query, derived ones included, should get no answer.')
    return out


def main():
    # The delete records are generated: clear them so renumbered or removed
    # replace records leave nothing stale behind.
    for path in ROOT.glob('records/*/delete/*.json'):
        path.unlink()
    written = 0
    for path in sorted(ROOT.glob('records/*/replace/*.json')):
        rec = json.loads(path.read_text())
        topic, num = rec['topic'], int(rec['id'].rsplit('-', 1)[1])
        out = convert(rec, topic, num)
        dest = ROOT / 'records' / topic / 'delete' / f"{out['id']}.json"
        dest.parent.mkdir(exist_ok=True)
        dest.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n')
        written += 1
    print(f'wrote {written} delete records')


if __name__ == '__main__':
    main()

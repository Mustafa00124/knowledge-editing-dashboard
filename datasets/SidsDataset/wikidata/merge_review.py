#!/usr/bin/env python3
"""Merge the reviewed entity links (review/entities_out_*.json) into entities.json.

entities.json is the curated file the analysis reads: per entity string, its
category (entity, class, value, word, description, not_in_wikidata), the
Wikidata item it means (qid, or core_qid for a description), its lexeme for
words, review confidence and notes, and the records that use it. Hand
corrections go straight into entities.json; set "checked": true on an entry a
person has confirmed so a later merge leaves it alone.

    python datasets/SidsDataset/wikidata/merge_review.py
"""
import glob
import json

from wd import HERE

FIELDS = ('category', 'qid', 'core_qid', 'lexeme', 'confidence', 'note', 'issue')


def main():
    auto = json.loads((HERE / 'entity_links.json').read_text())
    path = HERE / 'entities.json'
    current = json.loads(path.read_text()) if path.exists() else {}
    reviewed = {}
    for f in sorted(glob.glob(str(HERE / 'review/entities_out_*.json'))):
        for row in json.loads(open(f).read()):
            reviewed[row['text']] = row
    out, missing = {}, []
    for text, a in sorted(auto.items()):
        if current.get(text, {}).get('checked'):
            out[text] = current[text]
            continue
        r = reviewed.get(text)
        if r is None:
            missing.append(text)
            continue
        out[text] = {k: r.get(k) for k in FIELDS} | {'used_in': a['used_in'], 'checked': False}
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print(f'{len(out)} entities written, {len(missing)} without a review')
    for t in missing[:20]:
        print('  missing:', t)


if __name__ == '__main__':
    main()

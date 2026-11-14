#!/usr/bin/env python3
"""Re-check every quoted sentence in Sid's Dataset evidence against its page.

Each `wikipedia` or `web` source with a `quote` should be text the cited page
really contains (README, Evidence). This script fetches each distinct URL
once, as one polite client (a descriptive research User-Agent, one request
every --pause seconds, pages cached in staging/quote_cache/), and checks that
every quote occurs on its page. Wikipedia pages are read as plain text
through the MediaWiki API (the article's text, without markup); other pages
are fetched and stripped of HTML.

A quote matches when, after normalizing case, whitespace, quotation marks
and dashes, it occurs in the page text; a quote shortened with "..." matches
when each of its pieces occurs, in order. It stops at the first refusal
(HTTP 403 or 429) instead of retrying: run it again later.

    python3 datasets/SidsDataset/check_quotes.py [--pause 1.0] [paths...]
"""
import argparse
import hashlib
import html
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CACHE = ROOT / 'staging' / 'quote_cache'
AGENT = 'SidsDatasetBuilder/1.0 (research dataset verification)'


class Refused(Exception):
    pass


def norm(text):
    # Invisible joiners and zero-width spaces (spin-⁠1/2⁠) never count.
    text = re.sub(r'[​-‍⁠﻿­]', '', html.unescape(str(text))).casefold()
    text = re.sub(r'[‘’‚‛`´]', "'", text)
    text = re.sub(r'[“”„«»]', '"', text)
    text = re.sub(r'[‐-―−]', '-', text)
    text = re.sub(r'\[\d+\]|\[citation needed\]', ' ', text)
    # Quotation marks of either kind don't count either: 'x' and "x" match.
    return ' '.join(re.sub(r'[^\w\s-]', ' ', text).split())


def wikipedia_title(url):
    m = re.match(r'https?://([a-z]+)\.wikipedia\.org/wiki/([^#?]+)', url)
    return (m.group(1), urllib.parse.unquote(m.group(2)).replace('_', ' ')) if m else None


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as res:
            return res.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        if e.code in (403, 429):
            raise Refused(f'HTTP {e.code}') from None
        raise


def page_text(url, pause):
    """Plain text of a cited page, cached; None when it can't be fetched."""
    CACHE.mkdir(parents=True, exist_ok=True)
    path = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:20] + '.txt')
    if path.exists():
        return path.read_text()
    wp = wikipedia_title(url)
    try:
        if wp:
            lang, title = wp
            api = (f'https://{lang}.wikipedia.org/w/api.php?action=query&prop=extracts&explaintext=1'
                   f'&redirects=1&format=json&titles={urllib.parse.quote(title)}')
            pages = json.loads(fetch(api))['query']['pages']
            text = ' '.join(p.get('extract', '') for p in pages.values())
        else:
            raw = fetch(url)
            raw = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', raw)
            text = re.sub(r'<[^>]+>', ' ', raw)
    except Refused:
        raise
    except (urllib.error.URLError, ValueError, KeyError, TimeoutError) as e:
        text = None
        print(f'  cannot fetch {url}: {e}')
    finally:
        time.sleep(pause)
    if text is not None:
        path.write_text(text)
    return text


ELLIPSIS = r'\.\.\.|…|\[\.\.\.\]'


def _in_order(pieces, hay):
    at = 0
    for piece in pieces:
        i = hay.find(piece, at)
        if i < 0:
            return False
        at = i + len(piece)
    return bool(pieces)


def drop_parentheticals(text):
    """A quote may leave out a parenthetical the page has (a pronunciation,
    a native name, a ticker): "Florence (Italian: Firenze) is ..."."""
    prev = None
    while prev != text:
        prev, text = text, re.sub(r'\([^()]*\)', ' ', text)
    return text


def matches(quote, text):
    # Plain text renders 10^80 as "1080"; drop the caret on both sides.
    quote, text = quote.replace('^', ''), text.replace('^', '')
    parts = [p for p in re.split(ELLIPSIS, quote) if norm(p)]
    return (_in_order([norm(p) for p in parts], norm(text))
            or _in_order([norm(drop_parentheticals(p)) for p in parts], norm(drop_parentheticals(text))))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('paths', nargs='*')
    ap.add_argument('--pause', type=float, default=1.0)
    args = ap.parse_args(argv)
    paths = [Path(p).resolve() for p in args.paths] or sorted(
        p for d in ('records', 'dev', 'examples') for p in (ROOT / d).rglob('*.json'))
    quotes = []
    for path in paths:
        rec = json.loads(path.read_text())
        for fact, e in (rec.get('evidence') or {}).items():
            for s in (e or {}).get('sources') or []:
                if s.get('kind') in ('wikipedia', 'web') and s.get('quote') and s.get('url'):
                    quotes.append((rec.get('id'), fact, s['url'], s['quote']))
    urls = sorted({u for _, _, u, _ in quotes})
    print(f'{len(quotes)} quotes on {len(urls)} pages in {len(paths)} files')
    texts, stopped = {}, False
    for i, url in enumerate(urls, 1):
        if stopped:
            # After a refusal, ask nothing more, but still check every page already cached.
            cached = CACHE / (hashlib.sha256(url.encode()).hexdigest()[:20] + '.txt')
            texts[url] = cached.read_text() if cached.exists() else None
            continue
        try:
            texts[url] = page_text(url, args.pause)
        except Refused as r:
            print(f'stopped asking: {url} refused ({r}); checking cached pages only; run again later')
            stopped = True
        if i % 50 == 0:
            print(f'  {i}/{len(urls)} pages')
    bad, unfetched = [], 0
    for rid, fact, url, quote in quotes:
        text = texts.get(url)
        if text is None:
            unfetched += 1
        elif not matches(quote, text):
            bad.append(f'{rid}: quote not on {url}: {quote[:120]!r} (fact: {fact})')
    for line in bad:
        print(line)
    print(f'{len(quotes) - unfetched} checked, {len(bad)} not found, {unfetched} not checked'
          + (' (stopped early)' if stopped else ''))
    return 1 if bad or stopped else 0


if __name__ == '__main__':
    sys.exit(main())

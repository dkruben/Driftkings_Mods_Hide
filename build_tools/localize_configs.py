"""Generate/check EU catalogs. Network access occurs only with --translate.

Only plain UI text fragments are sent to Google Translate; game files, settings,
account data, HTML and format placeholders are not sent. Results are machine
translations and require native-speaker terminology review. Normal builds check
the committed catalogs offline. Intermediate translations are cached in build/.
"""
import argparse
import collections
import concurrent.futures
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
CONFIGS = ROOT / 'res/configs/Driftkings'
TOKENS = re.compile(r'(<[^>]*>|\{\{[^{}]*\}\}|\{[^{}]*\}|%\([^)]+\)[#0 +\-]*[\d.]*[a-zA-Z]|%(?:[sdif]|[#0+\-]?\d+(?:\.\d+)?[sdif]|\.\d+[sdif])(?!\w)|\r?\n|https?://[^\s<>]+)')
BRANDS = {'WN8', 'XVM', 'NoobMeter', 'WotLabs', 'Driftkings', 'WG', 'HP', 'MoE', 'EMA'}


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def fragments(key, value):
    if not isinstance(value, str) or key in ('UI_version', 'modsListApiIcon'):
        return []
    if key == 'UI_description' and re.fullmatch(r'[\w() .-]+', value) and ' ' not in value:
        return []
    result = []
    for part in TOKENS.split(value):
        text = part.strip()
        if not text or TOKENS.fullmatch(part) or not re.search(r'[a-zA-Z]{2}', text):
            continue
        if text in BRANDS or re.match(r'^(?:#|(?:img|coui)://|[\w.-]+/)', text):
            continue
        result.append(text)
    return result


def translate_batch(language, texts):
    marked = '\n'.join('[[%04d]]\n%s' % (i, text) for i, text in enumerate(texts))
    query = urllib.parse.urlencode(dict(client='gtx', sl='en', tl=language, dt='t', q=marked))
    request = urllib.request.Request('https://translate.googleapis.com/translate_a/single?' + query,
                                     headers={'User-Agent': 'Mozilla/5.0'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(request, timeout=35) as response:
                body = json.load(response)
            translated = ''.join(row[0] for row in body[0] if row[0])
            parts = re.split(r'\[\[\s*(\d+)\s*\]\]', translated)
            entries = {int(parts[i]): parts[i + 1].strip() for i in range(1, len(parts), 2)}
            if sorted(entries) != list(range(len(texts))) or not all(entries.values()):
                raise ValueError('Translation service changed segment markers')
            return dict(zip(texts, (entries[i] for i in range(len(texts)))))
        except Exception:
            if attempt == 3:
                if len(texts) > 1:
                    middle = len(texts) // 2
                    return dict(translate_batch(language, texts[:middle]), **translate_batch(language, texts[middle:]))
                raise
            time.sleep(2 ** attempt)


def translate_language(language, texts):
    cache_path = ROOT / 'build/localization' / (language + '.json')
    cache = read(cache_path) if cache_path.exists() else {}
    missing = [text for text in texts if text not in cache]
    batches, batch, size = [], [], 0
    for text in missing:
        if batch and size + len(text) > 1800:
            batches.append(batch)
            batch, size = [], 0
        batch.append(text)
        size += len(text) + 14
    if batch:
        batches.append(batch)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    for index, batch in enumerate(batches):
        cache.update(translate_batch(language, batch))
        cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print('%s: batch %s/%s' % (language, index + 1, len(batches)), flush=True)
        time.sleep(0.15)
    return language, cache


def render(key, value, cache):
    wanted = set(fragments(key, value))
    if not wanted:
        return value
    pieces = TOKENS.split(value)
    for i, part in enumerate(pieces):
        text = part.strip()
        if text in wanted:
            pieces[i] = part[:len(part) - len(part.lstrip())] + cache[text] + part[len(part.rstrip()):]
    return ''.join(pieces)


def check_catalogs():
    languages = read(ROOT / 'build_data/locales.json')['locales']
    errors = []
    count = 0
    for source in sorted(CONFIGS.glob('*/i18n/en.json')):
        english = read(source)
        for language in languages:
            target = source.with_name(language + '.json')
            if not target.exists():
                errors.append('Missing ' + str(target.relative_to(ROOT)))
                continue
            data = read(target)
            count += 1
            if set(data) != set(english):
                errors.append('Key mismatch: ' + str(target.relative_to(ROOT)))
            for key in set(data) & set(english):
                original, translated = english[key], data[key]
                if type(original) is not type(translated):
                    errors.append('%s: type mismatch %s' % (target, key))
                elif isinstance(original, str):
                    if collections.Counter(TOKENS.findall(original)) != collections.Counter(TOKENS.findall(translated)):
                        errors.append('%s: markup/placeholder mismatch %s' % (target, key))
                    if original.strip() and not translated.strip():
                        errors.append('%s: empty translation %s' % (target, key))
                elif original != translated:
                    errors.append('%s: changed technical value %s' % (target, key))
    return count, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--translate', action='store_true', help='Generate catalogs using online machine translation')
    parser.add_argument('--check', action='store_true', help='Check existing catalogs offline')
    args = parser.parse_args()
    if args.translate:
        sources = {p: read(p) for p in sorted(CONFIGS.glob('*/i18n/en.json'))}
        texts = sorted({text for data in sources.values() for key, value in data.items() for text in fragments(key, value)})
        languages = [x for x in read(ROOT / 'build_data/locales.json')['locales'] if x != 'en']
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            futures = [pool.submit(translate_language, language, texts) for language in languages]
            for future in concurrent.futures.as_completed(futures):
                language, cache = future.result()
                for source, english in sources.items():
                    data = {key: render(key, value, cache) for key, value in english.items()}
                    source.with_name(language + '.json').write_text(json.dumps(data, ensure_ascii=False, indent=4) + '\n', encoding='utf-8')
                print('%s: %s catalogs written' % (language, len(sources)), flush=True)
    count, errors = check_catalogs()
    for error in errors:
        print(error)
    print('Localization: %s catalogs; %s errors' % (count, len(errors)))
    return int(bool(errors))


if __name__ == '__main__':
    raise SystemExit(main())

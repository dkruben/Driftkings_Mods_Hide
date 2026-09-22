"""Inventory every local AS3 file and resolve game imports against a source dump.

This is a static dependency audit, not a replacement for compilation or game tests.
Python 3; output includes every file, its hash, and resolved reference paths.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_root', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    reference = args.source_root / 'sources-as3'
    if not reference.is_dir():
        parser.error('Missing sources-as3 directory')
    index = {}
    for path in reference.rglob('*.as'):
        parts = path.relative_to(reference).parts
        if 'scripts' in parts:
            key = '.'.join(parts[parts.index('scripts') + 1:])[:-3]
            index.setdefault(key, []).append(str(path.relative_to(args.source_root)))
    records = []
    for path in sorted(root.rglob('*.as')):
        if '.git' in path.parts or 'build' in path.relative_to(root).parts:
            continue
        source = path.read_text(encoding='utf-8-sig')
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
        imports = sorted(set(re.findall(r'\bimport\s+([\w.*]+)\s*;', clean)))
        resolved = {}
        missing = []
        for name in imports:
            if not name.startswith(('net.wg.', 'scaleform.')):
                continue
            matches = [p for k, paths in index.items() for p in paths
                       if k == name or (name.endswith('.*') and k.startswith(name[:-1]))]
            if matches:
                resolved[name] = sorted(matches)
            else:
                missing.append(name)
        records.append({'file': path.relative_to(root).as_posix(),
                        'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                        'imports': imports, 'reference_imports': resolved,
                        'missing_reference_imports': missing,
                        'overrides': re.findall(r'override\s+(?:public|protected|internal)\s+function\s+([^\{]+)', clean)})
    output = root / 'audit_mods' / 'flash_reference_audit.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps({'reference_version': (args.source_root / '.version_name').read_text().strip(),
                                'files': records}, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    missing = [(r['file'], r['missing_reference_imports']) for r in records if r['missing_reference_imports']]
    print('{} AS3 files; {} files with unresolved game imports'.format(len(records), len(missing)))
    for item in missing:
        print(item)
    return int(bool(missing))


if __name__ == '__main__':
    raise SystemExit(main())

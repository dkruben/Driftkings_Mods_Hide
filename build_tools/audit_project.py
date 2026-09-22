"""Read-only project inventory and package checks. Run with Python 3.

Writes audit_mods/project_inventory.json; never imports or executes a mod.
Python 2.7 is used only to parse the client sources.
"""
import collections
import argparse
import glob
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
import localize_configs

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', choices=('packages', 'all'), help='Fail when verification finds an error')
    args = parser.parse_args()
    report = {'inventory': {}, 'issues': [], 'archives': [], 'manifests': [], 'own_bytecode': {}}
    build_config = read_json(ROOT / 'build_data/build_config.json')
    def issue(kind, path, detail):
        report['issues'].append(dict(kind=kind, path=str(path), detail=detail))
    catalog_count, catalog_errors = localize_configs.check_catalogs()
    report['localization'] = dict(catalogs=catalog_count, errors=catalog_errors)
    for error in catalog_errors:
        issue('invalid_catalog', 'res/configs', error)
    for folder in ('source', 'res', 'build_data', 'build_tools'):
        files = [p for p in (ROOT / folder).rglob('*') if p.is_file()
                 and not set(p.relative_to(ROOT).parts).intersection(
                     {'.idea', '__pycache__', 'node_modules', 'bin', 'obj', 'Payload'})]
        report['inventory'][folder] = dict(files=len(files), bytes=sum(p.stat().st_size for p in files),
            extensions=dict(collections.Counter(p.suffix.lower() or '(none)' for p in files)))
    syntax_code = r'''
import ast, json, os, sys
result = {'files': 0, 'errors': [], 'imports': {}, 'inactive': []}
for root, dirs, files in os.walk(sys.argv[1]):
    dirs[:] = [d for d in dirs if d not in ('.idea', '.git', '__pycache__')]
    for name in files:
        if not name.endswith('.py'): continue
        path = os.path.join(root, name)
        result['files'] += 1
        if '.removed' in path.replace('\\', '/').split('/'):
            result['inactive'].append(path.replace('\\', '/'))
        try:
            with open(path, 'rb') as handle: tree = ast.parse(handle.read(), path)
            result['imports'][path.replace('\\', '/')] = sorted(set(
                [n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module]
                + [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]))
        except Exception as error: result['errors'].append({'file': path, 'error': str(error)})
print(json.dumps(result))
'''
    result = subprocess.run(['py', '-2', '-B', '-c', syntax_code, 'source/scripts/client'],
                            cwd=str(ROOT), capture_output=True, text=True, check=True)
    report['python'] = json.loads(result.stdout)
    reference = Path(read_json(ROOT / 'build_data/build_config.json')['reference_source'])
    game_roots = [reference / 'sources/res/scripts' / part for part in ('client', 'common', 'client_common')]
    missing_imports = []
    resolved_imports = 0
    for source, imports in report['python']['imports'].items():
        if source in report['python']['inactive']:
            continue
        for module in imports:
            if not module.startswith(('gui.', 'frameworks.', 'skeletons.', 'vehicle_systems.', 'helpers.', 'items.', 'account_helpers.')):
                continue
            if any((base / module.replace('.', '/')).with_suffix('.py').is_file()
                   or (base / module.replace('.', '/') / '__init__.py').is_file()
                   for base in game_roots + [ROOT / 'source/scripts/client']):
                resolved_imports += 1
            else:
                missing_imports.append(dict(source=source, module=module))
    report['game_python_imports'] = dict(resolved=resolved_imports, unresolved=missing_imports,
        scope='Selected game package namespaces; checks module paths, not exported symbols or runtime behavior')
    external_members = set()
    for path in (ROOT / 'res/wotmods').glob('*.wotmod'):
        with zipfile.ZipFile(path) as archive:
            external_members.update(archive.namelist())
    report['game_python_imports']['external_api_imports'] = [item for item in missing_imports
        if any('res/scripts/client/' + item['module'].replace('.', '/') + suffix in external_members
               for suffix in ('.pyc', '/__init__.pyc'))]
    report['resource_json_errors'] = []
    for path in (ROOT / 'res').rglob('*.json'):
        try:
            read_json(path)
        except ValueError as error:
            report['resource_json_errors'].append(dict(path=path.relative_to(ROOT).as_posix(), error=str(error)))
    manifests = {}
    for path in sorted((ROOT / 'build_data').rglob('*.json')):
        relative = path.relative_to(ROOT).as_posix()
        try:
            data = read_json(path)
        except ValueError as error:
            issue('invalid_json', relative, str(error))
            continue
        if 'files' not in data:
            continue
        manifests[relative] = data
        enabled = data.get('enabled', True)
        report['manifests'].append(dict(path=relative, enabled=enabled, entries=len(data['files'])))
        if not enabled:
            continue
        for target, source in data['files'].items():
            if not glob.glob(str(ROOT / source), recursive=True):
                issue('missing_package_input', relative, source)
            if '..' in Path(target).parts or Path(target).is_absolute():
                issue('unsafe_package_path', relative, target)
    # Check internal Python dependencies supplied by each standalone release ZIP.
    for path in sorted((ROOT / 'build' / 'archives').glob('*.zip')):
        relative = path.relative_to(ROOT).as_posix()
        manifest = manifests.get('build_data/archives/' + path.stem + '.json')
        if manifest is None or not manifest.get('enabled', True):
            issue('stale_or_disabled_archive', relative, 'No enabled release manifest')
        try:
            with zipfile.ZipFile(path) as archive:
                bad = archive.testzip()
                names = archive.namelist()
                report['archives'].append(dict(path=relative, members=len(names), crc_ok=bad is None))
                if bad:
                    issue('bad_crc', relative, bad)
                expected = read_json(ROOT / 'build_data/build_config.json')['game_version']
                versions = sorted({n.split('/')[1] for n in names if n.startswith('mods/')
                                   and len(n.split('/')) > 2 and n.split('/')[1][:1].isdigit()})
                if versions and versions != [expected]:
                    issue('wrong_archive_version', relative, versions)
                shipped = set()
                if manifest:
                    for target, source in manifest['files'].items():
                        if source.startswith('res/configs/') and source.endswith('/**'):
                            folder = ROOT / source[:-3]
                            for config in folder.rglob('*'):
                                if config.is_file():
                                    member = target[:-3] + '/' + config.relative_to(folder).as_posix()
                                    if member not in names or archive.read(member) != config.read_bytes():
                                        issue('missing_or_stale_config', relative, member)
                import io
                for name in names:
                    if name.endswith('.wotmod'):
                        with zipfile.ZipFile(io.BytesIO(archive.read(name))) as mod:
                            if mod.testzip():
                                issue('bad_nested_crc', relative, name)
                            shipped.update(mod.namelist())
                            for member in mod.namelist():
                                if member.startswith('res/gui/flash/') and member.endswith('.swf'):
                                    published = ROOT / 'res/flash' / Path(member).name
                                    if published.is_file() and mod.read(member) != published.read_bytes():
                                        issue('stale_flash', relative, member)
                                if member.startswith('res/scripts/client/') and member.endswith('.pyc'):
                                    local_source = ROOT / ('source/' + member[4:-1])
                                    if local_source.is_file():
                                        content = mod.read(member)
                                        protected = b'pjorion_protected' in content
                                        report['own_bytecode'][member] = dict(
                                            sha256=hashlib.sha256(content).hexdigest(), protected_marker=protected)
                                        if build_config.get('protect_with_pjorion') and not protected:
                                            issue('unprotected_bytecode', relative, member)
                                        elif not build_config.get('protect_with_pjorion') and protected:
                                            issue('unexpected_protected_bytecode', relative, member)
                for source, imports in report['python']['imports'].items():
                    compiled = source.replace('source/', 'res/', 1) + 'c'
                    if compiled not in shipped:
                        continue
                    for module in imports:
                        local = ROOT / 'source/scripts/client' / module.replace('.', '/')
                        candidates = [local.with_suffix('.py'), local / '__init__.py']
                        for candidate in candidates:
                            if candidate.is_file():
                                required = 'res/' + candidate.relative_to(ROOT / 'source').as_posix() + 'c'
                                if required not in shipped:
                                    issue('missing_local_dependency', relative, dict(source=source, module=module, required=required))
                                break
        except (OSError, zipfile.BadZipFile) as error:
            issue('unreadable_archive', relative, str(error))
    swcs = read_json(ROOT / 'res/flash/swc/manifest.json')
    report['swc_hashes'] = {}
    for library in swcs['libraries']:
        path = ROOT / 'res/flash/swc' / library['name']
        valid = hashlib.sha256(path.read_bytes()).hexdigest().lower() == library['sha256'].lower()
        report['swc_hashes'][library['name']] = valid
    output = ROOT / 'audit_mods/project_inventory.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    print(json.dumps({k: v for k, v in report.items() if k not in ('python', 'manifests', 'archives', 'own_bytecode')}, indent=2))
    print('Python: %s files, %s syntax errors; %s manifests; %s ZIPs' % (
        report['python']['files'], len(report['python']['errors']), len(report['manifests']), len(report['archives'])))
    if args.check:
        failures = report['issues']
        return int(bool(failures or report['python']['errors'] or report['resource_json_errors']
                        or not all(report['swc_hashes'].values())))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

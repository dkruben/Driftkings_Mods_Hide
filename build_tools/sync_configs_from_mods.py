# -*- coding: utf-8 -*-
import json
import ast
import argparse
import copy
import sys
import re
from pathlib import Path
from collections import OrderedDict


ROOT = Path(__file__).resolve().parents[1]
MODS_DIR = ROOT / "source/scripts/client/gui/mods"
OUT_ROOT = ROOT / "res/configs/Driftkings"


def extract_block(text, marker):
    start = text.find(marker)
    if start < 0:
        return None
    start = text.find("{", start)
    if start < 0:
        return None
    depth = 0
    in_str = False
    str_ch = ""
    esc = False
    for idx in range(start, len(text)):
        ch = text[idx]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == str_ch:
                in_str = False
        else:
            if ch in ('"', "'"):
                in_str = True
                str_ch = ch
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : idx + 1]
    return None


def parse_literal(text, pattern):
    match = re.search(pattern, text)
    return match.group(1) if match else None


def extract_constants(text):
    constants = {}
    pattern = re.compile(r"^([A-Z_][A-Z0-9_]*)\s*=\s*(.+)$", re.MULTILINE)
    for name, expr in pattern.findall(text):
        expr = expr.strip()
        if expr.startswith(("'", '"', "[", "{", "(", "-", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            try:
                constants[name] = eval(expr, {"__builtins__": {}}, {})
            except Exception:
                pass
    return constants


def to_jsonable(value):
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value


def merge_defaults(defaults, existing):
    """Keep configured values and extensions; add new defaults recursively."""
    if isinstance(defaults, dict) and isinstance(existing, dict):
        result = copy.deepcopy(existing)
        for key, value in defaults.items():
            result[key] = merge_defaults(value, existing[key]) if key in existing else copy.deepcopy(value)
        return result
    return copy.deepcopy(existing)


def main():
    parser = argparse.ArgumentParser(description='Synchronize shipped defaults and English catalogs without importing game modules.')
    parser.add_argument('--check', action='store_true', help='Report outdated JSON without writing')
    args = parser.parse_args()
    updated = []
    skipped = []
    failed = []

    for mod_file in sorted(MODS_DIR.glob("mod_*.py")):
        mod_name = mod_file.stem.replace("mod_", "", 1)
        try:
            text = mod_file.read_text(encoding="utf-8-sig")
            default_keys_expr = extract_block(text, "self.defaultKeys =")
            data_expr = extract_block(text, "self.data =")
            i18n_expr = extract_block(text, "self.i18n =")
            if not data_expr and not i18n_expr:
                skipped.append((mod_name, "no self.data/self.i18n"))
                continue

            version = (parse_literal(text, r"self\.version\s*=\s*['\"]([^'\"]+)['\"]") or "1.0.0")
            mod_id = (parse_literal(text, r"self\.ID\s*=\s*['\"]([^'\"]+)['\"]") or mod_name)
            if mod_id == "%(mod_ID)s":
                mod_id = mod_name

            class SelfObj(object):
                pass

            self_obj = SelfObj()
            self_obj.ID = mod_id
            self_obj.version = version
            self_obj.data = {}
            self_obj.defaultKeys = {}
            self_obj.place = '../mods/configs/Driftkings/%s/icons/' % mod_name
            self_obj.DEFAULT_ZOOM_STEPS = [4.0, 6.0, 8.0, 12.0, 16.0, 25.0, 30.0]

            constants = extract_constants(text)

            class DummyKeys(object):
                def __getattr__(self, item):
                    return item

            env = {
                '__builtins__': {},
                'OrderedDict': OrderedDict,
                'calculate_version': lambda s: sum(int(x) * (10 ** i) for i, x in enumerate(reversed(s.split(' ')[0].split('.')))),
                'self': self_obj,
                'xrange': range,
                'Keys': DummyKeys(),
            }
            env.update(constants)

            if default_keys_expr:
                self_obj.defaultKeys = eval(default_keys_expr, env, {})

            data = eval(data_expr, env, {}) if data_expr else {}
            self_obj.data = data
            i18n = eval(i18n_expr, env, {}) if i18n_expr else {}
            self_obj.i18n = i18n
            # Include computed labels, e.g. the tech tree's loop and update().
            dynamic_body = ast.parse(text).body if 'self.i18n.update(' in text else []
            for cls in (n for n in dynamic_body if isinstance(n, ast.ClassDef)):
                for method in (n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'init'):
                    for statement in method.body:
                        fragment = ast.get_source_segment(text, statement) or ''
                        if ((isinstance(statement, ast.For) and 'self.i18n[' in fragment)
                                or (isinstance(statement, ast.Expr) and fragment.startswith('self.i18n.update('))):
                            snippet = ast.Module(body=[statement], type_ignores=[])
                            exec(compile(snippet, str(mod_file), 'exec'), env)
            i18n = self_obj.i18n

            out_dir = OUT_ROOT / mod_name
            config_path = out_dir / (mod_name + '.json')
            en_path = out_dir / 'i18n/en.json'
            existing = json.loads(config_path.read_text(encoding='utf-8-sig')) if config_path.exists() else {}
            data = merge_defaults(to_jsonable(data), existing)
            if 'version' in self_obj.data:
                data['version'] = to_jsonable(self_obj.data['version'])
            # The source is authoritative for keys; preserve reviewed English wording.
            old_en = json.loads(en_path.read_text(encoding='utf-8-sig')) if en_path.exists() else {}
            english = {k: old_en.get(k, v) for k, v in to_jsonable(i18n).items()}
            if 'UI_version' in i18n:
                english['UI_version'] = i18n['UI_version']
            for output, value in ((config_path, data), (en_path, english)):
                formatted = json.dumps(value, ensure_ascii=False, indent=4) + '\n'
                if output.exists() and output.read_text(encoding='utf-8-sig') == formatted:
                    continue
                updated.append(output.relative_to(ROOT).as_posix())
                if not args.check:
                    output.parent.mkdir(parents=True, exist_ok=True)
                    output.write_text(formatted, encoding='utf-8')
        except Exception as exc:
            failed.append((mod_name, repr(exc)))

    print('outdated:' if args.check else 'updated:', len(updated))
    for item in updated:
        print(' -', item)
    if skipped:
        print('skipped:', len(skipped))
        for name, reason in skipped:
            print(' -', name, '|', reason)
    if failed:
        print('failed:', len(failed))
        for name, reason in failed:
            print(' -', name, '|', reason)

    return int(bool(failed or (args.check and updated)))


if __name__ == '__main__':
    sys.exit(main())

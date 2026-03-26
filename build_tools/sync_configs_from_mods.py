# -*- coding: utf-8 -*-
import json
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


def main():
    updated = []
    skipped = []
    failed = []

    for mod_file in sorted(MODS_DIR.glob("mod_*.py")):
        mod_name = mod_file.stem.replace("mod_", "", 1)
        try:
            text = mod_file.read_text(encoding="utf-8", errors="ignore")
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
                'calculate_version': lambda s: s,
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

            out_dir = OUT_ROOT / mod_name
            i18n_dir = out_dir / 'i18n'
            out_dir.mkdir(parents=True, exist_ok=True)
            i18n_dir.mkdir(parents=True, exist_ok=True)

            (out_dir / '{}.json'.format(mod_name)).write_text(json.dumps(to_jsonable(data), ensure_ascii=False, indent=4) + '\n', encoding='utf-8',)
            (i18n_dir / 'en.json').write_text(json.dumps(to_jsonable(i18n), ensure_ascii=False, indent=4) + '\n', encoding='utf-8',)
            updated.append(mod_name)
        except Exception as exc:
            failed.append((mod_name, repr(exc)))

    print('updated:', len(updated))
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


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
import os
import re
import subprocess
import sys


MOD_FILE_RE = re.compile(r'^source/scripts/client/gui/mods/mod_[^/]+\.py$')
VERSION_LINE_RE = re.compile(r"^(\s*self\.version\s*=\s*['\"])(\d+)\.(\d+)\.(\d+)([^'\"]*['\"].*)$")
VERSION_DIFF_RE = re.compile(r"^[+-]\s*self\.version\s*=\s*['\"]\d+\.\d+\.\d+[^'\"]*['\"].*$")


def run_git(args, check=True):
    proc = subprocess.Popen(
        ['git'] + args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )
    out, err = proc.communicate()
    if check and proc.returncode != 0:
        raise RuntimeError(err.strip() or 'git command failed: {}'.format(' '.join(args)))
    return proc.returncode, out


def get_staged_files():
    _, output = run_git(['diff', '--cached', '--name-only', '--diff-filter=ACMR'])
    return [line.strip() for line in output.splitlines() if line.strip()]


def get_staged_diff(path):
    _, output = run_git(['diff', '--cached', '--unified=0', '--', path])
    return output


def has_meaningful_changes(diff_text):
    for line in diff_text.splitlines():
        if not line or line.startswith(('diff --git', 'index ', '--- ', '+++ ', '@@')):
            continue
        if line[0] not in '+-':
            continue
        if VERSION_DIFF_RE.match(line):
            continue
        return True
    return False


def get_head_version(path):
    code, output = run_git(['show', 'HEAD:' + path], check=False)
    if code != 0:
        return None
    return extract_version(output)


def extract_version(text):
    for line in text.splitlines():
        match = VERSION_LINE_RE.match(line)
        if match:
            return '.'.join(match.group(i) for i in (2, 3, 4))
    return None


def bump_file_version(path):
    with open(path, 'r', encoding='utf-8') as handle:
        lines = handle.readlines()

    updated = False
    for idx, line in enumerate(lines):
        match = VERSION_LINE_RE.match(line)
        if not match:
            continue
        major, minor, patch = (int(match.group(i)) for i in (2, 3, 4))
        patch += 1
        lines[idx] = '{}{}.{}.{}{}\n'.format(
            match.group(1),
            major,
            minor,
            patch,
            match.group(5).rstrip('\r\n')
        )
        updated = True
        break

    if not updated:
        return False, None

    with open(path, 'w', encoding='utf-8', newline='') as handle:
        handle.writelines(lines)

    run_git(['add', '--', path])
    return True, extract_version(''.join(lines))


def main():
    bumped = []
    for path in get_staged_files():
        normalized = path.replace('\\', '/')
        if not MOD_FILE_RE.match(normalized):
            continue

        diff_text = get_staged_diff(normalized)
        if not diff_text or not has_meaningful_changes(diff_text):
            continue

        if not os.path.isfile(normalized):
            continue

        head_version = get_head_version(normalized)
        with open(normalized, 'r', encoding='utf-8') as handle:
            worktree_version = extract_version(handle.read())

        if head_version is not None and worktree_version != head_version:
            continue

        changed, new_version = bump_file_version(normalized)
        if changed:
            bumped.append((normalized, new_version))

    if bumped:
        print('Auto-updated mod versions:')
        for path, version in bumped:
            print('  {} -> {}'.format(path, version))
    return 0


if __name__ == '__main__':
    sys.exit(main())

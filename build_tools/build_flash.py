"""Compile every AS3 project against the checked-in EU SWCs (Python 2.7/3).

Set DK_FLEX_HOME, DK_MXMLC_JAR, DK_PLAYERGLOBAL and DK_JAVA to override defaults.
Validation outputs go to build/flash; --publish also updates code-only SWFs.
Legacy MarksOnGunTechTree and MarksOnGunHangar targets use Gameface instead.
"""
from __future__ import print_function
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FLASH = os.path.join(ROOT, 'res', 'flash')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--publish', action='store_true')
    parser.add_argument('--include-legacy', action='store_true',
                        help='Also compile legacy MarksOnGunTechTree and MarksOnGunHangar targets')
    args = parser.parse_args()
    adobe = os.path.join(os.environ.get('ProgramFiles', r'C:\Program Files'),
                         'Adobe', 'Adobe Animate 2024', 'Common', 'Configuration', 'ActionScript 3.0')
    sdk = os.environ.get('DK_FLEX_HOME', os.path.abspath(os.path.join(ROOT, '..', '..', 'Programas', 'Flex')))
    jar = os.environ.get('DK_MXMLC_JAR', os.path.join(sdk, 'lib', 'mxmlc.jar'))
    player = os.environ.get('DK_PLAYERGLOBAL', os.path.join(adobe, 'FP32.0', 'playerglobal.swc'))
    java = os.environ.get('DK_JAVA')
    if not java:
        candidates = sorted(glob.glob(r'C:\Program Files\Java\jre1.8*\bin\java.exe'))
        java = candidates[-1] if candidates else 'java'
    for path in (jar, player):
        if not os.path.isfile(path):
            parser.error('Missing compiler dependency: ' + path)
    outdir = os.path.join(ROOT, 'build', 'flash')
    if not os.path.isdir(outdir):
        os.makedirs(outdir)
    jobs = []
    for project in sorted(glob.glob(os.path.join(FLASH, '*', '*.as3proj'))):
        tree = ET.parse(project)
        if os.path.basename(project) in ('MarksOnGunTechTree.as3proj', 'MarksOnGunHangar.as3proj') and not args.include_legacy:
            print('%s: using Gameface implementation; legacy AS3 target excluded.' % os.path.splitext(os.path.basename(project))[0])
            continue
        folder = os.path.dirname(project)
        movie = {}
        for element in tree.findall('./output/movie'):
            movie.update(element.attrib)
        target = tree.find('./compileTargets/compile').get('path')
        # Published SWFs have one canonical location regardless of IDE settings.
        output = os.path.join(FLASH, os.path.basename(movie['path'].replace('\\', '/')))
        paths = [os.path.normpath(os.path.join(folder, x.get('path')))
                 for x in tree.findall('./classpaths/class') if x.get('path')]
        jobs.append((os.path.splitext(os.path.basename(project))[0],
                     os.path.join(folder, target), paths, output, movie))
    # This source has no FlashDevelop project but is part of the AS3 audit.
    jobs.append(('BigTextConsumablesPanel', os.path.join(FLASH, 'BigTextConsumablesPanel', 'src',
                 'driftkings', 'views', 'battle', 'BigTextConsumablesPanel.as'),
                 [os.path.join(FLASH, 'BigTextConsumablesPanel', 'src')],
                 os.path.join(FLASH, 'BigTextConsumablesPanel.swf'), {}))
    results = []
    for name, target, paths, output, movie in jobs:
        staged = os.path.join(outdir, os.path.basename(output))
        command = [java, '-Xmx1024m', '-jar', jar, '+flexlib=' + os.path.join(sdk, 'frameworks'),
                   '-load-config=', '-compiler.theme=',
                   '-compiler.external-library-path=' + player,
                   '-compiler.external-library-path+=' + os.path.join(FLASH, 'swc'),
                   '-compiler.library-path=' + os.path.join(sdk, 'frameworks', 'libs', 'framework.swc'),
                   '-compiler.source-path=' + ','.join(paths),
                   '-target-player=11.1', '-swf-version=14', '-debug=false',
                   '-compiler.strict=true', '-compiler.optimize=true',
                   '-default-size=' + movie.get('width', '1024') + ',' + movie.get('height', '768'),
                   '-default-frame-rate=' + movie.get('fps', '30'),
                   '-output=' + staged, target]
        log = os.path.join(outdir, name + '.log')
        with open(log, 'wb') as handle:
            code = subprocess.call(command, stdout=handle, stderr=subprocess.STDOUT)
        results.append({'project': name, 'success': code == 0, 'log': os.path.relpath(log, ROOT),
                        'output': os.path.relpath(output, ROOT),
                        'timeline': name == 'MarksOnGunTechTree'})
        print('{}: {}'.format(name, 'OK' if code == 0 else 'FAILED (see ' + log + ')'))
        sys.stdout.flush()
    with open(os.path.join(outdir, 'results.json'), 'w') as handle:
        json.dump(results, handle, indent=2)
    if not all(x['success'] for x in results):
        return 1
    if args.publish:
        for name, target, paths, output, movie in jobs:
            if name == 'MarksOnGunTechTree':
                print('MarksOnGunTechTree: keeping timeline SWF; publish through Animate.')
                continue
            shutil.copy2(os.path.join(outdir, os.path.basename(output)), output)
    return 0


if __name__ == '__main__':
    sys.exit(main())

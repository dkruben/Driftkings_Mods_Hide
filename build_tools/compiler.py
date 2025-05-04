# -*- coding: utf-8 -*-
import __builtin__
import imp
import marshal
import os
import py_compile
import struct
import subprocess
import sys
import time
import logging

# Configure logging
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Global variables
ORION_PATH = None


def get_git_date(path):
    try:
        return subprocess.check_output(['git', 'log', '-n', '1', '--format=%ct', '--', path]).strip()
    except subprocess.CalledProcessError:
        return ''


def compile_dir(path, max_levels=10, d_dir=None, o_dir=None, force=False, quiet=False):
    if not quiet:
        logger.info('Listing %s ...', path)
    try:
        names = os.listdir(path)
    except os.error:
        logger.error("Can't list %s", path)
        return False
    success = True
    for name in sorted(names):
        f_name = os.path.join(path, name).replace(os.sep, '/')
        d_file = None if d_dir is None else os.path.join(d_dir, name).replace(os.sep, '/')
        o_file = None if o_dir is None else os.path.join(o_dir, name).replace(os.sep, '/')
        if not os.path.isdir(f_name):
            success &= compile_file(f_name, d_file, o_file, force, quiet)
        elif (max_levels > 0 and
              name not in (os.curdir, os.pardir) and
              os.path.isdir(f_name) and
              not os.path.islink(f_name)):
            success &= compile_dir(f_name, max_levels - 1, d_file, o_file, force, quiet)
    return success


def compile_file(fullname, d_file=None, o_file=None, force=False, quiet=False):
    if not os.path.isfile(fullname) or not fullname.endswith('.py'):
        return True
    name = os.path.basename(fullname)
    head, _ = os.path.splitext(name)
    timeStr = get_git_date(fullname)
    if not force and head != '__init__':
        try:
            m_time = int(timeStr) if timeStr else int(os.stat(fullname).st_mtime)
            expect = struct.pack('<4sl', imp.get_magic(), m_time)
            c_file = (o_file or fullname) + (__debug__ and 'c' or 'o')
            with open(c_file, 'rb') as c_handle:
                actual = c_handle.read(8)

            if expect == actual:
                return True
        except IOError:
            pass
    if not quiet:
        logger.info('Compiling %s ...', fullname)
    try:
        ok = do_compile(fullname, d_file, o_file, True, timeStr)
        return ok
    except py_compile.PyCompileError as err:
        if quiet:
            logger.info('Compiling %s ...', fullname)
        logger.error(err.msg)
        return False
    except IOError as e:
        logger.error("IO Error: %s", e)
        return False


def do_compile(f_path, d_file=None, o_file=None, raises=False, time_str=''):
    with open(f_path, 'U') as f:
        if time_str:
            max_ts = timestamp = long(time_str)
        else:
            try:
                max_ts = timestamp = long(os.fstat(f.fileno()).st_mtime)
            except AttributeError:
                max_ts = timestamp = long(os.stat(f_path).st_mtime)
        code_string = f.read()
    mod_name = f_path
    if '__init__' in f_path:
        mod_name = os.path.dirname(f_path)
        if '%(file_compile_date)s' in code_string:
            time_str = get_git_date(mod_name)
            if not time_str:
                logger.info('Non-versioned mod folder detected: %s', mod_name)
                for root, _, files in os.walk(mod_name):
                    for fh in files:
                        if not fh.endswith('.py'):
                            continue
                        path = os.path.join(root, fh).replace(os.sep, '/')
                        file_time_str = get_git_date(path)
                        m_time = long(file_time_str) if file_time_str else long(os.stat(path).st_mtime)
                        if m_time > max_ts:
                            max_ts = m_time
            else:
                max_ts = long(time_str)
    mod_id = os.path.basename(mod_name).replace('.py', '').replace('mod_', '')
    compile_date = time.strftime('%d.%m.%Y', time.localtime(max_ts))
    code_string = code_string.replace('%(file_compile_date)s', compile_date)
    code_string = code_string.replace('%(mod_ID)s', mod_id)
    if '# -*- obfuscated -*-' in code_string:
        if ORION_PATH is None:
            logger.error('Obfuscated files present, but Orion path is not specified.')
            sys.exit(2)
        obf_path = (o_file or f_path).replace('.py', '_obf.py')
        obf_dir = os.path.dirname(obf_path)
        if not os.path.isdir(obf_dir):
            os.makedirs(obf_dir)
        with open(obf_path, 'wb') as fo:
            fo.write(code_string)
        try:
            base_path = os.getcwd() + '/' + obf_path
            subprocess.check_call([ORION_PATH, '/obfuscate-bytecode-file', base_path, '/exit'])
            subprocess.check_call([ORION_PATH, '/protect-bytecode-file', base_path + 'c', '/exit'])
        except subprocess.CalledProcessError as err:
            logger.error(str(err))
        else:
            if time_str:
                os.utime(obf_path + 'c', (time.time(), timestamp))
    try:
        code_object = __builtin__.compile(code_string, d_file or f_path, 'exec')
    except Exception as err:
        py_exc = py_compile.PyCompileError(err.__class__, err, d_file or f_path)
        if raises:
            raise py_exc
        else:
            logger.error(py_exc.msg)
            return False
    o_file = (o_file or f_path) + (__debug__ and 'c' or 'o')
    o_dir = os.path.dirname(o_file)
    if not os.path.isdir(o_dir):
        os.makedirs(o_dir)
    with open(o_file, 'wb') as fc:
        fc.write('\0\0\0\0')
        py_compile.wr_long(fc, timestamp)
        marshal.dump(code_object, fc)
        fc.flush()
        fc.seek(0, 0)
        fc.write(py_compile.MAGIC)
    if time_str or timestamp:
        os.utime(o_file, (time.time(), timestamp))
    return True


def parse_args():
    import getopt
    usage = """usage: python %s [-l] [-f] [-q] [-p PJOrion_path] [-d dest_dir] [-o output_dir] [directory|file ...]
    arguments: one or more file and directory names to compile
    options:
    -l: don't recurse into subdirectories
    -f: force rebuild even if timestamps are up-to-date
    -q: output only error messages
    -p PJOrion_path: path to PJOrion executable, only required if any obfuscated files are present
    -d dest_dir: directory to prepend to file paths for use in compile-time and runtime tracebacks in cases where the
        source file is unavailable
    -o output_dir: directory to put compiled files into, defaults to the folder being compiled""" % os.path.basename(sys.argv[0])
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'lfqp:d:o:')
    except getopt.error as msg:
        logger.error(msg)
        logger.error(usage)
        sys.exit(2)
    options = {'max_levels': 10, 'p_dir': None, 'd_dir': None, 'o_dir': None, 'force': False, 'quiet': False }
    for o, a in opts:
        if o == '-l':
            options['max_levels'] = 0
        elif o == '-f':
            options['force'] = True
        elif o == '-q':
            options['quiet'] = True
            logger.setLevel(logging.ERROR)
        elif o == '-p':
            options['p_dir'] = a
        elif o == '-d':
            options['d_dir'] = a
        elif o == '-o':
            options['o_dir'] = a
    return options, args


def main():
    global ORION_PATH
    options, args = parse_args()
    ORION_PATH = options['p_dir']
    if options['o_dir'] and args:
        if len(args) != 1 or not os.path.isdir(args[0]):
            logger.error("-o output_dir requires exactly one directory argument")
            sys.exit(2)
    if not args:
        logger.error('One or more arguments required to compile')
        return False
    success = True
    try:
        for arg in args:
            if os.path.isdir(arg):
                success &= compile_dir(arg, options['max_levels'], options['d_dir'], options['o_dir'], options['force'], options['quiet'])
            else:
                d_path = None if options['d_dir'] is None else options['d_dir'] + os.path.basename(arg)
                o_path = None if options['o_dir'] is None else options['o_dir'] + os.path.basename(arg)
                success &= compile_file(arg, d_path, o_path, options['force'], options['quiet'])
    except KeyboardInterrupt:
        logger.error('\n[interrupted]')
        return False
    return success


if __name__ == '__main__':
    sys.exit(int(not main()))

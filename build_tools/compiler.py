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


Orion_path = None


def get_git_date(path):
    try:
        return subprocess.check_output('git log -n 1 --format="%ct" --'.split() + [path])[1:-2]
    except subprocess.CalledProcessError:
        return ''


def compile_dir(path, max_levels=10, d_dir=None, o_dir=None, force=False, quiet=False):
    if not quiet:
        print 'Listing', path, '...'
    try:
        names = os.listdir(path)
    except os.error:
        print 'Can\'t list', path
        names = []
    success = True
    for name in sorted(names):
        f_name = os.path.join(path, name).replace(os.sep, '/')
        d_file = None if d_dir is None else os.path.join(d_dir, name).replace(os.sep, '/')
        o_file = None if o_dir is None else os.path.join(o_dir, name).replace(os.sep, '/')
        if not os.path.isdir(f_name):
            success &= compile_file(f_name, d_file, o_file, force, quiet)
        elif max_levels > 0 and name not in (os.curdir, os.pardir) and os.path.isdir(f_name) and not os.path.islink(f_name):
            success &= compile_dir(f_name, max_levels - 1, d_file, o_file, force, quiet)
    return success


def compile_file(fullname, d_file=None, o_file=None, force=False, quiet=False):
    success = True
    name = os.path.basename(fullname)
    head, tail = name[:-3], name[-3:]
    if not os.path.isfile(fullname) or tail != '.py':
        return success
    timeStr = get_git_date(fullname)
    if not force and head != '__init__':
        try:
            m_time = int(timeStr) if timeStr else int(os.stat(fullname).st_mtime)
            expect = struct.pack('<4sl', imp.get_magic(), m_time)
            c_file = (o_file or fullname) + (__debug__ and 'c' or 'o')
            with open(c_file, 'rb') as c_handle:
                actual = c_handle.read(8)
            if expect == actual:
                return success
        except IOError:
            pass
    if not quiet:
        print 'Compiling', fullname, '...'
    try:
        ok = do_compile(fullname, d_file, o_file, True, timeStr)
    except py_compile.PyCompileError, err:
        if quiet:
            print 'Compiling', fullname, '...'
        print err.msg
        success = False
    except IOError, e:
        print "Sorry", e
        success = False
    else:
        success &= ok
    return success


def main():
    global Orion_path
    import getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'lfqp:d:o:')
    except getopt.error, msg:
        print msg
        print "usage: python %s [-l] [-f] [-q] [-p PJOrion_path] [-d dest_dir] [-o output_dir] [directory|file ...]" % os.path.basename(sys.argv[0])
        print '''    arguments: one or more file and directory names to compile
    options:
        -l: don't recurse into subdirectories
        -f: force rebuild even if timestamps are up-to-date
        -q: output only error messages
        -p PJOrion_path: path to PJOrion executable, only required if any obfuscated files are present
        -d dest_dir: directory to prepend to file paths for use in compile-time and runtime tracebacks in cases where the
            source file is unavailable
        -o output_dir: directory to put compiled files into, defaults to the folder being compiled'''
        sys.exit(2)
    max_levels = 10
    p_dir = None
    d_dir = None
    o_dir = None
    force = 0
    quiet = 0
    for o, a in opts:
        if o == '-l':
            max_levels = 0
        if o == '-f':
            force = True
        if o == '-q':
            quiet = True
        if o == '-p':
            p_dir = a
        if o == '-d':
            d_dir = a
        if o == '-o':
            o_dir = a
    Orion_path = p_dir
    if o_dir:
        if len(args) != 1 and not os.path.isdir(args[0]):
            print "-o output_dir requires exactly one directory argument"
            sys.exit(2)
    success = True
    try:
        if args:
            for arg in args:
                if os.path.isdir(arg):
                    success &= compile_dir(arg, max_levels, d_dir, o_dir, force, quiet)
                else:
                    success &= compile_file(arg, d_dir + os.path.basename(arg), o_dir + os.path.basename(arg), force, quiet)
        else:
            print 'One or more arguments required to compile'
            success = False
    except KeyboardInterrupt:
        print '\n[interrupted]'
        success = 0
    return success


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
                print 'Non-versioned mod folder detected:', mod_name
                for path in ('/'.join((x[0], y)).replace(os.sep, '/') for x in os.walk(mod_name) for y in x[2]):
                    if not path.endswith('.py'):
                        continue
                    time_str = get_git_date(path)
                    m_time = long(time_str) if time_str else long(os.stat(path).st_mtime)
                    if m_time > max_ts:
                        max_ts = m_time
            else:
                max_ts = long(time_str)
    code_string = code_string.replace('%(file_compile_date)s', time.strftime('%d.%m.%Y', time.localtime(max_ts))).replace('%(mod_ID)s', os.path.basename(mod_name).replace('.py', '').replace('mod_', ''))
    if '# -*- obfuscated -*-' in code_string:
        if Orion_path is None:
            sys.stderr.write('Obfuscated files present, but Orion path is not specified.')
            sys.exit(2)
        obf_path = (o_file or f_path).replace('.py', '_obf.py')
        obf_dir = os.path.dirname(obf_path)
        if not os.path.isdir(obf_dir):
            os.makedirs(obf_dir)
        with open(obf_path, 'wb') as fo:
            fo.write(code_string)
        try:
            # subprocess.check_call([Orion_path, '/obfuscate-text-file', os.getcwd() + '/' + obf_path, '/exit'])
            subprocess.check_call([Orion_path, '/obfuscate-bytecode-file', os.getcwd() + '/' + obf_path, '/exit'])
            subprocess.check_call([Orion_path, '/protect-bytecode-file', os.getcwd() + '/' + obf_path + 'c', '/exit'])
        except subprocess.CalledProcessError, err:
            sys.stderr.write(err.message + '\n')
        else:
            if time_str:
                os.utime(obf_path + 'c', (time.time(), timestamp))
    try:
        code_object = __builtin__.compile(code_string, d_file or f_path, 'exec')
    except Exception, err:
        py_exc = py_compile.PyCompileError(err.__class__, err, d_file or f_path)
        if raises:
            raise py_exc
        else:
            sys.stderr.write(py_exc.msg + '\n')
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


if __name__ == '__main__':
    sys.exit(int(not main()))

# -*- coding: utf-8 -*-
"""Small file helpers compatible with the client's Python 2 runtime."""
import os
import sys
import tempfile


def atomicWrite(path, data):
    """Replace a file only after its complete replacement has been written."""
    path = os.path.abspath(path)
    directory = os.path.dirname(path)
    if not os.path.isdir(directory):
        os.makedirs(directory)
    descriptor, temporary = tempfile.mkstemp(prefix='.driftkings-', dir=directory)
    try:
        with os.fdopen(descriptor, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if hasattr(os, 'replace'):
            os.replace(temporary, path)
        elif os.name == 'nt':
            import ctypes
            from ctypes import wintypes
            move = ctypes.WinDLL('kernel32', use_last_error=True).MoveFileExW
            move.argtypes = (wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD)
            move.restype = wintypes.BOOL
            encoding = sys.getfilesystemencoding() or 'mbcs'
            source = temporary.decode(encoding) if isinstance(temporary, str) else temporary
            destination = path.decode(encoding) if isinstance(path, str) else path
            if not move(source, destination, 0x1 | 0x8):
                raise ctypes.WinError(ctypes.get_last_error())
        else:
            os.rename(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.remove(temporary)

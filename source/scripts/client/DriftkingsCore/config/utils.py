# -*- coding: utf-8 -*-
import collections

import BigWorld
import Keys

__all__ = ('smart_update', 'processHotKeys',)


def smart_update(old, new):
    changed = False
    for k in old:
        v = new.get(k)
        if isinstance(v, dict):
            changed |= smart_update(old[k], v)
        elif v is not None:
            if isinstance(v, unicode):
                v = v.encode('utf-8')
            changed |= old[k] != v
            old[k] = v
    return changed


KEY_ALT, KEY_CONTROL, KEY_SHIFT = range(-1, -4, -1)
SPECIAL_TO_KEYS = {
    KEY_ALT: ['KEY_LALT', 'KEY_RALT'],
    KEY_CONTROL: ['KEY_LCONTROL', 'KEY_RCONTROL'],
    KEY_SHIFT: ['KEY_LSHIFT', 'KEY_RSHIFT']}


def processHotKeys(data, keys, mode):
    add = lambda key: key if 'KEY_' in key else 'KEY_' + key
    if mode == 'read':
        process = lambda key: getattr(Keys, add(key))
    elif mode == 'write':
        process = lambda key: SPECIAL_TO_KEYS.get(key) or add(BigWorld.keyToString(key))
    else:
        assert False, 'unknown hotkey conversion mode'
    make = lambda keySet: [make(key) if isinstance(key, (list, tuple)) else process(key) for key in keySet]
    for dataKey in keys:
        newKey = dataKey.replace('key', 'Key')
        if (newKey if mode == 'read' else dataKey) not in data:
            continue
        data[(dataKey if mode == 'read' else newKey)] = make(data.pop((newKey if mode == 'read' else dataKey)))

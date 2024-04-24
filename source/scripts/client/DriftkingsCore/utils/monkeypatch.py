# -*- coding: utf-8 -*-
import inspect
from functools import partial, update_wrapper

from .abstract import redirect_traceback
from .logger import logTrace, logError

__all__ = ('registerEvent', 'override', 'overrideMethod', 'overrideStaticMethod', 'overrideClassMethod', 'find_attr', 'find_attr_name')
_sentinel = object()


def find_attr_name(obj, name, accept_property=False):
    if not name.endswith('__'):
        while name.startswith('_'):
            name = name[1:]
    full_name = '__'.join((getattr(obj, '__name__', obj.__class__.__name__), name))
    if not full_name.startswith('_'):
        full_name = '_' + full_name
    suf_name = '_' + name
    for _name in ((full_name, suf_name, name), (name, suf_name, full_name))[accept_property]:
        if hasattr(obj, _name):
            return _name


def find_attr(obj, name, default=_sentinel, accept_property=False):
    _name = find_attr_name(obj, name, accept_property)
    if _name is None and default is not _sentinel:
        return default
    return getattr(obj, (_name or ('_' + name)))


def override(obj, prop=_sentinel, getter=None, setter=None, deleter=None):
    """
    :param obj: object, which attribute needs overriding
    :param prop: attribute name (can be not mangled), attribute must be callable
    :param getter: f_get function or None
    :param setter: f_set function or None
    :param deleter: f_del function or None
    :return function: unmodified getter or, if getter is None and src is not property, decorator"""

    if getter:
        getter_func = getter
        while isinstance(getter_func, partial):
            getter_func = getter_func.func
    if prop is _sentinel:
        if getter:
            # noinspection PyUnboundLocalVariable
            prop = getter_func.__name__
        else:
            return partial(override, obj, prop)
    if inspect.isclass(obj) and not prop.endswith('__') and not hasattr(obj, prop):
        prop = find_attr_name(obj, prop, True)
    src = getattr(obj, prop)
    if type(src) is property and (getter or setter or deleter):
        props = []
        for func, fType in ((getter, 'fget'), (setter, 'fset'), (deleter, 'fdel')):
            assert func is None or callable(func), fType + ' is not callable!'
            props.append(partial(func, getattr(src, fType)) if func else getattr(src, fType))
        setattr(obj, prop, property(*props))
        return getter
    elif getter:
        assert callable(src), 'Source property is not callable!'
        assert callable(getter), 'Handler is not callable!'
        getter_new = redirect_traceback(partial(getter, src), getattr(getter_func, 'func_code', None))
        try:
            update_wrapper(getter_new, getter_func)
        except AttributeError:
            pass
        if inspect.isclass(obj):
            if inspect.isfunction(src):
                getter_new = staticmethod(getter_new)
            elif getattr(src, '__self__', None) is not None:
                getter_new = classmethod(getter_new)
        setattr(obj, prop, getter_new)
        return getter
    else:
        return partial(override, obj, prop)


# ----! HOOKS !----
class EventHook(object):

    def __init__(self):
        self.__handlers = []

    def __iadd__(self, handler):
        self.__handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.__handlers:
            self.__handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        for handler in self.__handlers:
            handler(*args, **kwargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self.__handlers:
            if theHandler.im_self == inObject:
                self -= theHandler


class HooksDecorators(object):

    def __init__(self):
        self.registerEvent = self._hook_decorator(self._registerEvent)
        self.overrideStaticMethod = self._hook_decorator(self._OverrideStaticMethod)
        self.overrideClassMethod = self._hook_decorator(self._OverrideClassMethod)

    @staticmethod
    def _hook_decorator(func):
        def decorator1(*args, **kwargs):
            def decorator2(handler):
                func(handler, *args, **kwargs)
            return decorator2
        return decorator1

    @staticmethod
    def _override(cls, method, setter):
        getter = getattr(cls, method)
        if type(getter) is not property:
            setattr(cls, method, setter)
        else:
            setattr(cls, method, property(setter))

    def _OverrideStaticMethod(self, handler, cls, method):
        getter = getattr(cls, method)
        setter = staticmethod(lambda *a, **k: handler(getter, *a, **k))
        self._override(cls, method, setter)

    def _OverrideClassMethod(self, handler, cls, method):
        getter = getattr(cls, method)
        setter = classmethod(lambda *a, **k: handler(getter, *a, **k))
        self._override(cls, method, setter)

    @staticmethod
    def __event_handler(prepend, e, m, *a, **k):
        try:
            if prepend:
                e.fire(*a, **k)
                r = m(*a, **k)
            else:
                r = m(*a, **k)
                e.fire(*a, **k)
            return r
        except StandardError:
            logTrace(__file__)

    def _registerEvent(self, handler, cls, method, prepend=False):
        evt = '__event_%i_%s' % ((1 if prepend else 0), method)
        if hasattr(cls, evt):
            e = getattr(cls, evt)
        else:
            new_m = '__orig_%i_%s' % ((1 if prepend else 0), method)
            setattr(cls, evt, EventHook())
            setattr(cls, new_m, getattr(cls, method))
            e = getattr(cls, evt)
            m = getattr(cls, new_m)
            l = lambda *a, **k: self.__event_handler(prepend, e, m, *a, **k)
            l.__name__ = method
            setattr(cls, method, l)
        e += handler

    @staticmethod
    def overrideMethod(setter, getter='__init__'):
        """
        setter: class object
        getter: unicode default __init__
        """
        class_name = setter.__name__
        if not hasattr(setter, getter):
            if getter.startswith('__'):
                full_name = '_{0}{1}'.format(class_name, getter)
                if hasattr(setter, full_name):
                    getter = full_name
                elif hasattr(setter, getter[1:]):
                    getter = getter[1:]

        def outer(new_method):
            old_method = getattr(setter, getter, None)
            if old_method is not None and callable(old_method):
                def __override(*args, **kwargs):
                    return new_method(old_method, *args, **kwargs)
                setattr(setter, getter, __override)
            else:
                logError('overrideMethod error: %s in %s is not callable or undefined in %s' % (getter, class_name, new_method.__name__))
            return new_method

        return outer


# ---! HooksDecorators !---
registerEvent = HooksDecorators().registerEvent
overrideMethod = HooksDecorators().overrideMethod
overrideStaticMethod = HooksDecorators().overrideStaticMethod
overrideClassMethod = HooksDecorators().overrideClassMethod

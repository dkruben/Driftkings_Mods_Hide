# -*- coding: utf-8 -*-
from gui.shared.view_helpers.blur_manager import _BlurManager

from ... import override

__all__ = ()


@override(_BlurManager, '_setLayerBlur')
def _setLayerBlur(func, self, blur, *args, **kwargs):
    if self._battle is None:
        return func(self, blur, *args, **kwargs)
    self._battle.blurBackgroundViews(blur.ownLayer, blur.blurAnimRepeatCount, blur.uiBlurRadius)
    # self._battle.blurBackgroundViews(blur.ownLayer, blur.blurAnimRepeatCount)

"""Zengge (Mesh) Color"""
from __future__ import annotations
from typing import Final
import colorsys
import math
import logging

_LOGGER = logging.getLogger(__name__)

class ZenggeColor:
    def __new__():
        raise TypeError("This is a static class and cannot be initialized.")
    
    @staticmethod
    def _normal_round(n):
        if n - math.floor(n) < 0.5:
            return math.floor(n)
        return math.ceil(n)
    
    @staticmethod
    def _clamp(value, min_value, max_value):
        return max(min_value, min(max_value, value))
    
    @staticmethod
    def _saturate(value):
        return ZenggeColor._clamp(value, 0.0, 1.0)
       
    @staticmethod
    def normalize(value, min_from, max_from, min_to, max_to) -> int:
        normalized = (value - min_from) / (max_from - min_from)
        new_value = min(
            round((normalized * (max_to - min_to)) + min_to),
            max_to,
        )
        return max(new_value, min_to)
    
    @staticmethod
    def h360_to_h255(h360):
        if h360 <= 180:
            return ZenggeColor._normal_round((h360*254)/360)
        else:
            return ZenggeColor._normal_round((h360*255)/360)
    
    @staticmethod
    def h255_to_h360(h255):
        if h255 <= 128:
            return ZenggeColor._normal_round((h255*360)/254)
        else:
            return ZenggeColor._normal_round((h255*360)/255)

    @staticmethod
    def hue_to_rgb(h):
        r = abs(h * 6.0 - 3.0) - 1.0
        g = 2.0 - abs(h * 6.0 - 2.0)
        b = 2.0 - abs(h * 6.0 - 4.0)
        return ZenggeColor._saturate(r), ZenggeColor._saturate(g), ZenggeColor._saturate(b)

    @staticmethod
    def hsl_to_rgb(h, s=1, l=.5):
        h = (h/360)
        r, g, b = ZenggeColor.hue_to_rgb(h)
        c = (1.0 - abs(2.0 * l - 1.0)) * s
        r = round((r - 0.5) * c + l,4) * 255
        g = round((g - 0.5) * c + l,4) * 255
        b = round((b - 0.5) * c + l,4) * 255
        if (r >= 250):
            r = 255
        if (g >= 250):
            g = 255
        if (b >= 250):
            b = 255
        return round(r), round(g), round(b)
    
    @staticmethod
    def decode_hsl_rgb(h, s=1, l=0.5):
        return ZenggeColor.hsl_to_rgb(ZenggeColor.h255_to_h360(h), s, l)

    @staticmethod
    def decode_hsv_rgb(h, s, v=1):
        return ZenggeColor.hsv_to_rgb(h / 255, s / 63, v)
        return ZenggeColor.hsv_to_rgb(ZenggeColor.h255_to_h360(h) / 360, s / 63, v)
   
    @staticmethod
    def hsv_to_rgb(h: float, s: float, v: float = 1.0) -> tuple[int, int, int]:
        return tuple(round(i * 255) for i in colorsys.hsv_to_rgb(h,s,v))

# -*- coding: utf-8 -*-

from __future__ import absolute_import

from . import image
from .base import Type  # noqa

# Supported image types
IMAGE = (
    image.Dwg(),
    image.Xcf(),
    image.Jpeg(),
    image.Jpx(),
    image.Apng(),
    image.Png(),
    image.Gif(),
    image.Webp(),
    image.Tiff(),
    image.Cr2(),
    image.Bmp(),
    image.Jxr(),
    image.Psd(),
    image.Ico(),
    image.Heic(),
    image.Dcm(),
    image.Avif(),
    image.Svg(),
)

# Expose supported type matchers
TYPES = list(IMAGE)

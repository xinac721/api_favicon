# -*- coding: utf-8 -*-

# favicon
from flask import Blueprint

favicon_blu = Blueprint('favicon', __name__)
from .views import *

# -*- coding: utf-8 -*-

import logging
import os
import sys

from flask import Flask
from flask import redirect, url_for

sys.path.append(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
))

logging.basicConfig(level=logging.INFO, format='[%(levelname)-7s] %(asctime)s -[%(filename)s:%(lineno)4d] %(message)s')

app = Flask(__name__)

# 注册蓝图
from applications.application import favicon_blu
app.register_blueprint(favicon_blu)


# @app.route('/')
def hello_world():
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=False)

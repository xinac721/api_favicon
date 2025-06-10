# -*- coding: utf-8 -*-

import hashlib
import logging
import re
from urllib.parse import urlparse

import requests
import urllib3
from urllib3.exceptions import MaxRetryError, ReadTimeoutError

from app_favicon.xtools import header
from app_favicon.xtools.filetype import helpers, filetype

urllib3.disable_warnings()
logging.captureWarnings(True)
logger = logging.getLogger()


class Favicon:
    # 协议://域名:端口号, 域名md5值
    scheme, domain, port, domain_md5, icon_url = None, None, None, None, None
    # 访问路径
    path = '/'

    def __init__(self, url: str):
        try:
            url = url.lower().strip()
            self._parse(url)
            if not self.domain_md5 and ('.' in url):
                if url.startswith('//'):
                    self._parse('http:' + url)
                elif not (url.startswith('https://') or url.startswith('http://')):
                    self._parse('http://' + url)
        except Exception as e:
            logger.error('Init error: ' + url)
            logger.error(e)

    def _parse(self, url: str):
        try:
            _url = urlparse(url)
            self.scheme = _url.scheme
            self.domain = _url.hostname
            self.path = _url.path
            self.port = _url.port
            if self.scheme not in ['https', 'http']:
                if self.scheme:
                    logger.warning('-> Unsupported scheme: %s' % self.scheme)
                self.scheme = 'http'
            if self.domain and _check_url(self.domain) is None:
                self.domain = None
            if self.domain:
                self.domain_md5 = hashlib.md5(self.domain.encode("utf-8")).hexdigest()
        except Exception as e:
            self.scheme = None
            self.domain = None
            logger.error('Parse url error: ' + url)
            logger.error(e)

    def _get_icon_url(self, icon_path: str):
        if icon_path.startswith('https://') or icon_path.startswith('http://'):
            self.icon_url = icon_path
        elif icon_path.startswith('//'):
            self.icon_url = self.scheme + ':' + icon_path
        elif icon_path.startswith('/'):
            self.icon_url = self.scheme + '://' + self.domain + icon_path
        elif icon_path.startswith('..'):
            self.icon_url = self.scheme + '://' + self.domain + '/' + icon_path.replace('../', '')
        elif icon_path.startswith('./'):
            self.icon_url = self.scheme + '://' + self.domain + icon_path[1:]
        else:
            self.icon_url = self.scheme + '://' + self.domain + '/' + icon_path

    def _get_icon_default(self):
        self.icon_url = self.scheme + '://' + self.domain + '/favicon.ico'

    def get_icon_url(self, icon_path: str, default=False) -> str:
        if default:
            self._get_icon_default()
        else:
            self._get_icon_url(icon_path)
        return self.icon_url

    def get_icon_file(self, icon_path: str, default=False):
        self.get_icon_url(icon_path, default)
        if self.icon_url and ('.' in self.domain):
            _content, _ct = _req_get(self.icon_url)
            if _ct and helpers.is_image(_content):
                if _content and len(_content) > 1 * 1024 * 1024:
                    logger.warning('-> Image is too large: %d' % len(_content))
                    logger.warning('-> Image is too large: %s' % self.domain)
                return _content, filetype.guess_mime(_content) or _ct
        return None, None

    def req_get(self):
        if '.' not in self.domain:
            return None
        _url = self.scheme + '://' + self.domain
        if self.port:
            _url += ':' + str(self.port)
        _content, _ct = _req_get(_url)
        if _ct and ('text' in _ct or 'html' in _ct):
            if _content and len(_content) > 20 * 1024 * 1024:
                logger.error('-> Source is too large: %d' % len(_content))
                logger.error('-> Source is too large: %s' % _url)
                return None
            return _content
        return None

    def get_base_url(self):
        if '.' not in self.domain:
            return None
        _url = self.scheme + '://' + self.domain
        if self.port and self.port not in [80, 443]:
            _url += ':' + str(self.port)
        return _url


def _req_get(url: str):
    """
    :return: content, content_type
    """
    logger.info('-> %s' % url)
    try:
        session = requests.Session()
        session.max_redirects = 3
        req = session.get(url, headers=header.get_header(), timeout=10, verify=False)
        if req.ok:
            if req.is_redirect:
                return _req_get(req.next.url)
            else:
                ct_type = req.headers.get('Content-Type')
                ct_length = req.headers.get('Content-Length')
                if ct_type and ';' in ct_type:
                    _cts = ct_type.split(';')
                    if 'charset' in _cts[0]:
                        ct_type = _cts[-1].strip()
                    else:
                        ct_type = _cts[0].strip()
                if ct_length and int(ct_length) > 10 * 1024 * 1024:
                    logger.warning('-> Response is too large: %d' % int(ct_length))
                return req.content, ct_type
        else:
            logger.error('-> Request error: %d' % req.status_code)
    except (MaxRetryError, ReadTimeoutError, Exception):
        pass
    return None, None


_pattern_domain = re.compile(r'[a-zA-Z0-9\u4E00-\u9FA5][-a-zA-Z0-9\u4E00-\u9FA5]{0,62}(\.[a-zA-Z0-9\u4E00-\u9FA5][-a-zA-Z0-9\u4E00-\u9FA5]{0,62})+\.?', re.I)


def _check_url(url: str):
    return _pattern_domain.match(url)

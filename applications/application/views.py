import hashlib
import logging
import os
import re
import time

import bs4
from bs4 import SoupStrainer
from flask import request, make_response, redirect, url_for

from app_favicon.xtools import header, file_util
from app_favicon.xtools.filetype import helpers, filetype
from . import favicon_blu
from .models import Favicon

# icon 存储的路径
icon_root_path = favicon_blu.root_path
default_icon_path = '/'.join([favicon_blu.root_path, 'favicon.png'])
default_icon_content = file_util.read_file(default_icon_path, mode='rb')
logger = logging.getLogger()


@favicon_blu.route('/icon/')
def index():
    req_url = request.args.get('url')
    if not req_url:
        # return 'Illegal parameter: [url]'
        # return redirect(url_for('favicon.default'))
        return render_template('index.html')

    entity = Favicon(req_url)
    if not entity.domain:
        # return 'Illegal parameter: [url]'
        return redirect(url_for('favicon.default'))

    icon_url, icon_content, icon_type, icon_flag = None, None, None, True
    _cached, cache_icon = _get_cache_icon(entity.domain_md5)
    if cache_icon and helpers.is_image(cache_icon):
        icon_content = cache_icon
        icon_type = filetype.guess_mime(icon_content)
    else:
        html_content = entity.req_get()
        if html_content:
            icon_url = _parse_html(html_content, entity)
        # 1. 从原始网页标签链接中获取
        if icon_url:
            icon_content, icon_type = entity.get_icon_file(icon_url)
        # 2. 从网站默认位置获取
        if not icon_content:
            logger.info('-> get icon from ico: /favicon.ico')
            icon_content, icon_type = entity.get_icon_file('', True)
            pass
        # 写入默认图标
        if not icon_content:
            logger.error('-> get icon fail: %s' % entity.domain)
            icon_content = _cached if _cached else default_icon_content
            icon_flag = False
        if icon_content:
            cache_path = '/'.join([icon_root_path, 'icon', entity.domain_md5 + '.png'])
            file_util.write_file(cache_path, icon_content, mode='wb')

    resp = make_response(icon_content)
    resp.headers.update(_get_header(icon_type, cache=icon_flag))
    return resp


@favicon_blu.route('/icon/default')
def default():
    icon_content = default_icon_content
    resp = make_response(icon_content)
    resp.headers.update(_get_header('', cache=False))
    return resp


def _get_header(content_type: str, cache: bool):
    _ct = 'image/x-icon'
    if content_type and content_type in header.image_type:
        _ct = content_type
    return {
        'Content-Type': _ct,
        'Cache-Control': 'public, max-age=%d' % (604800 if cache else 43200),
        'X-Robots-Tag': 'noindex, nofollow'
    }


def _get_file_md5(file_path):
    try:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                buffer = f.read(1024 * 8)
                if not buffer:
                    break
                else:
                    md5.update(buffer)
        return md5.hexdigest().lower()
    except Exception as e:
        print(e)
    return None


_pattern_icon = re.compile(r'(icon|shortcut icon|alternate icon|apple-touch-icon)+', re.I)
_pattern_link = re.compile(r'(<link[^>]+rel=.(icon|shortcut icon|alternate icon|apple-touch-icon)[^>]+>)', re.I)


def _parse_html(content: str, entity: Favicon):
    if content:
        bs = bs4.BeautifulSoup(content, features='lxml', parse_only=SoupStrainer("link"))
        if len(bs) == 0:
            bs = bs4.BeautifulSoup(content, features='html.parser', parse_only=SoupStrainer("link"))
        html_links = bs.find_all("link", rel=_pattern_icon)
        if not html_links or len(html_links) == 0:
            content = str(content).encode('utf-8', 'replace').decode('utf-8', 'replace')
            content_links = _pattern_link.findall(content)
            c_link = ''.join([_links[0] for _links in content_links])
            bs = bs4.BeautifulSoup(c_link, features='lxml')
            html_links = bs.find_all("link", rel=_pattern_icon)
        if html_links and len(html_links) > 0:
            icon_url = _get_link_rel(html_links, entity, 'shortcut icon') or \
                       _get_link_rel(html_links, entity, 'icon') or \
                       _get_link_rel(html_links, entity, 'alternate icon') or \
                       _get_link_rel(html_links, entity, '')
            logger.info('-> get icon href: %s' % icon_url)
            return icon_url
    else:
        return None


def _get_link_rel(links, entity: Favicon, _rel: str):
    _icon_url = None
    if links:
        for link in links:
            r = link.get('rel')
            _r = ' '.join(r)
            _href = link.get('href')
            if _rel:
                if _r.lower() == _rel:
                    _icon_url = entity.get_icon_url(str(_href))
                    break
            else:
                _icon_url = entity.get_icon_url(str(_href))
    return _icon_url


default_icon_md5 = [_get_file_md5(default_icon_path), '05231fb6b69aff47c3f35efe09c11ba0', '3ca64f83fdcf25135d87e08af65e68c9']


def _get_cache_icon(domain_md5: str):
    return _get_cache_file(domain_md5)


def _get_cache_file(domain_md5: str):
    cache_path = '/'.join([icon_root_path, 'icon', domain_md5 + '.png'])
    if os.path.exists(cache_path) and os.path.isfile(cache_path) and os.path.getsize(cache_path) > 0:
        cached_icon = file_util.read_file(cache_path, mode='rb')
        file_md5 = _get_file_md5(cache_path)
        file_time = int(os.path.getmtime(cache_path))
        if file_md5 in default_icon_md5:
            if int(time.time()) - file_time > 12 * 60 * 60:
                return cached_icon, None
        else:
            if int(time.time()) - file_time > 30 * 24 * 60 * 60:
                return cached_icon, None
        # logger.info('-> get icon from cache: %s' % domain)
        return cached_icon, cached_icon
    return None, None


if __name__ == '__main__':
    pass

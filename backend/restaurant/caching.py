"""
Cache-aside layer for the public catalog (menu items + categories).
"""
import hashlib
import os
from urllib.parse import urlencode

from django.core.cache import cache

MENU_LIST_TTL = int(os.environ.get('CACHE_TTL_MENU_LIST', 300))
MENU_ITEM_TTL = int(os.environ.get('CACHE_TTL_MENU_ITEM', 300))
CATEGORY_LIST_TTL = int(os.environ.get('CACHE_TTL_CATEGORY_LIST', 300))

MENU_LIST_VERSION_KEY = 'llapi:menu:list:version'
CATEGORY_LIST_VERSION_KEY = 'llapi:category:list:version'


def _query_digest(query_params):
    """Deterministic short hash of a request's query params, order-independent."""
    normalized = urlencode(sorted(query_params.items()))
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _bump_version(version_key):
    """Atomically advance a version counter. Never raises: a missing key (first
    write ever) or an unreachable Redis both just fall back safely."""
    try:
        cache.incr(version_key)
    except ValueError:
        cache.set(version_key, 2, timeout=None)
    except Exception:
        pass


# --- Menu items ---

def menu_list_key(query_params):
    version = cache.get(MENU_LIST_VERSION_KEY, 1)
    return f'llapi:menu:list:v{version}:{_query_digest(query_params)}'


def menu_item_key(pk):
    return f'llapi:menu:item:{pk}'


def get_menu_list(query_params):
    return cache.get(menu_list_key(query_params))


def set_menu_list(query_params, data):
    cache.set(menu_list_key(query_params), data, MENU_LIST_TTL)


def get_menu_item(pk):
    return cache.get(menu_item_key(pk))


def set_menu_item(pk, data):
    cache.set(menu_item_key(pk), data, MENU_ITEM_TTL)


def on_menu_item_write(pk=None):
    """Call after any MenuItem create/update/delete."""
    _bump_version(MENU_LIST_VERSION_KEY)
    if pk is not None:
        cache.delete(menu_item_key(pk))


# --- Categories ---

def category_list_key(query_params):
    version = cache.get(CATEGORY_LIST_VERSION_KEY, 1)
    return f'llapi:category:list:v{version}:{_query_digest(query_params)}'


def get_category_list(query_params):
    return cache.get(category_list_key(query_params))


def set_category_list(query_params, data):
    cache.set(category_list_key(query_params), data, CATEGORY_LIST_TTL)


def on_category_write():
    """Call after any Category create/update/delete. Category data is embedded
    in every menu item response, so a category write invalidates both lists."""
    _bump_version(CATEGORY_LIST_VERSION_KEY)
    _bump_version(MENU_LIST_VERSION_KEY)

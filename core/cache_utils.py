"""
Caching utilities for performance optimization
"""

import hashlib
import json
from functools import wraps

from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key


def cache_key_generator(*args, **kwargs):
    """Generate a consistent cache key from arguments"""
    key_data = {"args": args, "kwargs": sorted(kwargs.items()) if kwargs else {}}
    key_string = json.dumps(key_data, sort_keys=True, default=str)
    return hashlib.md5(key_string.encode()).hexdigest()


def cached_view(timeout=300, key_prefix="view"):
    """
    Decorator for caching view results

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key based on view name, user, and parameters
            cache_key_parts = [
                key_prefix,
                view_func.__name__,
                str(request.user.id) if request.user.is_authenticated else "anonymous",
                cache_key_generator(*args, **kwargs),
            ]
            cache_key = ":".join(cache_key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute view and cache result
            result = view_func(request, *args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def cached_queryset(timeout=300, key_prefix="queryset"):
    """
    Decorator for caching queryset results

    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_prefix: Prefix for cache key
    """

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key_parts = [key_prefix, func.__name__, cache_key_generator(*args, **kwargs)]
            cache_key = ":".join(cache_key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def invalidate_cache_pattern(pattern):
    """
    Invalidate cache keys matching a pattern.
    Uses Redis pattern matching when available; provides safe fallbacks for LocMemCache.
    """
    # Try Redis first
    try:
        from django.core.cache.backends.redis import RedisCache

        if isinstance(cache, RedisCache):
            keys = cache._cache.get_client().keys(f"*{pattern}*")
            if keys:
                cache._cache.get_client().delete(*keys)
            return
    except Exception:
        # If Redis backend is not available or operation fails, continue to fallback
        pass

    # Fallback for LocMemCache (default dev backend): iterate internal keys safely
    try:
        from django.core.cache.backends.locmem import LocMemCache

        if isinstance(cache, LocMemCache):
            keys_to_delete = [k for k in cache._cache.keys() if pattern in str(k)]
            for k in keys_to_delete:
                cache.delete(k)
            return
    except Exception:
        # LocMem fallback failed; proceed to last resort
        pass

    # Last resort: clear cache to avoid stale data
    try:
        cache.clear()
    except Exception:
        # Silently ignore if clear is not available
        pass


class CacheManager:
    """Manager class for common caching operations"""

    # Cache timeouts (in seconds)
    TIMEOUTS = {
        "short": 300,  # 5 minutes
        "medium": 1800,  # 30 minutes
        "long": 3600,  # 1 hour
        "very_long": 86400,  # 24 hours
    }

    @staticmethod
    def generate_key(prefix, **kwargs):
        """Generate a cache key with prefix and parameters"""
        key_parts = [prefix]
        if kwargs:
            sorted_params = sorted(kwargs.items())
            param_string = "_".join([f"{k}:{v}" for k, v in sorted_params if v])
            if param_string:
                key_parts.append(param_string)
        return ":".join(key_parts)

    @staticmethod
    def get_craftsmen_list_key(filters=None):
        """Generate cache key for craftsmen list"""
        filter_hash = cache_key_generator(filters) if filters else "all"
        return f"craftsmen_list:{filter_hash}"

    @staticmethod
    def get_services_list_key():
        """Generate cache key for services list"""
        return "services_list:all"

    @staticmethod
    def get_orders_list_key(user_id, status=None):
        """Generate cache key for user orders list"""
        status_key = status or "all"
        return f"orders_list:{user_id}:{status_key}"

    @staticmethod
    def get_craftsman_profile_key(craftsman_id):
        """Generate cache key for craftsman profile"""
        return f"craftsman_profile:{craftsman_id}"

    @staticmethod
    def get_statistics_key(stat_type):
        """Generate cache key for statistics"""
        return f"statistics:{stat_type}"

    @staticmethod
    def invalidate_user_cache(user_id):
        """Invalidate all cache entries for a specific user"""
        patterns = [f"orders_list:{user_id}", f"craftsman_profile:{user_id}", f"view:*:{user_id}:*"]
        for pattern in patterns:
            invalidate_cache_pattern(pattern)

    @staticmethod
    def invalidate_craftsmen_cache():
        """Invalidate craftsmen list cache"""
        invalidate_cache_pattern("craftsmen_list")

    @staticmethod
    def invalidate_available_orders_cache():
        """Invalidate available orders cache entries across all craftsmen and filters"""
        invalidate_cache_pattern("available_orders")

    @staticmethod
    def invalidate_services_cache():
        """Invalidate services cache"""
        cache.delete("services_list:all")


# Template fragment caching helpers
def get_template_cache_key(fragment_name, *args):
    """Get template fragment cache key"""
    return make_template_fragment_key(fragment_name, args)


def cache_template_fragment(fragment_name, timeout=300):
    """
    Context manager for template fragment caching
    Usage in templates: {% cache timeout fragment_name variables %}
    """
    return {"fragment_name": fragment_name, "timeout": timeout}

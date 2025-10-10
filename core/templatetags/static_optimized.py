from django import template
from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def static_css(path):
    """
    Load CSS file with automatic minification in production
    """
    # Check if we're in production and minified version exists
    if not settings.DEBUG:
        min_path = path.replace(".css", ".min.css")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<link rel="stylesheet" href="{url}">')


@register.simple_tag
def static_js(path):
    """
    Load JavaScript file with automatic minification in production
    """
    # Check if we're in production and minified version exists
    if not settings.DEBUG:
        min_path = path.replace(".js", ".min.js")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<script src="{url}"></script>')


@register.simple_tag
def preload_css(path):
    """
    Preload CSS file for better performance
    """
    if not settings.DEBUG:
        min_path = path.replace(".css", ".min.css")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<link rel="preload" href="{url}" as="style" onload="this.onload=null;this.rel=\'stylesheet\'">')


@register.simple_tag
def preload_js(path):
    """
    Preload JavaScript file for better performance
    """
    if not settings.DEBUG:
        min_path = path.replace(".js", ".min.js")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<link rel="preload" href="{url}" as="script">')


@register.simple_tag
def critical_css(css_content):
    """
    Inline critical CSS for above-the-fold content
    """
    return mark_safe(f"<style>{css_content}</style>")


@register.simple_tag
def defer_js(path):
    """
    Load JavaScript file with defer attribute
    """
    if not settings.DEBUG:
        min_path = path.replace(".js", ".min.js")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<script src="{url}" defer></script>')


@register.simple_tag
def async_js(path):
    """
    Load JavaScript file with async attribute
    """
    if not settings.DEBUG:
        min_path = path.replace(".js", ".min.js")
        if staticfiles_storage.exists(min_path):
            path = min_path

    url = staticfiles_storage.url(path)
    return mark_safe(f'<script src="{url}" async></script>')

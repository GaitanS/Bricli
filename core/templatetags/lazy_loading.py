import hashlib

from django import template
from django.utils import timezone
from django.utils.safestring import mark_safe

register = template.Library()


@register.simple_tag
def lazy_img(src, alt="", css_class="", width="", height="", placeholder_color="#f8f9fa", style="", **kwargs):
    """
    Generate a lazy-loaded image with placeholder
    """
    # Handle None or empty src
    if not src:
        src = ""

    # Convert src to string if it's not already
    src_str = str(src) if src else ""

    # Generate a unique ID for the image
    img_id = hashlib.md5(src_str.encode()).hexdigest()[:8]

    # Create placeholder SVG
    placeholder_svg = f"""data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='{width or 300}' height='{height or 200}' viewBox='0 0 {width or 300} {height or 200}'%3E%3Crect width='100%25' height='100%25' fill='{placeholder_color}'/%3E%3Ctext x='50%25' y='50%25' text-anchor='middle' dy='.3em' fill='%23999' font-family='Arial, sans-serif' font-size='14'%3EÎncarcare...%3C/text%3E%3C/svg%3E"""

    # Build CSS classes
    classes = f"lazy-image {css_class}".strip()

    # Build attributes
    attrs = []
    if width:
        attrs.append(f'width="{width}"')
    if height:
        attrs.append(f'height="{height}"')
    if style:
        attrs.append(f'style="{style}"')

    # Add any additional attributes from kwargs
    for key, value in kwargs.items():
        # Convert underscores to hyphens for HTML attributes (e.g., data_bs_toggle -> data-bs-toggle)
        attr_name = key.replace("_", "-")
        attrs.append(f'{attr_name}="{value}"')

    attrs_str = " ".join(attrs)

    # Use placeholder if src is empty or None
    actual_src = src_str if src_str else placeholder_svg

    html = f"""
    <img id="lazy-{img_id}" 
         class="{classes}" 
         src="{placeholder_svg}" 
         data-src="{actual_src}" 
         alt="{alt}" 
         {attrs_str}
         loading="lazy"
         onload="this.classList.add('loaded')"
         onerror="this.classList.add('error')">
    """

    return mark_safe(html)


@register.simple_tag
def lazy_bg(src, css_class="", height="200px"):
    """
    Generate a lazy-loaded background image
    """
    # Generate a unique ID for the background
    bg_id = hashlib.md5(src.encode()).hexdigest()[:8]

    classes = f"lazy-bg {css_class}".strip()

    html = f"""
    <div id="lazy-bg-{bg_id}" 
         class="{classes}" 
         data-bg="{src}" 
         style="height: {height}; background-color: #f8f9fa; background-image: url('data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'100\' height=\'100\' viewBox=\'0 0 100 100\'%3E%3Crect width=\'100%25\' height=\'100%25\' fill=\'%23f8f9fa\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' fill=\'%23999\' font-family=\'Arial, sans-serif\' font-size=\'12\'%3EÎncarcare...%3C/text%3E%3C/svg%3E');">
    </div>
    """

    return mark_safe(html)


@register.simple_tag
def lazy_content(content_id, load_url, placeholder="Se încarcă conținutul..."):
    """
    Generate a lazy-loaded content container
    """
    html = f"""
    <div id="{content_id}" 
         class="lazy-content" 
         data-load-url="{load_url}">
        <div class="lazy-placeholder text-center py-4 text-muted">
            <div class="spinner-border spinner-border-sm me-2" role="status">
                <span class="visually-hidden">Loading...</span>
            </div>
            {placeholder}
        </div>
    </div>
    """

    return mark_safe(html)


@register.inclusion_tag("core/lazy_loading_scripts.html")
def lazy_loading_scripts():
    """
    Include the lazy loading JavaScript
    """
    return {}


@register.simple_tag
def profile_img_version(user):
    """
    Return an integer timestamp suitable for cache-busting the user's profile image URL.
    Prefer the file's last modified time; fallback to user.updated_at or user.date_joined.
    """
    try:
        image = getattr(user, "profile_picture", None)
        if image and getattr(image, "name", None):
            storage = getattr(image, "storage", None)
            if storage:
                dt = storage.get_modified_time(image.name)
                if dt:
                    try:
                        return str(int(dt.timestamp()))
                    except Exception:
                        dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                        return str(int(dt.timestamp()))
        dt = getattr(user, "updated_at", None) or getattr(user, "date_joined", None) or timezone.now()
        return str(int(dt.timestamp()))
    except Exception:
        return str(int(timezone.now().timestamp()))


@register.simple_tag
def image_version(image, fallback_dt=None):
    """
    Return an integer timestamp for cache-busting a given ImageField/FileField.
    Prefer the file's last modified time; fallback to provided datetime or current time.
    """
    try:
        if image and getattr(image, "name", None):
            storage = getattr(image, "storage", None)
            if storage:
                dt = storage.get_modified_time(image.name)
                if dt:
                    try:
                        return str(int(dt.timestamp()))
                    except Exception:
                        dt = timezone.make_aware(dt) if timezone.is_naive(dt) else dt
                        return str(int(dt.timestamp()))
    except Exception:
        pass
    # Fallbacks
    if fallback_dt:
        try:
            return str(int(fallback_dt.timestamp()))
        except Exception:
            try:
                fallback_dt = timezone.make_aware(fallback_dt) if timezone.is_naive(fallback_dt) else fallback_dt
                return str(int(fallback_dt.timestamp()))
            except Exception:
                pass
    return str(int(timezone.now().timestamp()))

"""
Font Awesome 5 icon mapping for service categories
Central source of truth for category icons across all templates
"""

ICONS = {
    "acoperisuri": "fa-home",
    "asamblare-montaj": "fa-tools",
    "curatenie-menaj": "fa-broom",
    "design-interior": "fa-couch",
    "geamuri-ferestre": "fa-window-restore",
    "gradinarit-peisagistica": "fa-seedling",
    "instalatii-electrice": "fa-bolt",
    "instalatii-sanitare": "fa-bath",
    "it-tehnologie": "fa-laptop",
    "renovari-constructii": "fa-hammer",
}

DEFAULT_ICON = "fa-tools"


def get_category_icon(category_slug):
    """
    Get Font Awesome icon class for a category slug

    Args:
        category_slug: The slug of the category

    Returns:
        Font Awesome icon class (e.g., "fa-hammer")
    """
    return ICONS.get(category_slug, DEFAULT_ICON)

from django import template

register = template.Library()


@register.inclusion_tag("core/pagination.html", takes_context=True)
def optimized_pagination(context, page_obj, adjacent_pages=2):
    """
    Optimized pagination template tag that preserves query parameters
    and provides efficient page range calculation
    """
    request = context["request"]

    # Get current query parameters
    query_dict = request.GET.copy()
    if "page" in query_dict:
        del query_dict["page"]
    query_string = query_dict.urlencode()

    # Calculate page range efficiently
    current_page = page_obj.number
    total_pages = page_obj.paginator.num_pages

    # Calculate start and end pages for display
    start_page = max(1, current_page - adjacent_pages)
    end_page = min(total_pages, current_page + adjacent_pages)

    # Adjust if we're near the beginning or end
    if current_page <= adjacent_pages:
        end_page = min(total_pages, 2 * adjacent_pages + 1)
    elif current_page > total_pages - adjacent_pages:
        start_page = max(1, total_pages - 2 * adjacent_pages)

    page_range = range(start_page, end_page + 1)

    return {
        "page_obj": page_obj,
        "page_range": page_range,
        "query_string": query_string,
        "show_first": start_page > 1,
        "show_last": end_page < total_pages,
        "show_prev_ellipsis": start_page > 2,
        "show_next_ellipsis": end_page < total_pages - 1,
    }


@register.simple_tag
def page_url(query_string, page_number):
    """Generate URL for a specific page number while preserving query parameters"""
    if query_string:
        return f"?page={page_number}&{query_string}"
    return f"?page={page_number}"


@register.filter
def get_page_size_options(current_size=12):
    """Get available page size options"""
    options = [12, 24, 48, 96]
    if current_size not in options:
        options.append(current_size)
        options.sort()
    return options

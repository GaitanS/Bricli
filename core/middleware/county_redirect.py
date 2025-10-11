"""
301 Redirect Middleware for County ID → Slug in Query Parameters

This middleware handles permanent redirects from numeric county IDs
to county slugs in the query string for SEO-friendly URLs.
Only applies to GET requests.
"""

from django.http import HttpResponsePermanentRedirect
from django.utils.http import urlencode

from accounts.models import County


class CountySlugRedirectMiddleware:
    """
    301 redirects from ?county=<id> to ?county=<slug>

    Examples:
    - /cautare/?county=15 → /cautare/?county=bucuresti
    - /cautare/?q=instalatii&county=10 → /cautare/?q=instalatii&county=cluj
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only apply to GET requests with 'county' parameter
        if request.method == "GET" and "county" in request.GET:
            county_param = request.GET.get("county", "")

            # Check if it's a numeric ID
            if county_param.isdigit():
                try:
                    county = County.objects.get(pk=int(county_param))

                    # Only redirect if county has a slug
                    if county.slug:
                        # Build new query parameters with slug instead of ID
                        new_params = request.GET.copy()
                        new_params["county"] = county.slug

                        # Build new URL with updated query string
                        new_url = f"{request.path}?{urlencode(new_params)}"

                        # Return 301 Permanent Redirect
                        return HttpResponsePermanentRedirect(new_url)

                except (County.DoesNotExist, ValueError):
                    # Invalid ID - let the view handle it (will be ignored)
                    pass

        # No redirect needed, continue processing
        return self.get_response(request)

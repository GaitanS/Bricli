"""
301 Redirect Middleware for Old URLs to New Romanian ASCII URLs

This middleware handles permanent redirects from old English/mixed URLs
to new Romanian URLs without diacritics (ASCII-only for SEO stability).
"""

import re

from django.http import HttpResponsePermanentRedirect


class RomanianURLRedirectMiddleware:
    """
    301 redirects from old English/mixed URLs to new Romanian ASCII URLs

    Key changes:
    - services/* → servicii/*
    - accounts/mesterii/ → conturi/meseriasi/ (ș→s, ț→t)
    - accounts/mester/<slug>/ → conturi/meserias/<slug>/
    - accounts/inregistrare/ → inregistrare/ (root-level)
    - accounts/autentificare/ → autentificare/ (root-level)
    - messages/* → mesaje/*
    """

    # Mapping: (regex_pattern, replacement)
    REDIRECTS = [
        # Services → Servicii (all subpaths)
        (r"^/services/(.*)$", r"/servicii/\1"),
        # Old category detail URL (singular) → new (plural)
        (r"^/servicii/categorie/(.*)$", r"/servicii/categorii/\1"),
        # Accounts → Conturi (craftsmen list with diacritics removed)
        (r"^/accounts/mesterii/$", "/conturi/meseriasi/"),
        # Craftsman detail (mester → meserias, no diacritics)
        (r"^/accounts/mester/([^/]+)/$", r"/conturi/meserias/\1/"),
        # Profile/dashboard → Conturi
        (r"^/accounts/profil/(.*)$", r"/conturi/profil/\1"),
        (r"^/accounts/portofoliu/(.*)$", r"/conturi/portofoliu/\1"),
        (r"^/accounts/integrare/(.*)$", r"/conturi/integrare/\1"),
        # Auth → Root level
        (r"^/accounts/inregistrare/(.*)$", r"/inregistrare/\1"),
        (r"^/accounts/autentificare/$", "/autentificare/"),
        (r"^/accounts/deconectare/$", "/deconectare/"),
        (r"^/accounts/resetare-parola/(.*)$", r"/resetare-parola/\1"),
        # Messaging → Mesaje
        (r"^/messages/(.*)$", r"/mesaje/\1"),
        # Core old English routes
        (r"^/how-it-works/$", "/cum-functioneaza/"),
        (r"^/faq/$", "/intrebari-frecvente/"),
        (r"^/about/$", "/despre/"),
        (r"^/search/$", "/cautare/"),
        (r"^/contact/$", "/contact/"),  # Already Romanian-friendly
        (r"^/terms/$", "/termeni/"),
        (r"^/privacy/$", "/confidentialitate/"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response
        # Pre-compile regex patterns for performance
        self.compiled_redirects = [(re.compile(pattern), target) for pattern, target in self.REDIRECTS]

    def __call__(self, request):
        path = request.path

        # Check each redirect pattern
        for pattern, target in self.compiled_redirects:
            match = pattern.match(path)
            if match:
                # Perform regex substitution
                new_path = pattern.sub(target, path)

                # Preserve query string
                query_string = request.META.get("QUERY_STRING", "")
                if query_string:
                    new_path += "?" + query_string

                # Return 301 Permanent Redirect
                return HttpResponsePermanentRedirect(new_path)

        # No redirect needed, continue processing
        return self.get_response(request)

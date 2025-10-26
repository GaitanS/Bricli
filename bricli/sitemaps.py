# -*- coding: utf-8 -*-
"""
Sitemap configuration for Bricli
Helps Google crawl and index all important pages
"""

from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from blog.models import BlogPost
from core.models import CityLandingPage
from services.models import Order


class BlogPostSitemap(Sitemap):
    """Sitemap for blog articles"""
    changefreq = "weekly"
    priority = 0.8

    def items(self):
        return BlogPost.objects.filter(status='published')

    def lastmod(self, obj):
        return obj.updated_at


class CityLandingPageSitemap(Sitemap):
    """Sitemap for SEO city landing pages - HIGH PRIORITY"""
    changefreq = "monthly"
    priority = 0.9  # Very high priority for SEO

    def items(self):
        return CityLandingPage.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.updated_at


class PublicOrdersSitemap(Sitemap):
    """Sitemap for public orders"""
    changefreq = "daily"
    priority = 0.6

    def items(self):
        return Order.objects.filter(status='published').order_by('-created_at')[:100]

    def lastmod(self, obj):
        return obj.updated_at


class StaticViewSitemap(Sitemap):
    """Sitemap for static pages"""
    priority = 0.7
    changefreq = "monthly"

    def items(self):
        return [
            'core:home',
            'core:about',
            'core:how_it_works',
            'core:faq',
            'core:contact',
            'core:search',
            'blog:post_list',
        ]

    def location(self, item):
        return reverse(item)

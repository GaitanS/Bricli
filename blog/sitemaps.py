"""
Blog Sitemaps for SEO
Auto-generates sitemap.xml with all published blog posts
"""
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from .models import BlogPost, BlogCategory


class BlogPostSitemap(Sitemap):
    """
    Sitemap for blog posts
    Helps search engines discover and index blog content
    """
    changefreq = "monthly"
    priority = 0.8

    def items(self):
        """Return all published blog posts"""
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).order_by('-published_at')

    def lastmod(self, obj):
        """Last modification date"""
        return obj.updated_at

    def location(self, obj):
        """URL for the blog post"""
        return obj.get_absolute_url()


class BlogCategorySitemap(Sitemap):
    """
    Sitemap for blog categories
    """
    changefreq = "weekly"
    priority = 0.6

    def items(self):
        """Return all active categories"""
        return BlogCategory.objects.filter(is_active=True)

    def lastmod(self, obj):
        """Last modification date"""
        return obj.updated_at

    def location(self, obj):
        """URL for the category"""
        return obj.get_absolute_url()

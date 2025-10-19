from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from accounts.models import User


class BlogCategory(models.Model):
    """
    Blog content categories for organizing posts
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="FontAwesome icon class (e.g., fa-tools)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO Fields
    meta_title = models.CharField(max_length=60, blank=True, help_text="SEO title (max 60 chars)")
    meta_description = models.CharField(max_length=160, blank=True, help_text="SEO description (max 160 chars)")

    class Meta:
        verbose_name = "Categorie Blog"
        verbose_name_plural = "Categorii Blog"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})


class BlogTag(models.Model):
    """
    Tags for blog posts to improve discoverability
    """
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Tag Blog"
        verbose_name_plural = "Taguri Blog"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})


class BlogPost(models.Model):
    """
    SEO-optimized blog posts for driving organic traffic

    Content Strategy:
    - Pricing guides: "Cât costă renovarea unei băi în 2025?"
    - How-to guides: "Cum alegi meșterul potrivit pentru renovare?"
    - Comparisons: "Gresie vs. faianță: Ghidul complet 2025"
    - Local SEO: "Cei mai buni meseriași din [Oraș]"
    """

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    # Basic Fields
    title = models.CharField(max_length=200, help_text="Titlul articolului (H1)")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='blog_posts')
    category = models.ForeignKey(BlogCategory, on_delete=models.SET_NULL, null=True, related_name='posts')
    tags = models.ManyToManyField(BlogTag, blank=True, related_name='posts')

    # Content
    excerpt = models.TextField(max_length=300, help_text="Scurt rezumat (300 chars max)")
    content = models.TextField(help_text="Conținut complet (Markdown/HTML)")
    featured_image = models.ImageField(upload_to='blog/featured/', blank=True, null=True)
    featured_image_alt = models.CharField(max_length=200, blank=True, help_text="Alt text for SEO")

    # Publishing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # SEO Fields (Critical for Organic Traffic)
    meta_title = models.CharField(
        max_length=60,
        blank=True,
        help_text="SEO title (max 60 chars) - appears in Google search results"
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO description (max 160 chars) - appears in Google search results"
    )
    meta_keywords = models.CharField(
        max_length=255,
        blank=True,
        help_text="Cuvinte cheie separate prin virgulă (e.g., renovare baie, cost renovare)"
    )

    # Open Graph / Social Media
    og_image = models.ImageField(upload_to='blog/og/', blank=True, null=True, help_text="1200x630px recommended")
    og_title = models.CharField(max_length=100, blank=True)
    og_description = models.CharField(max_length=200, blank=True)

    # Analytics
    views_count = models.PositiveIntegerField(default=0)
    read_time_minutes = models.PositiveSmallIntegerField(default=5, help_text="Estimated reading time")

    # Schema.org structured data
    schema_type = models.CharField(
        max_length=50,
        default='Article',
        help_text="Schema.org type (Article, HowTo, FAQPage)"
    )

    class Meta:
        verbose_name = "Articol Blog"
        verbose_name_plural = "Articole Blog"
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['-published_at']),
            models.Index(fields=['status']),
            models.Index(fields=['slug']),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Auto-generate slug from title
        if not self.slug:
            self.slug = slugify(self.title)

        # Auto-set published_at when changing status to published
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Auto-generate meta fields if empty
        if not self.meta_title:
            self.meta_title = self.title[:60]
        if not self.meta_description:
            self.meta_description = self.excerpt[:160]
        if not self.og_title:
            self.og_title = self.title[:100]
        if not self.og_description:
            self.og_description = self.excerpt[:200]

        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def increment_views(self):
        """Increment the view count"""
        self.views_count += 1
        self.save(update_fields=['views_count'])

    @property
    def is_published(self):
        """Check if post is published"""
        return self.status == 'published' and self.published_at and self.published_at <= timezone.now()

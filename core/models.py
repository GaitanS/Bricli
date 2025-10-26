# -*- coding: utf-8 -*-
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class CityLandingPage(models.Model):
    """
    Landing pages pentru orașe specifice (SEO local)
    Exemplu: /instalator-brasov/, /electrician-cluj/
    """
    city_name = models.CharField(max_length=100, verbose_name="Nume oraș")
    city_slug = models.SlugField(max_length=100, unique=False, verbose_name="Slug oraș")

    profession = models.CharField(max_length=100, verbose_name="Meserie")
    profession_slug = models.SlugField(max_length=100, verbose_name="Slug meserie")

    # SEO
    meta_title = models.CharField(max_length=200, verbose_name="Meta Title")
    meta_description = models.TextField(max_length=300, verbose_name="Meta Description")
    h1_title = models.CharField(max_length=200, verbose_name="H1 Title")

    # Content
    intro_text = models.TextField(verbose_name="Text intro", help_text="Primul paragraf")
    services_text = models.TextField(verbose_name="Text servicii", help_text="Descriere servicii disponibile")
    prices_text = models.TextField(verbose_name="Text prețuri", blank=True, help_text="Informații despre prețuri orientative")
    how_it_works_text = models.TextField(verbose_name="Cum funcționează", help_text="Pași pentru găsirea meșterului")

    # Stats (opțional, pentru credibilitate)
    craftsmen_count = models.IntegerField(default=0, verbose_name="Număr meșteri", help_text="Ex: 45")
    reviews_count = models.IntegerField(default=0, verbose_name="Număr review-uri", help_text="Ex: 230")

    # Status
    is_active = models.BooleanField(default=True, verbose_name="Activ")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "City Landing Page"
        verbose_name_plural = "City Landing Pages"
        unique_together = ['city_slug', 'profession_slug']
        ordering = ['city_name', 'profession']

    def __str__(self):
        return f"{self.profession} {self.city_name}"

    def get_absolute_url(self):
        return reverse('core:city_landing', kwargs={
            'profession_slug': self.profession_slug,
            'city_slug': self.city_slug
        })

    def save(self, *args, **kwargs):
        if not self.city_slug:
            self.city_slug = slugify(self.city_name)
        if not self.profession_slug:
            self.profession_slug = slugify(self.profession)
        super().save(*args, **kwargs)


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default="Bricli")
    site_description = models.TextField(max_length=500, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=20, blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    linkedin_url = models.URLField(blank=True)

    # Trust indicators
    total_craftsmen = models.PositiveIntegerField(default=0)
    total_completed_jobs = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Site Settings"
        verbose_name_plural = "Site Settings"

    def __str__(self):
        return self.site_name


class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True)
    content = models.TextField(max_length=500)
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    image = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "-created_at"]

    def __str__(self):
        return f"{self.name} - {self.rating} stele"


class FAQ(models.Model):
    question = models.CharField(max_length=300)
    answer = models.TextField(max_length=1000)
    category = models.CharField(max_length=100, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["order", "question"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class CityLandingFAQ(models.Model):
    """
    FAQ specific to city landing pages for Schema.org FAQPage markup
    """
    landing_page = models.ForeignKey(
        CityLandingPage,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name="Landing Page"
    )
    question = models.CharField(max_length=300, verbose_name="Întrebare")
    answer = models.TextField(max_length=1000, verbose_name="Răspuns")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordine")
    is_active = models.BooleanField(default=True, verbose_name="Activ")

    class Meta:
        ordering = ["landing_page", "order", "question"]
        verbose_name = "City Landing FAQ"
        verbose_name_plural = "City Landing FAQs"

    def __str__(self):
        return f"{self.landing_page} - {self.question}"


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    excerpt = models.TextField(max_length=300, blank=True)
    featured_image = models.ImageField(upload_to="blog/", blank=True, null=True)

    is_published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-published_at", "-created_at"]

    def __str__(self):
        return self.title

from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils import timezone
from .models import BlogPost, BlogCategory, BlogTag


class BlogListView(ListView):
    """
    Display all published blog posts with pagination
    SEO-optimized for blog homepage
    """
    model = BlogPost
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        """Only show published posts, ordered by publish date"""
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = BlogCategory.objects.filter(is_active=True)
        context['popular_tags'] = BlogTag.objects.all()[:10]
        return context


class BlogPostDetailView(DetailView):
    """
    Display individual blog post with full SEO metadata
    Increments view count on each visit
    """
    model = BlogPost
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        """Only show published posts"""
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now()
        ).select_related('author', 'category').prefetch_related('tags')

    def get_object(self, queryset=None):
        """Increment view count when post is viewed"""
        obj = super().get_object(queryset)
        obj.increment_views()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Related posts from same category
        context['related_posts'] = BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
            category=self.object.category
        ).exclude(pk=self.object.pk).order_by('-published_at')[:3]

        return context


class BlogCategoryView(ListView):
    """
    Display all posts in a specific category
    SEO-optimized for category pages
    """
    model = BlogPost
    template_name = 'blog/category.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        """Filter posts by category slug"""
        self.category = get_object_or_404(BlogCategory, slug=self.kwargs['slug'], is_active=True)
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
            category=self.category
        ).select_related('author', 'category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['categories'] = BlogCategory.objects.filter(is_active=True)
        return context


class BlogTagView(ListView):
    """
    Display all posts with a specific tag
    SEO-optimized for tag pages
    """
    model = BlogPost
    template_name = 'blog/tag.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        """Filter posts by tag slug"""
        self.tag = get_object_or_404(BlogTag, slug=self.kwargs['slug'])
        return BlogPost.objects.filter(
            status='published',
            published_at__lte=timezone.now(),
            tags=self.tag
        ).select_related('author', 'category').order_by('-published_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['categories'] = BlogCategory.objects.filter(is_active=True)
        return context

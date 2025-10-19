"""
Blog URL Configuration
SEO-friendly URL structure for blog posts
"""
from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    # Blog homepage - list all posts
    path('', views.BlogListView.as_view(), name='post_list'),

    # Category filtering
    path('categorie/<slug:slug>/', views.BlogCategoryView.as_view(), name='category'),

    # Tag filtering
    path('tag/<slug:slug>/', views.BlogTagView.as_view(), name='tag'),

    # Individual blog post (must be last to avoid conflicts)
    path('<slug:slug>/', views.BlogPostDetailView.as_view(), name='post_detail'),
]

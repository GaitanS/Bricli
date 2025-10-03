from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from accounts.models import CraftsmanProfile
from services.models import Order, ServiceCategory, CraftsmanService
from core.cache_utils import CacheManager


@receiver([post_save, post_delete], sender=CraftsmanProfile)
def invalidate_craftsmen_cache(sender, **kwargs):
    """Invalidate craftsmen list cache when a craftsman profile is updated"""
    cache.delete_many(cache.keys('craftsmen_list:*'))
    cache.delete('counties_list')


@receiver([post_save, post_delete], sender=Order)
def invalidate_orders_cache(sender, **kwargs):
    """Invalidate orders cache when an order is updated"""
    cache.delete_many(cache.keys('available_orders:*'))
    cache.delete('service_categories_with_stats')


@receiver([post_save, post_delete], sender=ServiceCategory)
def invalidate_categories_cache(sender, **kwargs):
    """Invalidate service categories cache when a category is updated"""
    cache.delete('service_categories_with_stats')


@receiver([post_save, post_delete], sender=CraftsmanService)
def invalidate_craftsman_services_cache(sender, **kwargs):
    """Invalidate related caches when craftsman services are updated"""
    cache.delete_many(cache.keys('available_orders:*'))
    cache.delete_many(cache.keys('craftsmen_list:*'))
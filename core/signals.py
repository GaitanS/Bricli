from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from accounts.models import CraftsmanProfile
from core.cache_utils import CacheManager
from services.models import CraftsmanService, Order, ServiceCategory


@receiver([post_save, post_delete], sender=CraftsmanProfile)
def invalidate_craftsmen_cache(sender, **kwargs):
    """Invalidate craftsmen list cache when a craftsman profile is updated"""
    CacheManager.invalidate_craftsmen_cache()
    cache.delete("counties_list")


@receiver([post_save, post_delete], sender=Order)
def invalidate_orders_cache(sender, **kwargs):
    """Invalidate orders cache when an order is updated"""
    CacheManager.invalidate_available_orders_cache()
    cache.delete("service_categories_with_stats")


@receiver([post_save, post_delete], sender=ServiceCategory)
def invalidate_categories_cache(sender, **kwargs):
    """Invalidate service categories cache when a category is updated"""
    cache.delete("service_categories_with_stats")


@receiver([post_save, post_delete], sender=CraftsmanService)
def invalidate_craftsman_services_cache(sender, **kwargs):
    """Invalidate related caches when craftsman services are updated"""
    CacheManager.invalidate_available_orders_cache()
    CacheManager.invalidate_craftsmen_cache()

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def craftsman_required(view_func):
    """
    Decorator that requires the user to be a craftsman.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Trebuie să te autentifici pentru a accesa această pagină.')
            return redirect('accounts:login')
        
        if request.user.user_type != 'craftsman':
            messages.error(request, 'Doar meșterii pot accesa această pagină.')
            return redirect('core:home')
        
        if not hasattr(request.user, 'craftsman_profile'):
            messages.error(request, 'Trebuie să îți completezi profilul de meșter mai întâi.')
            return redirect('accounts:profile')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def client_required(view_func):
    """
    Decorator that requires the user to be a client.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Trebuie să te autentifici pentru a accesa această pagină.')
            return redirect('accounts:login')
        
        if request.user.user_type != 'client':
            messages.error(request, 'Doar clienții pot accesa această pagină.')
            return redirect('core:home')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def user_type_required(user_type):
    """
    Decorator that requires the user to have a specific user_type.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Trebuie să te autentifici pentru a accesa această pagină.')
                return redirect('accounts:login')
            
            if request.user.user_type != user_type:
                if user_type == 'craftsman':
                    messages.error(request, 'Doar meșterii pot accesa această pagină.')
                elif user_type == 'client':
                    messages.error(request, 'Doar clienții pot accesa această pagină.')
                else:
                    messages.error(request, 'Nu ai permisiunea să accesezi această pagină.')
                return redirect('core:home')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def order_owner_required(view_func):
    """
    Decorator that requires the user to be the owner of the order.
    Expects the order to be available as self.get_object() in class-based views
    or as a parameter in function-based views.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Trebuie să te autentifici pentru a accesa această pagină.')
            return redirect('accounts:login')
        
        # This decorator is meant to be used with views that have access to an order
        # The actual order ownership check should be done in the view itself
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class UserTypeMixin:
    """
    Mixin for class-based views that requires a specific user type.
    """
    required_user_type = None
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Trebuie să te autentifici pentru a accesa această pagină.')
            return redirect('accounts:login')
        
        if self.required_user_type and request.user.user_type != self.required_user_type:
            if self.required_user_type == 'craftsman':
                messages.error(request, 'Doar meșterii pot accesa această pagină.')
            elif self.required_user_type == 'client':
                messages.error(request, 'Doar clienții pot accesa această pagină.')
            else:
                messages.error(request, 'Nu ai permisiunea să accesezi această pagină.')
            return redirect('core:home')
        
        return super().dispatch(request, *args, **kwargs)


class CraftsmanRequiredMixin(UserTypeMixin):
    """
    Mixin that requires the user to be a craftsman with a complete profile.
    """
    required_user_type = 'craftsman'
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # If the parent dispatch returned a redirect, return it
        if hasattr(response, 'status_code') and response.status_code == 302:
            return response
        
        # Check if craftsman has a complete profile
        if not hasattr(request.user, 'craftsman_profile'):
            messages.error(request, 'Trebuie să îți completezi profilul de meșter mai întâi.')
            return redirect('accounts:profile')
        
        return response


class ClientRequiredMixin(UserTypeMixin):
    """
    Mixin that requires the user to be a client.
    """
    required_user_type = 'client'


def can_post_orders(user):
    """
    Check if user can post orders (clients only).
    """
    return user.is_authenticated and user.user_type == 'client'


def can_post_services(user):
    """
    Check if user can post services (craftsmen only).
    """
    return (user.is_authenticated and 
            user.user_type == 'craftsman' and 
            hasattr(user, 'craftsman_profile'))


def can_quote_on_order(user, order):
    """
    Check if user can quote on an order.
    """
    if not user.is_authenticated or user.user_type != 'craftsman':
        return False
    
    if not hasattr(user, 'craftsman_profile'):
        return False
    
    if order.status != 'published':
        return False
    
    # Check if craftsman already has a quote for this order
    if order.quotes.filter(craftsman=user.craftsman_profile).exists():
        return False
    
    return True


def can_accept_quote(user, quote):
    """
    Check if user can accept a quote.
    """
    return (user.is_authenticated and 
            quote.order.client == user and 
            quote.status == 'pending')


def can_review_order(user, order):
    """
    Check if user can review an order.
    """
    return (user.is_authenticated and 
            order.client == user and 
            order.status == 'completed' and 
            not hasattr(order, 'review'))

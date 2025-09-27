"""
Decorators for rate limiting and moderation
"""
from functools import wraps
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import check_rate_limit, RateLimit


def rate_limit(limit_type, redirect_url=None, template_name='moderation/rate_limited.html'):
    """
    Decorator pentru rate limiting pe acțiuni specifice
    
    Args:
        limit_type: Tipul de acțiune (din RateLimit.LIMIT_TYPES)
        redirect_url: URL de redirect în caz de depășire (opțional)
        template_name: Template pentru afișarea erorii
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            
            # Verifică rate limiting
            if not check_rate_limit(user, limit_type):
                # Obține detaliile limitei
                try:
                    rate_limit_obj = RateLimit.objects.get(user=user, limit_type=limit_type)
                    max_limit = rate_limit_obj.get_max_limit()
                    window_hours = rate_limit_obj.window_hours
                    
                    if window_hours == 24:
                        time_text = "24 de ore"
                    elif window_hours == 1:
                        time_text = "1 oră"
                    else:
                        time_text = f"{window_hours} ore"

                    error_message = (
                        f'Ai efectuat deja {max_limit} acțiuni în ultimele {time_text}. '
                        f'Pentru siguranța platformei, te rugăm să aștepți puțin înainte să încerci din nou.'
                    )
                    
                    if redirect_url:
                        messages.error(request, error_message)
                        return redirect(redirect_url)
                    else:
                        return render(request, template_name, {
                            'error_message': error_message,
                            'limit_type': limit_type,
                            'max_limit': max_limit,
                            'window_hours': window_hours
                        })
                        
                except RateLimit.DoesNotExist:
                    # Fallback error
                    messages.error(request, 'Ai efectuat prea multe acțiuni într-un timp scurt. Te rugăm să aștepți puțin.')
                    if redirect_url:
                        return redirect(redirect_url)
                    else:
                        return HttpResponseForbidden('Rate limit exceeded')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def order_creation_limit(view_func):
    """
    Rate limiting pentru crearea comenzilor
    """
    return rate_limit('order_creation', redirect_url='services:my_orders')(view_func)


def quote_creation_limit(view_func):
    """
    Rate limiting pentru crearea ofertelor
    """
    return rate_limit('quote_creation')(view_func)


def message_sending_limit(view_func):
    """
    Rate limiting pentru trimiterea mesajelor
    """
    return rate_limit('message_sending', redirect_url='messaging:conversation_list')(view_func)


def profile_update_limit(view_func):
    """
    Rate limiting pentru actualizările de profil
    """
    return rate_limit('profile_updates', redirect_url='accounts:profile')(view_func)


def review_creation_limit(view_func):
    """
    Rate limiting pentru crearea recenziilor
    """
    return rate_limit('review_creation')(view_func)


def new_user_restrictions(max_days=30):
    """
    Restricții suplimentare pentru utilizatori noi
    
    Args:
        max_days: Numărul de zile pentru a fi considerat utilizator nou
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            from django.utils import timezone
            from datetime import timedelta
            
            user = request.user
            
            # Verifică dacă utilizatorul este nou
            if user.date_joined > timezone.now() - timedelta(days=max_days):
                # Verificări suplimentare pentru utilizatori noi
                
                # Verifică dacă are email verificat
                if not user.is_verified:
                    messages.warning(
                        request, 
                        'Pentru a accesa această funcționalitate, trebuie să îți verifici adresa de email.'
                    )
                    return redirect('accounts:profile')
                
                # Verifică dacă are profil complet (pentru meșteri)
                if (hasattr(user, 'craftsman_profile') and 
                    user.craftsman_profile.profile_completion < 80):
                    messages.warning(
                        request,
                        'Pentru a accesa această funcționalitate, trebuie să îți completezi profilul (minim 80%).'
                    )
                    return redirect('accounts:edit_craftsman_profile')
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def check_user_status(view_func):
    """
    Verifică statusul utilizatorului (suspendat, banat, etc.)
    """
    @wraps(view_func)
    @login_required
    def _wrapped_view(request, *args, **kwargs):
        from .models import ModerationAction
        from django.utils import timezone
        
        user = request.user
        
        # Verifică pentru acțiuni de moderare active
        active_actions = ModerationAction.objects.filter(
            target_user=user,
            is_active=True
        ).exclude(
            expires_at__lt=timezone.now()
        )
        
        for action in active_actions:
            if action.action_type == 'account_ban':
                return render(request, 'moderation/account_banned.html', {
                    'action': action
                })
            elif action.action_type == 'account_suspension':
                if not action.is_expired():
                    return render(request, 'moderation/account_suspended.html', {
                        'action': action
                    })
                else:
                    # Dezactivează acțiunea expirată
                    action.is_active = False
                    action.save()
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class RateLimitMixin:
    """
    Mixin pentru class-based views cu rate limiting
    """
    rate_limit_type = None
    rate_limit_redirect_url = None
    
    def dispatch(self, request, *args, **kwargs):
        if self.rate_limit_type and request.user.is_authenticated:
            if not check_rate_limit(request.user, self.rate_limit_type):
                try:
                    rate_limit_obj = RateLimit.objects.get(
                        user=request.user, 
                        limit_type=self.rate_limit_type
                    )
                    max_limit = rate_limit_obj.get_max_limit()
                    window_hours = rate_limit_obj.window_hours
                    
                    if window_hours == 24:
                        time_text = "24 de ore"
                    elif window_hours == 1:
                        time_text = "1 oră"
                    else:
                        time_text = f"{window_hours} ore"

                    error_message = (
                        f'Ai efectuat deja {max_limit} acțiuni în ultimele {time_text}. '
                        f'Pentru siguranța platformei, te rugăm să aștepți puțin înainte să încerci din nou.'
                    )
                    
                    messages.error(request, error_message)
                    
                    if self.rate_limit_redirect_url:
                        return redirect(self.rate_limit_redirect_url)
                    else:
                        return render(request, 'moderation/rate_limited.html', {
                            'error_message': error_message
                        })
                        
                except RateLimit.DoesNotExist:
                    messages.error(request, 'Ai efectuat prea multe acțiuni într-un timp scurt. Te rugăm să aștepți puțin.')
                    return HttpResponseForbidden('Rate limit exceeded')
        
        return super().dispatch(request, *args, **kwargs)

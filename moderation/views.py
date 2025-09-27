"""
Views for moderation and reporting system
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView

from .models import Report, create_report
from .decorators import message_sending_limit


@login_required
@require_POST
@csrf_protect
def create_report_view(request):
    """
    Creează o raportare pentru conținut/utilizator
    """
    content_type_id = request.POST.get('content_type_id')
    object_id = request.POST.get('object_id')
    report_type = request.POST.get('report_type')
    description = request.POST.get('description', '').strip()
    
    if not all([content_type_id, object_id, report_type, description]):
        messages.error(request, 'Toate câmpurile sunt obligatorii.')
        return redirect(request.META.get('HTTP_REFERER', '/'))
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        # Verifică dacă utilizatorul nu a raportat deja acest conținut
        existing_report = Report.objects.filter(
            reporter=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if existing_report:
            messages.warning(request, 'Ai raportat deja acest conținut.')
            return redirect(request.META.get('HTTP_REFERER', '/'))
        
        # Creează raportarea
        report = create_report(
            reporter=request.user,
            content_object=content_object,
            report_type=report_type,
            description=description
        )
        
        messages.success(
            request, 
            'Raportarea a fost trimisă cu succes. Echipa noastră va analiza situația.'
        )
        
    except (ContentType.DoesNotExist, ValueError) as e:
        messages.error(request, 'A apărut o eroare la procesarea raportării.')
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


@login_required
def report_form_modal(request):
    """
    Returnează formularul de raportare pentru modal (AJAX)
    """
    content_type_id = request.GET.get('content_type_id')
    object_id = request.GET.get('object_id')
    
    if not content_type_id or not object_id:
        return JsonResponse({'error': 'Parametri lipsă'}, status=400)
    
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        context = {
            'content_type_id': content_type_id,
            'object_id': object_id,
            'content_object': content_object,
            'report_types': Report.REPORT_TYPES
        }
        
        html = render(request, 'moderation/report_form_modal.html', context).content.decode('utf-8')
        return JsonResponse({'html': html})
        
    except (ContentType.DoesNotExist, ValueError):
        return JsonResponse({'error': 'Conținut invalid'}, status=400)


class MyReportsView(LoginRequiredMixin, ListView):
    """
    Lista raportărilor făcute de utilizator
    """
    model = Report
    template_name = 'moderation/my_reports.html'
    context_object_name = 'reports'
    paginate_by = 20
    
    def get_queryset(self):
        return Report.objects.filter(reporter=self.request.user)


@login_required
def quick_report(request, content_type_id, object_id, report_type):
    """
    Raportare rapidă cu un singur click
    """
    try:
        content_type = ContentType.objects.get(id=content_type_id)
        content_object = content_type.get_object_for_this_type(id=object_id)
        
        # Verifică dacă utilizatorul nu a raportat deja
        existing_report = Report.objects.filter(
            reporter=request.user,
            content_type=content_type,
            object_id=object_id
        ).first()
        
        if existing_report:
            return JsonResponse({
                'success': False, 
                'message': 'Ai raportat deja acest conținut.'
            })
        
        # Creează raportarea cu descriere automată
        description_map = {
            'spam': 'Conținut marcat ca spam prin raportare rapidă',
            'inappropriate': 'Conținut nepotrivit marcat prin raportare rapidă',
            'fake_profile': 'Profil fals marcat prin raportare rapidă',
        }
        
        description = description_map.get(report_type, 'Raportare rapidă')
        
        report = create_report(
            reporter=request.user,
            content_object=content_object,
            report_type=report_type,
            description=description
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Conținutul a fost raportat cu succes.'
        })
        
    except (ContentType.DoesNotExist, ValueError):
        return JsonResponse({
            'success': False,
            'message': 'A apărut o eroare la procesarea raportării.'
        })


@login_required
def block_user_request(request, user_id):
    """
    Cerere de blocare utilizator (pentru moderatori)
    """
    # TODO: Implementează logica de blocare
    # Pentru moment, doar creează o raportare
    
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        target_user = get_object_or_404(User, id=user_id)
        
        # Creează o raportare pentru utilizator
        report = create_report(
            reporter=request.user,
            content_object=target_user,
            report_type='other',
            description=f'Cerere de blocare pentru utilizatorul {target_user.username}'
        )
        
        messages.success(
            request,
            'Cererea de blocare a fost trimisă către echipa de moderare.'
        )
        
    except Exception as e:
        messages.error(request, 'A apărut o eroare la procesarea cererii.')
    
    return redirect(request.META.get('HTTP_REFERER', '/'))


def rate_limited_view(request):
    """
    View pentru afișarea paginii de rate limiting
    """
    return render(request, 'moderation/rate_limited.html')


def ip_blocked_view(request):
    """
    View pentru afișarea paginii de IP blocat
    """
    return render(request, 'moderation/ip_blocked.html')


def account_suspended_view(request):
    """
    View pentru afișarea paginii de cont suspendat
    """
    return render(request, 'moderation/account_suspended.html')


def account_banned_view(request):
    """
    View pentru afișarea paginii de cont banat
    """
    return render(request, 'moderation/account_banned.html')


# Utility views for testing moderation features
@login_required
def test_rate_limit(request):
    """
    View pentru testarea rate limiting-ului
    """
    from .models import check_rate_limit
    
    if request.method == 'POST':
        limit_type = request.POST.get('limit_type', 'order_creation')
        
        if check_rate_limit(request.user, limit_type):
            messages.success(request, f'Acțiunea {limit_type} a fost permisă.')
        else:
            messages.error(request, f'Rate limit depășit pentru {limit_type}.')
    
    return render(request, 'moderation/test_rate_limit.html', {
        'limit_types': [choice[0] for choice in Report.REPORT_TYPES]
    })

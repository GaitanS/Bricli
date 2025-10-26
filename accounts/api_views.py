"""
API Views pentru verificare utilizator și autentificare
"""
from django.contrib.auth import get_user_model
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class CheckUserExistsView(View):
    """
    AJAX endpoint pentru verificare dacă email/telefon există în sistem

    Request: POST
    {
        "email": "user@example.com",
        "phone": "0740123456"
    }

    Response:
    {
        "exists": true/false,
        "field": "email"/"phone"/null,
        "message": "..."
    }
    """

    def post(self, request):
        import json

        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                'exists': False,
                'field': None,
                'message': 'Date invalide'
            }, status=400)

        email = data.get('email', '').strip()
        phone = data.get('phone', '').strip()

        # Verifică email
        if email:
            user = User.objects.filter(email__iexact=email).first()
            if user:
                return JsonResponse({
                    'exists': True,
                    'field': 'email',
                    'message': f'Cont existent pentru {email}'
                })

        # Verifică telefon
        if phone:
            # Normalizare telefon (elimină spații, liniuțe)
            clean_phone = ''.join(filter(str.isdigit, phone))

            # Verifică toate variantele (0740, +40740, 40740)
            user = User.objects.filter(
                phone_number__in=[
                    phone,
                    f'0{clean_phone[-9:]}' if len(clean_phone) >= 9 else phone,
                    f'+40{clean_phone[-9:]}' if len(clean_phone) >= 9 else phone,
                    f'40{clean_phone[-9:]}' if len(clean_phone) >= 9 else phone,
                ]
            ).first()

            if user:
                return JsonResponse({
                    'exists': True,
                    'field': 'phone',
                    'message': f'Cont existent pentru {phone}'
                })

        # Nu există utilizator
        return JsonResponse({
            'exists': False,
            'field': None,
            'message': 'Poți crea un cont nou'
        })


@method_decorator(csrf_exempt, name='dispatch')
class ResendCodeView(View):
    """
    AJAX endpoint pentru retrimite cod de verificare

    Request: POST (requires pending_user_id in session)
    Response:
    {
        "success": true/false,
        "message": "..."
    }
    """

    def post(self, request):
        from .verification_service import VerificationService

        user_id = request.session.get('pending_user_id')

        if not user_id:
            return JsonResponse({
                'success': False,
                'message': 'Nu există o verificare pendinte. Te rugăm să te înregistrezi din nou.'
            }, status=400)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'success': False,
                'message': 'Utilizatorul nu a fost găsit.'
            }, status=404)

        # Get last verification code method
        last_code = user.verification_codes.filter(is_used=False).order_by('-created_at').first()
        method = last_code.method if last_code else 'email'

        # Mark old codes as used
        user.verification_codes.filter(is_used=False).update(is_used=True)

        # Send new code
        verification_code = VerificationService.send_verification_code(user, method=method)

        if verification_code:
            method_display = {
                'email': 'email',
                'sms': 'SMS',
                'whatsapp': 'WhatsApp'
            }.get(method, 'email')

            return JsonResponse({
                'success': True,
                'message': f'Codul a fost retrimis pe {method_display}!'
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Eroare la trimiterea codului. Te rugăm să încerci mai târziu.'
            }, status=500)

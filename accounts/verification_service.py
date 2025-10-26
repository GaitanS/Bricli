"""
Serviciu de verificare cont prin cod (Email, SMS sau WhatsApp)
"""
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import VerificationCode


class VerificationService:
    """Serviciu pentru generare și trimitere coduri de verificare"""

    @staticmethod
    def send_verification_code(user, method='email'):
        """
        Generează și trimite cod de verificare

        Args:
            user: User instance
            method: 'email', 'sms' sau 'whatsapp'

        Returns:
            VerificationCode instance sau None dacă eșuează
        """
        # Generează cod
        verification_code = VerificationCode.generate_code(user, method=method)

        # Trimite codul bazat pe metodă
        if method == 'email':
            success = VerificationService._send_email_code(user, verification_code.code)
        elif method == 'sms':
            success = VerificationService._send_sms_code(user, verification_code.code)
        elif method == 'whatsapp':
            success = VerificationService._send_whatsapp_code(user, verification_code.code)
        else:
            return None

        if success:
            return verification_code
        else:
            # Șterge codul dacă trimiterea a eșuat
            verification_code.delete()
            return None

    @staticmethod
    def _send_email_code(user, code):
        """Trimite cod prin email"""
        try:
            subject = 'Cod de verificare Bricli'

            # Context pentru template
            context = {
                'user': user,
                'code': code,
                'code_formatted': f'{code[:3]} {code[3:]}',  # Formatare: 123 456
            }

            # Render HTML email
            html_message = render_to_string('accounts/emails/verification_code.html', context)
            plain_message = strip_tags(html_message)

            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False,
            )

            return True

        except Exception as e:
            print(f"Eroare trimitere email verificare: {e}")
            return False

    @staticmethod
    def _send_sms_code(user, code):
        """
        Trimite cod prin SMS folosind Twilio

        Args:
            user: User instance
            code: Codul de 6 cifre

        Returns:
            bool: True dacă trimiterea a avut succes
        """
        try:
            # Verifica daca user are numar de telefon
            if not user.phone_number:
                print("[ERROR] User nu are numar de telefon")
                return False

            # Verifica daca Twilio este configurat
            twilio_sid = settings.TWILIO_ACCOUNT_SID
            twilio_token = settings.TWILIO_AUTH_TOKEN
            twilio_phone = settings.TWILIO_PHONE_NUMBER

            if not all([twilio_sid, twilio_token, twilio_phone]):
                print("[WARNING] Twilio nu este configurat. Verifica setarile.")
                return False

            # Import Twilio (doar cand este necesar)
            from twilio.rest import Client

            # Creeaza client Twilio
            client = Client(twilio_sid, twilio_token)

            # Formateaza mesajul
            message_body = f"Codul tau de verificare Bricli este: {code}\n\nAcest cod va expira in 15 minute."

            # Trimite SMS
            message = client.messages.create(
                body=message_body,
                from_=twilio_phone,
                to=user.phone_number
            )

            print(f"[SUCCESS] SMS trimis cu succes! SID: {message.sid}")
            return True

        except Exception as e:
            print(f"[ERROR] Eroare trimitere SMS: {e}")
            return False

    @staticmethod
    def _send_whatsapp_code(user, code):
        """
        Trimite cod prin WhatsApp (OPȚIONAL - necesită setup)

        Implementare simplificată - poate fi extinsă cu:
        - pywhatkit (gratuit, necesită QR scan)
        - Twilio WhatsApp API (plătit, profesional)
        """
        try:
            # Verifică dacă user are număr de telefon
            if not user.phone_number:
                return False

            # TODO: Implementare WhatsApp
            # Opțiuni:
            # 1. pywhatkit.sendwhatmsg_instantly() - gratuit, necesită QR
            # 2. Twilio WhatsApp API - plătit, profesional
            # 3. WhatsApp Business API - oficial

            # Deocamdată, returnăm False (nu este implementat)
            print(f"WhatsApp verificare: {user.phone_number} - cod: {code}")
            print("⚠️  WhatsApp nu este încă configurat. Folosește Email.")

            return False

        except Exception as e:
            print(f"Eroare trimitere WhatsApp: {e}")
            return False

    @staticmethod
    def verify_code(user, code):
        """
        Verifică codul introdus de utilizator

        Args:
            user: User instance
            code: Codul de 6 cifre introdus

        Returns:
            (success: bool, message: str)
        """
        # Găsește cele mai recente coduri neutilizate
        verification_codes = user.verification_codes.filter(
            is_used=False
        ).order_by('-created_at')

        if not verification_codes.exists():
            return (False, "Nu există cod de verificare. Solicită un nou cod.")

        # Verifică codul
        for vc in verification_codes:
            if vc.code == code:
                if vc.is_valid():
                    # Marchează codul ca folosit
                    vc.is_used = True
                    vc.save()

                    # Activează utilizatorul
                    user.is_verified = True
                    user.is_active = True
                    user.save()

                    return (True, "Cont verificat cu succes!")
                else:
                    return (False, "Codul a expirat. Solicită un nou cod.")

        return (False, "Cod invalid. Verifică și încearcă din nou.")

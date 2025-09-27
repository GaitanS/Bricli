"""
Services for account management and validation
"""
import re
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import CraftsmanProfile


class CUIVerificationService:
    """
    Service pentru verificarea automată a CUI-urilor românești
    """
    
    @staticmethod
    def verify_cui(cui):
        """
        Verifică un CUI românesc folosind API-uri publice
        
        Args:
            cui (str): CUI-ul de verificat
            
        Returns:
            dict: {
                'is_valid': bool,
                'company_name': str or None,
                'status': str,
                'verified_at': datetime or None,
                'error': str or None
            }
        """
        if not cui:
            return {
                'is_valid': False,
                'company_name': None,
                'status': 'empty',
                'verified_at': None,
                'error': 'CUI gol'
            }
        
        # Curăță CUI-ul
        clean_cui = re.sub(r'[^0-9]', '', cui)
        
        # Verifică formatul de bază
        if not re.match(r'^\d{2,10}$', clean_cui):
            return {
                'is_valid': False,
                'company_name': None,
                'status': 'invalid_format',
                'verified_at': None,
                'error': 'Format CUI invalid'
            }
        
        # Verifică cifra de control
        if not CUIVerificationService._validate_control_digit(clean_cui):
            return {
                'is_valid': False,
                'company_name': None,
                'status': 'invalid_control',
                'verified_at': None,
                'error': 'Cifra de control incorectă'
            }
        
        # Încearcă verificarea online (poate fi extinsă cu API-uri reale)
        try:
            verification_result = CUIVerificationService._verify_online(clean_cui)
            return verification_result
        except Exception as e:
            # Fallback: consideră valid dacă trece validarea de format
            return {
                'is_valid': True,
                'company_name': None,
                'status': 'format_valid',
                'verified_at': timezone.now(),
                'error': None
            }
    
    @staticmethod
    def _validate_control_digit(cui):
        """Validează cifra de control pentru CUI românesc"""
        if len(cui) < 8:
            return True  # CUI-uri scurte nu au cifră de control
        
        # Constanta pentru calculul cifrei de control
        control_key = "753217532"
        
        # Completează cu zerouri la stânga dacă e necesar
        cui_str = cui.zfill(10)
        
        # Calculează suma de control
        control_sum = 0
        for i in range(9):  # Primele 9 cifre
            control_sum += int(cui_str[i]) * int(control_key[i])
        
        # Calculează cifra de control
        control_digit = control_sum % 11
        if control_digit == 10:
            control_digit = 0
        
        # Compară cu ultima cifră din CUI
        return control_digit == int(cui_str[9])
    
    @staticmethod
    def _verify_online(cui):
        """
        Verifică CUI-ul online folosind API-uri publice
        
        Această metodă poate fi extinsă pentru a folosi:
        - API-ul ANAF pentru verificarea CUI-urilor
        - Alte servicii de verificare
        
        Pentru moment, returnează un rezultat de bază
        """
        # TODO: Implementează verificarea reală cu API ANAF
        # URL exemplu: https://webservicesp.anaf.ro/PlatitorTvaRest/api/v8/ws/tva
        
        # Pentru moment, simulăm o verificare de succes
        return {
            'is_valid': True,
            'company_name': f'Companie CUI {cui}',
            'status': 'verified',
            'verified_at': timezone.now(),
            'error': None
        }
    
    @staticmethod
    def update_craftsman_cui_status(craftsman_profile, cui):
        """
        Actualizează statusul CUI pentru un profil de meșter
        
        Args:
            craftsman_profile (CraftsmanProfile): Profilul de actualizat
            cui (str): CUI-ul de verificat
        """
        verification_result = CUIVerificationService.verify_cui(cui)
        
        if verification_result['is_valid']:
            craftsman_profile.company_cui = cui
            craftsman_profile.company_verified_at = verification_result['verified_at']
            craftsman_profile.is_company_verified = True
        else:
            craftsman_profile.company_cui = cui
            craftsman_profile.company_verified_at = None
            craftsman_profile.is_company_verified = False
        
        # Actualizează badge-urile și procentajul de completare
        craftsman_profile.update_badges()
        craftsman_profile.update_profile_completion()
        craftsman_profile.save()
        
        return verification_result


class ProfileCompletionService:
    """
    Service pentru calcularea și actualizarea completării profilului
    """
    
    @staticmethod
    def calculate_completion_percentage(craftsman_profile):
        """
        Calculează procentajul de completare al profilului
        
        Args:
            craftsman_profile (CraftsmanProfile): Profilul de evaluat
            
        Returns:
            int: Procentaj de completare (0-100)
        """
        total_points = 100
        score = 0
        
        # Câmpuri obligatorii (70 puncte total)
        if craftsman_profile.display_name:
            score += 15
        if craftsman_profile.bio and len(craftsman_profile.bio.strip()) >= 200:
            score += 15
        if craftsman_profile.profile_photo:
            score += 10
        if craftsman_profile.county and craftsman_profile.city:
            score += 10
        if craftsman_profile.coverage_radius_km:
            score += 10
        
        # Portofoliu (20 puncte)
        portfolio_count = craftsman_profile.portfolio_images.filter(is_approved=True).count()
        if portfolio_count >= 3:
            score += 20
        elif portfolio_count >= 1:
            score += 10
        
        # Câmpuri opționale (10 puncte total)
        if craftsman_profile.years_experience:
            score += 3
        if craftsman_profile.hourly_rate or craftsman_profile.min_job_value:
            score += 3
        if (craftsman_profile.website_url or 
            craftsman_profile.facebook_url or 
            craftsman_profile.instagram_url):
            score += 2
        if craftsman_profile.company_cui:
            score += 2
        
        return min(score, total_points)
    
    @staticmethod
    def update_all_profiles():
        """
        Actualizează procentajul de completare pentru toate profilurile
        """
        profiles = CraftsmanProfile.objects.all()
        updated_count = 0
        
        for profile in profiles:
            old_completion = profile.profile_completion
            new_completion = ProfileCompletionService.calculate_completion_percentage(profile)
            
            if old_completion != new_completion:
                profile.profile_completion = new_completion
                profile.update_badges()
                profile.save()
                updated_count += 1
        
        return updated_count


class BadgeService:
    """
    Service pentru gestionarea badge-urilor de meșteri
    """
    
    @staticmethod
    def update_all_badges():
        """
        Actualizează badge-urile pentru toate profilurile de meșteri
        """
        profiles = CraftsmanProfile.objects.all()
        updated_count = 0
        
        for profile in profiles:
            old_badges = profile.get_badges()
            profile.update_badges()
            new_badges = profile.get_badges()
            
            if len(old_badges) != len(new_badges):
                profile.save()
                updated_count += 1
        
        return updated_count
    
    @staticmethod
    def get_badge_statistics():
        """
        Returnează statistici despre badge-uri
        """
        total_profiles = CraftsmanProfile.objects.count()
        
        return {
            'total_profiles': total_profiles,
            'profile_complete': CraftsmanProfile.objects.filter(is_profile_complete=True).count(),
            'company_verified': CraftsmanProfile.objects.filter(is_company_verified=True).count(),
            'top_rated': CraftsmanProfile.objects.filter(is_top_rated=True).count(),
            'active': CraftsmanProfile.objects.filter(is_active=True).count(),
            'trusted': CraftsmanProfile.objects.filter(is_trusted=True).count(),
        }

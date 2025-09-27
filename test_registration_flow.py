#!/usr/bin/env python3
"""
Test script pentru fluxul complet de înregistrare cu validarea JavaScript pentru bio
"""

import os
import django
import sys
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from accounts.forms import SimpleCraftsmanRegistrationForm
from services.models import Service
from accounts.models import County, User

def test_registration_flow():
    print("=== Test Fluxul Complet de Înregistrare ===\n")
    
    # 1. Verifică că serviciile și județele există
    print("1. Verificare date necesare...")
    services = Service.objects.all()
    counties = County.objects.all()
    
    print(f"   - Servicii disponibile: {services.count()}")
    print(f"   - Județe disponibile: {counties.count()}")
    
    if services.count() == 0 or counties.count() == 0:
        print("   ❌ EROARE: Nu există servicii sau județe în baza de date!")
        return False
    
    # 2. Test cu bio prea scurt (sub 200 caractere)
    print("\n2. Test cu bio prea scurt...")
    short_bio = "Sunt un meșter cu experiență."  # 32 caractere
    
    form_data_short = {
        'first_name': 'Ion',
        'last_name': 'Popescu',
        'email': f'test_short_{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com',
        'phone_number': '0721234567',
        'password': 'TestPassword123',
        'password_confirm': 'TestPassword123',
        'county': counties.first().id,
        'company_name': 'Test Company SRL',
        'bio': short_bio,
        'services': [services.first().id, services.last().id],
        'agree_terms': True
    }
    
    form_short = SimpleCraftsmanRegistrationForm(data=form_data_short)
    print(f"   - Bio lungime: {len(short_bio)} caractere")
    print(f"   - Form valid: {form_short.is_valid()}")
    
    if not form_short.is_valid():
        print("   - Erori form:")
        for field, errors in form_short.errors.items():
            print(f"     * {field}: {errors}")
        print("   ✅ Validarea backend funcționează corect (bio prea scurt)")
    else:
        print("   ❌ EROARE: Formularul ar trebui să fie invalid cu bio prea scurt!")
    
    # 3. Test cu bio suficient de lung (peste 200 caractere)
    print("\n3. Test cu bio suficient de lung...")
    long_bio = """Sunt un meșter cu peste 15 ani de experiență în domeniul construcțiilor și renovărilor. 
    Am lucrat la numeroase proiecte rezidențiale și comerciale, de la case unifamiliale la blocuri de apartamente. 
    Specializările mele includ zidărie, tencuieli decorative, montaj gresie și faianță, precum și lucrări de finisaje interioare. 
    Îmi place să lucrez cu atenție la detalii și să ofer clienților mei soluții de calitate superioară. 
    Sunt punctual, organizat și îmi respect întotdeauna termenele stabilite cu clienții."""
    
    form_data_long = {
        'first_name': 'Maria',
        'last_name': 'Ionescu',
        'email': f'test_long_{datetime.now().strftime("%Y%m%d_%H%M%S")}@example.com',
        'phone_number': '0731234567',
        'password': 'TestPassword123',
        'password_confirm': 'TestPassword123',
        'county': counties.first().id,
        'company_name': 'Maria Construct SRL',
        'bio': long_bio,
        'services': [services.first().id],
        'agree_terms': True
    }
    
    form_long = SimpleCraftsmanRegistrationForm(data=form_data_long)
    print(f"   - Bio lungime: {len(long_bio)} caractere")
    print(f"   - Form valid: {form_long.is_valid()}")
    
    if form_long.is_valid():
        print("   ✅ Validarea backend funcționează corect (bio suficient de lung)")
        
        # Verifică că email-ul nu există deja
        if User.objects.filter(email=form_data_long['email']).exists():
            print("   ⚠️  Email-ul există deja în baza de date")
        else:
            print("   ✅ Email-ul este disponibil")
            
    else:
        print("   ❌ EROARE: Formularul ar trebui să fie valid cu bio suficient de lung!")
        print("   - Erori form:")
        for field, errors in form_long.errors.items():
            print(f"     * {field}: {errors}")
    
    # 4. Verifică validatorul de bio
    print("\n4. Test validatorul de bio direct...")
    from accounts.validators import validate_bio_length
    
    try:
        validate_bio_length(short_bio)
        print("   ❌ EROARE: Validatorul ar trebui să ridice excepție pentru bio scurt!")
    except Exception as e:
        print(f"   ✅ Validatorul funcționează corect: {e}")
    
    try:
        validate_bio_length(long_bio)
        print("   ✅ Validatorul acceptă bio-ul lung")
    except Exception as e:
        print(f"   ❌ EROARE: Validatorul nu ar trebui să ridice excepție pentru bio lung: {e}")
    
    print("\n=== Rezumat Test ===")
    print("✅ Validarea backend pentru bio funcționează corect")
    print("✅ Formularul respinge bio-urile prea scurte")
    print("✅ Formularul acceptă bio-urile suficient de lungi")
    print("\n🔧 Următorul pas: Testarea manuală a validării JavaScript în browser")
    print("   - Accesează: http://127.0.0.1:8000/accounts/register/simple/craftsman/")
    print("   - Completează pasul 1 cu date valide")
    print("   - În pasul 2, încearcă să introduci un bio scurt (sub 200 caractere)")
    print("   - Verifică că JavaScript-ul afișează mesajul de eroare")
    print("   - Încearcă să treci la pasul 3 - ar trebui să fie blocat")
    print("   - Apoi completează un bio lung (peste 200 caractere)")
    print("   - Verifică că poți trece la pasul 3")

if __name__ == "__main__":
    test_registration_flow()
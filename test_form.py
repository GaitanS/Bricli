#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bricli.settings')
django.setup()

from accounts.forms import SimpleCraftsmanRegistrationForm
from services.models import Service
from accounts.models import County, User

def test_form():
    # Check if we have services and counties
    services = Service.objects.all()[:2]
    counties = County.objects.all()[:1]

    print(f'Services available: {len(services)}')
    print(f'Counties available: {len(counties)}')

    if services and counties:
        # Test form validation
        form_data = {
            'first_name': 'Ion',
            'last_name': 'Popescu',
            'email': 'test123@test.com',
            'phone_number': '0721234567',
            'password': 'Test123!',
            'password_confirm': 'Test123!',
            'county': counties[0].id,
            'company_name': 'Test Company',
            'bio': 'Aceasta este o biografie de test suficient de lunga pentru validare si testare. Sunt un meșteșugar cu experiență vastă în domeniul construcțiilor și renovărilor. Am lucrat la numeroase proiecte de-a lungul anilor, de la renovări simple la construcții complexe. Îmi place să lucrez cu atenție la detalii și să ofer servicii de calitate superioară clienților mei. Experiența mea include lucrări de zidărie, tencuieli, vopsitorii și multe altele.',
            'services': [s.id for s in services],
        }
        
        form = SimpleCraftsmanRegistrationForm(data=form_data)
        print(f'Form is valid: {form.is_valid()}')
        
        if not form.is_valid():
            print('Form errors:')
            for field, errors in form.errors.items():
                print(f'  {field}: {errors}')
        else:
            print('Form validation passed!')
            
            # Check if email already exists
            if User.objects.filter(email=form_data['email']).exists():
                print('Email already exists in database')
            else:
                print('Email is available')
    else:
        print('Missing services or counties in database')

if __name__ == '__main__':
    test_form()
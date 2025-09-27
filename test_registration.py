import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bricli.settings")
django.setup()

from accounts.models import User, CraftsmanProfile, County
from services.models import Service

# Test data
county = County.objects.first()
service = Service.objects.first()

print(f"County: {county}")
print(f"Service: {service}")

# Test creating user and profile
user_data = {
    "first_name": "Test",
    "last_name": "Craftsman", 
    "email": "test@example.com",
    "phone_number": "0721234567",
    "password": "TestPassword123",
    "county": county,
    "bio": "Test bio pentru craftsman cu peste 200 de caractere pentru a respecta validarea minimă. Aceasta este o descriere detaliată a serviciilor oferite de către meșterul de test care demonstrează experiența și competențele sale în domeniu."
}

print("Testing user creation...")
try:
    # Check if user exists
    if User.objects.filter(email=user_data["email"]).exists():
        print("User already exists, deleting...")
        User.objects.filter(email=user_data["email"]).delete()
    
    # Create user
    user = User.objects.create_user(
        username=user_data["email"],
        email=user_data["email"],
        first_name=user_data["first_name"],
        last_name=user_data["last_name"],
        phone_number=user_data["phone_number"],
        password=user_data["password"],
        user_type="craftsman"
    )
    print(f"User created: {user}")
    
    # Create profile
    profile = CraftsmanProfile.objects.create(
        user=user,
        county=user_data["county"],
        bio=user_data["bio"]
    )
    print(f"Profile created: {profile}")
    
    print("SUCCESS: User and profile created successfully!")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()


import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bricli.settings")
import django

django.setup()

from django.core.files.storage import default_storage

from accounts.models import CraftsmanProfile

CP_ID = 10

cp = CraftsmanProfile.objects.get(id=CP_ID)
fixed = 0
print("MEDIA_ROOT", os.path.abspath(str(__import__("bricli.settings").settings.MEDIA_ROOT)))
print("MEDIA_URL", __import__("bricli.settings").settings.MEDIA_URL)
print("Portfolio count", cp.portfolio_images.count())

for p in cp.portfolio_images.all():
    name = p.image.name.replace("\\", "/")
    exists = default_storage.exists(name)
    print("Before: ID", p.id, "name", repr(name), "exists", exists)
    if name.startswith("media/"):
        new_name = name[len("media/") :]
        print("Fixing to ->", new_name)
        p.image.name = new_name
        p.save(update_fields=["image"])
        fixed += 1

print("Fixed records:", fixed)

for p in cp.portfolio_images.all():
    name = p.image.name.replace("\\", "/")
    exists = default_storage.exists(name)
    print("After: ID", p.id, "name", repr(name), "exists", exists, "url", getattr(p.image, "url", None))

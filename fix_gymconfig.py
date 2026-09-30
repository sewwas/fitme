import os, sys, django
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings.local_dev'
sys.path.insert(0, '.')
django.setup()

from django.contrib.auth import get_user_model
from wger.core.models import UserProfile

User = get_user_model()

# Fix all users who are missing a UserProfile (e.g. the admin created before Site existed)
fixed = 0
for user in User.objects.all():
    if not UserProfile.objects.filter(user=user).exists():
        UserProfile.objects.create(user=user)
        print(f'  Created UserProfile for: {user.username}')
        fixed += 1

if fixed == 0:
    print('  All users already have a UserProfile.')
else:
    print(f'Fixed {fixed} user(s). Login should now work.')

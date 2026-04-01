import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import get_user_model
from allauth.account.models import EmailAddress

User = get_user_model()

def fix_users():
    users = User.objects.all()
    count = 0
    print(f"Sprawdzanie {users.count()} użytkowników...")
    
    for user in users:
        # Sprawdź czy użytkownik ma rekord EmailAddress i czy jest zweryfikowany
        email_obj, created = EmailAddress.objects.get_or_create(
            user=user, 
            email=user.email,
            defaults={'verified': True, 'primary': True}
        )
        
        if not email_obj.verified:
            email_obj.verified = True
            email_obj.save()
            count += 1
            print(f"Zweryfikowano: {user.email}")

    print(f"Gotowe! Naprawiono {count} rekordów.")

if __name__ == "__main__":
    fix_users()

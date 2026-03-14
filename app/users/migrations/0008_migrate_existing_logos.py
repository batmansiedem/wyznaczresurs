from django.db import migrations

def migrate_logos(apps, schema_editor):
    CustomUser = apps.get_model('users', 'CustomUser')
    UserLogo = apps.get_model('users', 'UserLogo')
    
    for user in CustomUser.objects.all():
        if user.custom_logo:
            # Create a UserLogo entry for existing custom_logo
            UserLogo.objects.create(
                user=user,
                image=user.custom_logo,
                width=user.logo_width,
                height=user.logo_height,
                position=user.logo_position,
                theme_color=user.theme_color,
                name="Logo główne",
                is_default=True
            )

def reverse_migrate_logos(apps, schema_editor):
    UserLogo = apps.get_model('users', 'UserLogo')
    UserLogo.objects.all().delete()

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_userlogo'),
    ]

    operations = [
        migrations.RunPython(migrate_logos, reverse_migrate_logos),
    ]

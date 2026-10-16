# Generated manually for Fit Me site domain configuration

from django.db import migrations


def update_site_domain(apps, schema_editor):
    Site = apps.get_model('sites', 'Site')
    # Update or create default site to production domain
    site = Site.objects.filter(pk=1).first()
    if site:
        site.domain = 'fitme-backend-mucu.onrender.com'
        site.name = 'Fit Me Fitness Club'
        site.save()
    else:
        Site.objects.create(
            pk=1,
            domain='fitme-backend-mucu.onrender.com',
            name='Fit Me Fitness Club'
        )


def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0029_userprofile_timezone'),
        ('sites', '0002_alter_domain_unique'),
    ]

    operations = [
        migrations.RunPython(update_site_domain, reverse_func),
    ]

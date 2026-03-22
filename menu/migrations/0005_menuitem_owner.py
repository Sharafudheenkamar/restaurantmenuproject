from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('menu', '0004_table_owner_and_constraints'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='menu_items',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]

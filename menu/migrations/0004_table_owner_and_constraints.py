from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('menu', '0003_alter_tableqr_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='table',
            name='owner',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='tables',
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AlterField(
            model_name='table',
            name='number',
            field=models.PositiveIntegerField(),
        ),
        migrations.AddConstraint(
            model_name='table',
            constraint=models.UniqueConstraint(fields=('owner', 'number'), name='unique_table_number_per_owner'),
        ),
        migrations.AlterModelOptions(
            name='table',
            options={'ordering': ['number']},
        ),
    ]

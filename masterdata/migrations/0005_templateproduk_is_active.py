from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("masterdata", "0004_ro_and_store_profile"),
    ]

    operations = [
        migrations.AddField(
            model_name="templateproduk",
            name="is_active",
            field=models.BooleanField(default=True, verbose_name="Aktif"),
        ),
    ]

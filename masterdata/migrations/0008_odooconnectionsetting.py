from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("masterdata", "0007_dapur_operation_types")]
    operations = [
        migrations.CreateModel(
            name="OdooConnectionSetting",
            fields=[
                ("id", models.PositiveSmallIntegerField(default=1, editable=False, primary_key=True, serialize=False)),
                ("base_url", models.URLField(max_length=500)),
                ("database", models.CharField(blank=True, max_length=120)),
                ("username", models.CharField(max_length=150)),
                ("api_key_encrypted", models.TextField()),
                ("last_tested_at", models.DateTimeField(blank=True, null=True)),
                ("connection_status", models.CharField(blank=True, max_length=20)),
                ("connection_message", models.CharField(blank=True, max_length=500)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={"verbose_name": "Pengaturan Koneksi Odoo"},
        ),
    ]

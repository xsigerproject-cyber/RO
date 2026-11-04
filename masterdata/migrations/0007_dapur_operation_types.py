from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("masterdata", "0006_templateproduk_is_active"),
    ]

    operations = [
        migrations.AddField(
            model_name="dapur",
            name="operation_type_kirim",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="dapur",
            name="operation_type_terima",
            field=models.CharField(default="", max_length=120),
            preserve_default=False,
        ),
    ]

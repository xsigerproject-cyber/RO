from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Dapur(models.Model):
    kode_dapur = models.PositiveIntegerField(primary_key=True)
    nama_dapur = models.CharField(max_length=120)
    operation_type = models.CharField(max_length=120)
    document = models.CharField(max_length=60)

    class Meta:
        ordering = ["kode_dapur"]

    def __str__(self):
        return f"{self.kode_dapur} - {self.nama_dapur}"


class Jadwal(models.Model):
    kode_jadwal = models.PositiveIntegerField(primary_key=True)
    jadwal_kirim = models.CharField(max_length=120)

    class Meta:
        ordering = ["kode_jadwal"]

    def __str__(self):
        return self.jadwal_kirim


class Toko(models.Model):
    kode_toko = models.PositiveIntegerField(primary_key=True)
    nama_toko = models.CharField(max_length=120)

    class Meta:
        ordering = ["kode_toko"]

    def __str__(self):
        return self.nama_toko


class TemplateProduk(models.Model):
    kode_produk = models.PositiveIntegerField(primary_key=True)
    nama_produk = models.CharField(max_length=160)
    dapur = models.ForeignKey(
        Dapur,
        on_delete=models.PROTECT,
        related_name="produk",
    )

    class Meta:
        ordering = ["kode_produk"]

    def __str__(self):
        return self.nama_produk


class UserProfile(models.Model):
    THEME_CHOICES = [
        ("light", "Light"),
        ("dark", "Dark"),
        ("ocean", "Ocean"),
        ("forest", "Forest"),
        ("sunset", "Sunset"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default="light",
    )

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.username} - {self.theme}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, "profile"):
        instance.profile.save()
    else:
        UserProfile.objects.get_or_create(user=instance)

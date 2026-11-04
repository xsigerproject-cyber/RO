from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Dapur(models.Model):
    kode_dapur = models.PositiveIntegerField(primary_key=True)
    nama_dapur = models.CharField(max_length=120)
    operation_type = models.CharField(max_length=120)
    operation_type_kirim = models.CharField(max_length=120)
    operation_type_terima = models.CharField(max_length=120)
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
    is_active = models.BooleanField(default=True, verbose_name="Aktif")

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
    toko = models.ForeignKey(
        Toko,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="admin_users",
        help_text="Wajib diisi untuk akun dengan role Admin Toko.",
    )

    class Meta:
        db_table = "user_profiles"

    def __str__(self):
        return f"{self.user.username} - {self.theme}"


class RO(models.Model):
    STATUS_DRAFT = 1
    STATUS_SENT = 2
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_SENT, "Terkirim"),
    ]

    id_ro = models.BigAutoField(primary_key=True)
    toko = models.ForeignKey(Toko, on_delete=models.PROTECT, related_name="ro_items")
    tgl_ro = models.DateField()
    tgl_produksi = models.DateField(null=True, blank=True)
    jadwal = models.ForeignKey(Jadwal, on_delete=models.PROTECT, related_name="ro_items")
    tgl_kirim = models.DateField()
    dapur = models.ForeignKey(Dapur, on_delete=models.PROTECT, related_name="ro_items")
    produk = models.ForeignKey(TemplateProduk, on_delete=models.PROTECT, related_name="ro_items")
    qty_pesan = models.PositiveIntegerField(default=0)
    status_ro = models.PositiveSmallIntegerField(choices=STATUS_CHOICES, default=STATUS_DRAFT)
    dibuat_oleh = models.ForeignKey(User, on_delete=models.PROTECT, related_name="ro_dibuat")
    dibuat_pada = models.DateTimeField(auto_now_add=True)
    diubah_pada = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["produk__kode_produk"]
        constraints = [
            models.UniqueConstraint(
                fields=["tgl_ro", "toko", "dapur", "jadwal", "produk"],
                name="uniq_ro_key_prod",
            )
        ]
        indexes = [
            models.Index(fields=["tgl_ro", "toko", "dapur", "jadwal"]),
            models.Index(fields=["status_ro", "tgl_kirim"]),
        ]

    def __str__(self):
        return f"RO {self.tgl_ro} - {self.toko} - {self.produk}"


# Signal membuat profil untuk user baru dan memastikan profil tersedia.
@receiver(post_save, sender=User)
def create_or_save_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
    else:
        UserProfile.objects.get_or_create(user=instance)


class OdooConnectionSetting(models.Model):
    """Konfigurasi satu koneksi Odoo; API key disimpan terenkripsi."""
    base_url = models.URLField(max_length=500)
    database = models.CharField(max_length=120, blank=True)
    username = models.CharField(max_length=150)
    api_key_encrypted = models.TextField()
    last_tested_at = models.DateTimeField(null=True, blank=True)
    connection_status = models.CharField(max_length=20, blank=True)
    connection_message = models.CharField(max_length=500, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Pengaturan Koneksi Odoo"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return "Pengaturan koneksi Odoo"

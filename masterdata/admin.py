from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Dapur, Jadwal, Toko, TemplateProduk, UserProfile, RO


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    extra = 0


class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "toko", "theme")
    search_fields = ("user__username", "toko__nama_toko")
    list_filter = ("theme", "toko")


@admin.register(RO)
class ROAdmin(admin.ModelAdmin):
    list_display = ("id_ro", "tgl_ro", "toko", "dapur", "jadwal", "produk", "qty_pesan", "status_ro")
    list_filter = ("status_ro", "tgl_ro", "toko", "dapur")
    search_fields = ("toko__nama_toko", "produk__nama_produk")
    readonly_fields = ("dibuat_oleh", "dibuat_pada", "diubah_pada")


admin.site.register([Dapur, Jadwal, Toko, TemplateProduk])

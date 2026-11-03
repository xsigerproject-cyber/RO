from django.urls import path
from . import views
from . import ro_views
from . import admin_views

urlpatterns = [
    path("admin-tools/", admin_views.admin_home, name="admin_home"),
    path("admin-tools/users/", admin_views.user_list, name="admin_user_list"),
    path("admin-tools/users/add/", admin_views.user_create, name="admin_user_create"),
    path("admin-tools/users/<int:user_id>/edit/", admin_views.user_edit, name="admin_user_edit"),
    path("admin-tools/users/<int:user_id>/password/", admin_views.user_password, name="admin_user_password"),
    path("admin-tools/users/<int:user_id>/delete/", admin_views.user_delete, name="admin_user_delete"),
    path("admin-tools/backup/", admin_views.backup_home, name="admin_backup"),
    path("admin-tools/backup/create/", admin_views.backup_create, name="admin_backup_create"),
    path("admin-tools/backup/download/<str:filename>/", admin_views.backup_download, name="admin_backup_download"),
    path("admin-tools/restore/", admin_views.restore_home, name="admin_restore"),
    path("admin-tools/restore/execute/", admin_views.restore_database, name="admin_restore_execute"),
    path("theme/set/", views.set_theme, name="set_theme"),
    path("ro/", ro_views.ro_transaksi, name="ro_transaksi"),
    path("ro/daftar/", ro_views.ro_daftar, name="ro_daftar"),
    path("", views.dashboard, name="dashboard"),
    path("<str:kind>/", views.list_data, name="master_list"),
    path("<str:kind>/add/", views.edit_data, name="master_create"),
    path("<str:kind>/<int:pk>/edit/", views.edit_data, name="master_edit"),
    path("<str:kind>/<int:pk>/delete/", views.delete_data, name="master_delete"),
    path("<str:kind>/import-template/", views.download_import_template, name="download_import_template"),
    path("<str:kind>/export/", views.export_excel, name="export_excel"),
    path("<str:kind>/import/", views.import_excel, name="import_excel"),
]

from django.urls import path
from . import views
from . import ro_views

urlpatterns = [
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

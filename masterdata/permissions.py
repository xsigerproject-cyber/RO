from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
def can_manage(user):
    return user.is_superuser or user.groups.filter(name__in=["Admin Master","Editor Master"]).exists()
def can_delete(user):
    return user.is_superuser or user.groups.filter(name="Admin Master").exists()

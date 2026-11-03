ROLE_ADMIN_TOKO = "Admin Toko"
ROLE_ADMIN_PRODUKSI = "Admin Produksi"
ROLE_ADMINISTRATOR = "Administrator"


def in_group(user, *names):
    return user.is_authenticated and user.groups.filter(name__in=names).exists()


def is_administrator(user):
    return user.is_authenticated and (
        user.is_superuser or in_group(user, ROLE_ADMINISTRATOR)
    )


def is_admin_toko(user):
    return in_group(user, ROLE_ADMIN_TOKO)


def is_admin_produksi(user):
    return in_group(user, ROLE_ADMIN_PRODUKSI)


def can_manage(user):
    return is_administrator(user) or in_group(user, "Admin Master", "Editor Master")


def can_delete(user):
    return is_administrator(user) or in_group(user, "Admin Master")


def can_access_ro(user):
    return is_administrator(user) or is_admin_toko(user) or is_admin_produksi(user)

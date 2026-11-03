from .models import UserProfile
from .permissions import is_administrator


def theme_context(request):
    """Inject current theme ke semua template secara otomatis."""
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {"current_theme": profile.theme}
    return {"current_theme": "light"}


def administrator_context(request):
    return {"is_administrator_user": is_administrator(request.user)}

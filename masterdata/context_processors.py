from .models import UserProfile


def theme_context(request):
    """Inject current theme ke semua template secara otomatis."""
    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        return {"current_theme": profile.theme}
    return {"current_theme": "light"}

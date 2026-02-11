from django.conf import settings

def mapbox_token(request):
    """Expose MAPBOX_TOKEN setting to templates."""
    return {
        'MAPBOX_TOKEN': getattr(settings, 'MAPBOX_TOKEN', '')
    }

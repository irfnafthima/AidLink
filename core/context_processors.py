from .models import Alert

def global_alert_processor(request):
    """
    Makes the latest global alert available to all templates.
    """
    latest_global = Alert.objects.filter(is_global=True).order_by('-created_at').first()
    return {
        'latest_global_alert': latest_global
    }

from .utils import get_unread_notifications_count

def notifications(request):
    """
    Context processor to add unread notifications count to all templates
    """
    context_data = {
        'unread_notifications_count': 0
    }
    
    if request.user.is_authenticated:
        context_data['unread_notifications_count'] = get_unread_notifications_count(request.user)
    
    return context_data

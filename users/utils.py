from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _
from .models import UserNotification
from rolepermissions.roles import assign_role
from rolepermissions.permissions import grant_permission, revoke_permission

def send_notification(recipient, notification_type, title, message, sender=None,
                     related_object_id=None, related_object_type=None, url=None):
    """
    Send a notification to a user

    Args:
        recipient: User object or User ID
        notification_type: Type of notification (from UserNotification.NOTIFICATION_TYPES)
        title: Notification title
        message: Notification message
        sender: User object or User ID (optional)
        related_object_id: ID of related object (optional)
        related_object_type: Type of related object (optional)
        url: URL to redirect to when notification is clicked (optional)

    Returns:
        UserNotification object
    """
    # Convert IDs to User objects if needed
    if isinstance(recipient, int):
        recipient = User.objects.get(id=recipient)

    if sender and isinstance(sender, int):
        try:
            sender = User.objects.get(id=sender)
        except User.DoesNotExist:
            sender = None

    # Create notification
    notification = UserNotification.objects.create(
        recipient=recipient,
        sender=sender,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_id=related_object_id,
        related_object_type=related_object_type,
        url=url
    )

    return notification

def send_notification_to_role(role, notification_type, title, message, sender=None,
                             related_object_id=None, related_object_type=None, url=None):
    """
    Send a notification to all users with a specific role

    Args:
        role: Role name (from Profile.ROLE_CHOICES)
        notification_type: Type of notification (from UserNotification.NOTIFICATION_TYPES)
        title: Notification title
        message: Notification message
        sender: User object or User ID (optional)
        related_object_id: ID of related object (optional)
        related_object_type: Type of related object (optional)
        url: URL to redirect to when notification is clicked (optional)

    Returns:
        List of created UserNotification objects
    """
    from .models import Profile

    # Get all users with the specified role
    users = User.objects.filter(profile__role=role)

    notifications = []
    for user in users:
        notification = send_notification(
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=sender,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            url=url
        )
        notifications.append(notification)

    return notifications

def assign_user_role(user, role_name):
    """
    Assign a role to a user and update their profile

    Args:
        user: User object
        role_name: Role name (from Profile.ROLE_CHOICES)
    """
    # Update the user's profile
    user.profile.role = role_name
    user.profile.save()

    # Assign the role using django-role-permissions
    if role_name == 'admin':
        assign_role(user, 'Admin')
    elif role_name == 'manager':
        assign_role(user, 'Manager')
    elif role_name == 'employee':
        assign_role(user, 'Employee')
    elif role_name == 'viewer':
        assign_role(user, 'Viewer')

    return user

def get_unread_notifications_count(user):
    """
    Get the count of unread notifications for a user

    Args:
        user: User object

    Returns:
        Integer count of unread notifications
    """
    return UserNotification.objects.filter(recipient=user, is_read=False).count()

def mark_all_notifications_as_read(user):
    """
    Mark all notifications for a user as read

    Args:
        user: User object

    Returns:
        Number of notifications marked as read
    """
    notifications = UserNotification.objects.filter(recipient=user, is_read=False)
    count = notifications.count()
    notifications.update(is_read=True)
    return count

def send_notification_to_admins(notification_type, title, message, related_object_id=None,
                               related_object_type=None, url=None):
    """
    Send a notification to all admin users

    Args:
        notification_type: Type of notification (from UserNotification.NOTIFICATION_TYPES)
        title: Notification title
        message: Notification message
        related_object_id: ID of related object (optional)
        related_object_type: Type of related object (optional)
        url: URL to redirect to when notification is clicked (optional)

    Returns:
        List of created UserNotification objects
    """
    from .models import Profile
    from django.contrib.auth.models import User

    # Get all admin users
    admin_users = User.objects.filter(profile__role='admin')

    notifications = []
    for user in admin_users:
        notification = send_notification(
            recipient=user,
            notification_type=notification_type,
            title=title,
            message=message,
            sender=None,
            related_object_id=related_object_id,
            related_object_type=related_object_type,
            url=url
        )
        notifications.append(notification)

    return notifications

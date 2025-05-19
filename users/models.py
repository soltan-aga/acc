from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

class Profile(models.Model):
    ROLE_CHOICES = (
        ('admin', _('مدير النظام')),
        ('manager', _('مدير')),
        ('employee', _('موظف')),
        ('viewer', _('مشاهد')),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(_("الصورة الشخصية"), upload_to='profile_pics/', blank=True, null=True)
    phone = models.CharField(_("رقم الهاتف"), max_length=20, blank=True, null=True)
    address = models.TextField(_("العنوان"), blank=True, null=True)
    role = models.CharField(_("الدور"), max_length=20, choices=ROLE_CHOICES, default='employee')
    email_notifications = models.BooleanField(_("إشعارات البريد الإلكتروني"), default=True)
    browser_notifications = models.BooleanField(_("إشعارات المتصفح"), default=True)

    class Meta:
        verbose_name = _("الملف الشخصي")
        verbose_name_plural = _("الملفات الشخصية")

    def __str__(self):
        return f"{self.user.username} profile"

    def get_role_display_name(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role)

class UserNotification(models.Model):
    NOTIFICATION_TYPES = (
        ('invoice', _('فاتورة جديدة')),
        ('payment', _('دفعة جديدة')),
        ('user', _('مستخدم جديد')),
        ('product', _('منتج جديد')),
        ('contact', _('جهة اتصال جديدة')),
        ('system', _('إشعار نظام')),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')
    notification_type = models.CharField(_("نوع الإشعار"), max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(_("العنوان"), max_length=255)
    message = models.TextField(_("الرسالة"))
    related_object_id = models.PositiveIntegerField(_("معرف الكائن المرتبط"), null=True, blank=True)
    related_object_type = models.CharField(_("نوع الكائن المرتبط"), max_length=50, null=True, blank=True)
    url = models.CharField(_("الرابط"), max_length=255, null=True, blank=True)
    is_read = models.BooleanField(_("مقروءة"), default=False)
    created_at = models.DateTimeField(_("تاريخ الإنشاء"), auto_now_add=True)
    updated_at = models.DateTimeField(_("تاريخ التحديث"), auto_now=True)

    class Meta:
        verbose_name = _("إشعار")
        verbose_name_plural = _("الإشعارات")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.notification_type} - {self.title} - {self.recipient.username}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, created, **kwargs):
    try:
        instance.profile.save()
    except User.profile.RelatedObjectDoesNotExist:
        # إذا لم يكن للمستخدم ملف شخصي، قم بإنشاء واحد
        Profile.objects.create(user=instance)

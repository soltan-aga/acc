from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import EmployeeLoan, Salary

@receiver(post_save, sender=EmployeeLoan)
def handle_employee_loan_save(sender, instance, created, **kwargs):
    """معالجة حفظ سلفة موظف"""
    # إذا كانت السلفة جديدة وتم تحديد الترحيل التلقائي
    if created and getattr(instance, 'auto_post', False):
        instance.post_loan()

@receiver(post_save, sender=Salary)
def handle_salary_save(sender, instance, created, **kwargs):
    """معالجة حفظ راتب موظف"""
    # إذا كان الراتب جديد وتم تحديد الترحيل التلقائي
    if created and getattr(instance, 'auto_post', False):
        instance.post_salary()

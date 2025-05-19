from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView
)
from .models import Profile, UserNotification
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from .utils import send_notification, get_unread_notifications_count, mark_all_notifications_as_read, assign_user_role

def register_view(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')

        if not (username and email and password1 and password2):
            error_message = 'يرجى ملء جميع الحقول المطلوبة'
        elif password1 != password2:
            error_message = 'كلمات المرور غير متطابقة'
        elif len(password1) < 8:
            error_message = 'يجب أن تحتوي كلمة المرور على 8 أحرف على الأقل'
        else:
            try:
                # استخدام UserRegisterForm للتحقق من صحة البيانات
                form = UserRegisterForm({
                    'username': username,
                    'email': email,
                    'password1': password1,
                    'password2': password2
                })

                if form.is_valid():
                    user = form.save()
                    # Assign default role
                    assign_user_role(user, 'employee')
                    # Send notification to admin users
                    admin_users = User.objects.filter(profile__role='admin')
                    for admin in admin_users:
                        send_notification(
                            recipient=admin,
                            notification_type='user',
                            title='مستخدم جديد',
                            message=f'تم تسجيل مستخدم جديد: {user.username}',
                            related_object_id=user.id,
                            related_object_type='User'
                        )
                    login(request, user)
                    messages.success(request, 'تم إنشاء حسابك بنجاح!')
                    return redirect('home')
                else:
                    # استخراج رسائل الخطأ من النموذج
                    for field, errors in form.errors.items():
                        error_message = errors[0]
                        break
            except Exception as e:
                error_message = str(e)

    # استخدام قالب بسيط جدًا إذا كان المستخدم غير مسجل الدخول
    if not request.user.is_authenticated:
        return render(request, 'users/basic_register.html', {'error_message': error_message})
    else:
        form = UserRegisterForm()
        return render(request, 'users/register.html', {'form': form})

def login_view(request):
    error_message = None

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'مرحبًا {username}، تم تسجيل دخولك بنجاح!')
                return redirect('home')
            else:
                error_message = 'اسم المستخدم أو كلمة المرور غير صحيحة'
        else:
            error_message = 'يرجى إدخال اسم المستخدم وكلمة المرور'

    # استخدام قالب بسيط جدًا إذا كان المستخدم غير مسجل الدخول
    if not request.user.is_authenticated:
        return render(request, 'users/basic_login.html', {'error_message': error_message})
    else:
        form = AuthenticationForm()
        return render(request, 'users/login.html', {'form': form})

@login_required
def profile_view(request):
    return render(request, 'users/profile.html')

@login_required
def account_settings_view(request):
    return render(request, 'users/account_settings.html')

@login_required
def update_profile(request):
    if request.method == 'POST':
        # Update user information
        user = request.user
        user.email = request.POST.get('email')
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.save()

        messages.success(request, 'تم تحديث معلوماتك الشخصية بنجاح!')
        return redirect('account_settings')

    return render(request, 'users/account_settings.html')

@login_required
def change_password(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'تم تغيير كلمة المرور بنجاح!')
            return redirect('account_settings')
        else:
            messages.error(request, 'الرجاء تصحيح الأخطاء أدناه.')
    else:
        form = PasswordChangeForm(request.user)

    return render(request, 'users/account_settings.html', {'password_form': form})

@login_required
def update_avatar(request):
    if request.method == 'POST' and request.FILES.get('avatar'):
        # الحصول على ملف الصورة المرفوعة
        avatar_file = request.FILES['avatar']

        # التحقق من نوع الملف (اختياري)
        if not avatar_file.content_type.startswith('image'):
            messages.error(request, 'يرجى تحميل ملف صورة صالح')
            return redirect('account_settings')

        # التحقق من حجم الملف (اختياري، الحد الأقصى 2 ميجابايت)
        if avatar_file.size > 2 * 1024 * 1024:
            messages.error(request, 'حجم الصورة يجب أن يكون أقل من 2 ميجابايت')
            return redirect('account_settings')

        # تحديث الصورة الشخصية للمستخدم
        profile = request.user.profile

        # إذا كان هناك صورة قديمة، قم بحذفها (اختياري)
        if profile.avatar:
            profile.avatar.delete(save=False)

        # حفظ الصورة الجديدة
        profile.avatar = avatar_file
        profile.save()

        messages.success(request, 'تم تحديث صورتك الشخصية بنجاح!')
        return redirect('account_settings')
    elif request.method == 'POST':
        messages.error(request, 'يرجى اختيار صورة للتحميل')

    return redirect('account_settings')

@login_required
def update_preferences(request):
    if request.method == 'POST':
        # Here you would save user preferences
        messages.success(request, 'تم حفظ التفضيلات بنجاح!')
        return redirect('account_settings')

    return render(request, 'users/account_settings.html')

class CustomPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    success_url = reverse_lazy('password_reset_done')

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

# Notification views
@login_required
def notifications_view(request):
    """View to display all notifications for the current user"""
    notifications = UserNotification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = get_unread_notifications_count(request.user)

    return render(request, 'users/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count
    })

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read"""
    notification = get_object_or_404(UserNotification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def mark_all_read(request):
    """Mark all notifications as read for the current user"""
    count = mark_all_notifications_as_read(request.user)
    return JsonResponse({'status': 'success', 'count': count})

@login_required
def get_notifications_count(request):
    """Get the count of unread notifications for the current user"""
    count = get_unread_notifications_count(request.user)
    return JsonResponse({'count': count})

# Role management views
@login_required
def user_list(request):
    """View to display all users (for admins and managers)"""
    # Check if user has admin or manager role
    if request.user.profile.role not in ['admin', 'manager']:
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'users/user_list.html', {'users': users})

@login_required
def change_user_role(request, user_id):
    """Change the role of a user (for admins)"""
    # Check if user has admin role
    if request.user.profile.role != 'admin':
        messages.error(request, 'ليس لديك صلاحية للوصول إلى هذه الصفحة')
        return redirect('home')
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        new_role = request.POST.get('role')

        if new_role in dict(Profile.ROLE_CHOICES).keys():
            # Assign the new role
            assign_user_role(user, new_role)

            # Send notification to the user
            send_notification(
                recipient=user,
                notification_type='system',
                title='تغيير الدور',
                message=f'تم تغيير دورك إلى {dict(Profile.ROLE_CHOICES).get(new_role)}',
                sender=request.user
            )

            messages.success(request, f'تم تغيير دور {user.username} بنجاح')
        else:
            messages.error(request, 'الدور غير صالح')

        return redirect('user_list')

    return HttpResponseForbidden()

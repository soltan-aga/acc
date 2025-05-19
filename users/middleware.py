from django.contrib.auth.models import User
from .models import Profile

class ProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # التحقق من وجود مستخدم مسجل الدخول
        if request.user.is_authenticated:
            try:
                # محاولة الوصول إلى الملف الشخصي
                profile = request.user.profile
            except User.profile.RelatedObjectDoesNotExist:
                # إذا لم يكن للمستخدم ملف شخصي، قم بإنشاء واحد
                Profile.objects.create(user=request.user)
        
        response = self.get_response(request)
        return response

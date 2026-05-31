"""
URL configuration for store_manager project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.core.management import call_command

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('dashboard.urls'))
]

# --- كود التهيئة التلقائية وقاعدة البيانات على السيرفر ---
try:
    # 1. إجبار السيرفر على بناء الجداول الناقصة تلقائياً فوراً
    call_command('migrate', interactive=False)
    
    # 2. إنشاء حسابك الخاص لتسجيل الدخول إذا لم يكن موجوداً
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if not User.objects.filter(username="Ayoub").exists():
        User.objects.create_superuser("Ayoub", "admin@example.com", "mohmoh05dz")
        print("Superuser 'Ayoub' created successfully!")
except Exception as e:
    print(f"Migration error during startup: {e}")
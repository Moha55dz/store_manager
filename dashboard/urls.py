from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('', views.dashboard_home, name='dashboard_home'),
    path('manage-users/', views.manage_users_view, name='manage_users'),
]
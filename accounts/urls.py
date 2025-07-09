from django.urls import path
from django.contrib.auth import views as auth_views
from .views import dashboard, register, logout_view, profile

urlpatterns = [
    path('profile/', profile, name='profile'),
    path('dashboard/', dashboard, name='accounts-dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'), # Register view to be added if it exists
] 
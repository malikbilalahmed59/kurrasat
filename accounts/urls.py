# In your accounts/urls.py
from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup, name='signup'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    path('password-change/', views.change_password, name='password_change'),
    path('logout/', views.logout_view, name='logout'),
]
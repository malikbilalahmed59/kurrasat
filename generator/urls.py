from django.urls import path
from . import views

urlpatterns = [
    path('', views.rfp_form, name='rfp_form'),
    path('generate/', views.generate_rfp, name='generate_rfp'),
    path('download/<str:filename>/', views.download_file, name='download_file'),
]
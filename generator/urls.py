from django.urls import path
from . import views

urlpatterns = [
    path('', views.rfp_form, name='rfp_form'),
    path('generate/', views.generate_rfp, name='generate_rfp'),
    path('download/<str:filename>', views.download_file, name='download_file'),  # Removed trailing slash
    path('success/<int:rfp_id>/', views.success_view, name='success'),  # New success URL
    path('improve/', views.improve_rfp_form, name='improve_rfp_form'),
    path('improve/process/', views.improve_rfp, name='improve_rfp'),
    path('improve/success/<int:rfp_id>/', views.improve_success_view, name='improve_success'),
    path('improve/download/<str:filename>', views.download_improved_file, name='download_improved_file'),

]
from django.urls import path
from . import views

urlpatterns = [
    path('', views.rfp_form, name='rfp_form'),
    path('generate/', views.generate_rfp, name='generate_rfp'),
    path('download/<str:filename>', views.download_file, name='download_file'),
    path('download_by_id/<int:rfp_id>/', views.download_by_id, name='download_by_id'),  # New ID-based download
    path('success/<int:rfp_id>/', views.success_view, name='success'),
    path('improve/', views.improve_rfp_form, name='improve_rfp_form'),
    path('improve/process/', views.improve_rfp, name='improve_rfp'),
    path('improve/success/<int:rfp_id>/', views.improve_success_view, name='improve_success'),
    path('improve/download/<str:filename>', views.download_improved_file, name='download_improved_file'),
    path('improve/download_by_id/<int:rfp_id>/', views.download_improved_by_id, name='download_improved_by_id'),
    # New ID-based download

    # Task status URLs
    path('task/status/<str:task_id>/<str:document_type>/<int:document_id>/', views.task_status, name='task_status'),
    path('task/check/<str:task_id>/<str:document_type>/<int:document_id>/', views.check_task_status,
         name='check_task_status'),
]
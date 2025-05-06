from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_document, name='create'),
    path('development/', views.develop_document, name='development'),
    path('drafts/', views.document_list, name='drafts'),
    path('document/<int:doc_id>/', views.document_detail, name='document_detail'),
    path('document/<int:doc_id>/edit/', views.document_edit, name='document_edit'),
    path('document/<int:doc_id>/delete/', views.document_delete, name='document_delete'),
    path('document/<int:doc_id>/download/', views.document_download, name='document_download'),
]
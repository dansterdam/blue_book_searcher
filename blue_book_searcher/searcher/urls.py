# cases/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.search_view, name='search'),
    path('download-all/', views.download_all_files, name='download_all_files'),
	path('case/<int:id>/', views.case_detail, name='case_detail'),
    path('casefiles/pdfs/<int:pk>/', views.serve_pdf, name='serve_pdf'),
]

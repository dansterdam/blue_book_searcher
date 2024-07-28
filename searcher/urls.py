# cases/urls.py

from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('', views.search_view, name='search'),
	path('case/<int:id>/', views.case_detail, name='case_detail'),
    path('case/<int:id>/casefiles/pdf/<int:pk>/', views.serve_pdf, name='serve_pdf'),
    path('media/casefiles/pdf/<int:pk>/', views.serve_pdf, name='serve_pdf'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

from django.urls import path
from .views import UploadReportView

urlpatterns = [
    path('upload/', UploadReportView.as_view(), name='upload_report'),
]

from django.db import models

class MedicalReport(models.Model):
    patient_name = models.CharField(max_length=255, default="John Doe")
    report_file = models.FileField(upload_to='reports/')
    extracted_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient_name} - {self.created_at}"

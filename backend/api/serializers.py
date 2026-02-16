from rest_framework import serializers
from .models import MedicalReport

class MedicalReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalReport
        fields = '__all__'

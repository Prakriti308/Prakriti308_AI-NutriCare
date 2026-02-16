from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from .serializers import MedicalReportSerializer
from .services import extract_medical_data, generate_diet_plan
import os

class UploadReportView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request, *args, **kwargs):
        file_serializer = MedicalReportSerializer(data=request.data)
        if file_serializer.is_valid():
            report = file_serializer.save()
            
            # Perform AI Extraction & Analysis
            file_path = report.report_file.path
            
            try:
                # 1. Extract Medical Data (Vision + LLM)
                # Returns a FLAT dict with keys: patient_name, age, gender,
                # blood_sugar, cholesterol, bmi, hemoglobin, total_protein,
                # albumin, abnormal_findings
                extracted, full_text = extract_medical_data(file_path)
                
                # 2. Get diet preference from request (default to Balanced)
                diet_type = request.data.get("diet_type", "Balanced")
                
                # 3. Get age from request (default to 25)
                age = int(request.data.get("age", 25))
                
                print(f"[VIEW] Diet Type received: {diet_type}")
                print(f"[VIEW] Age received: {age}")
                print(f"[VIEW] Extracted data keys: {list(extracted.keys())}")
                
                # 4. Generate Diet Plan (LLM) with diet preference and age
                result = generate_diet_plan(extracted, diet_type, age)
                
                # Extract plan and source from hybrid response
                diet_plan = result.get("plan", result)
                plan_source = result.get("source", "Unknown")
                
                # Save extracted data
                report.extracted_data = extracted
                report.save()

                # Construct Response — properly separate patient_info and medical_data
                response_data = {
                    "message": "Report processed successfully",
                    "patient_info": {
                        "name": extracted.get("patient_name", "N/A"),
                        "age": extracted.get("age", str(age)),
                        "gender": extracted.get("gender", "N/A"),
                    },
                    "medical_data": {
                        "blood_sugar": extracted.get("blood_sugar", "N/A"),
                        "cholesterol": extracted.get("cholesterol", "N/A"),
                        "bmi": extracted.get("bmi", "N/A"),
                        "hemoglobin": extracted.get("hemoglobin", "N/A"),
                        "total_protein": extracted.get("total_protein", "N/A"),
                        "albumin": extracted.get("albumin", "N/A"),
                        "abnormal_findings": extracted.get("abnormal_findings", []),
                    },
                    "diet_plan": diet_plan,
                    "plan_source": plan_source,
                    "raw_text_preview": full_text[:500] + "..." if full_text else ""
                }
                return Response(response_data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        else:
            return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

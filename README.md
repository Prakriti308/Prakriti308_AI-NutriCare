# AI-NutriCare: Personalized Diet Plan Generator

## 📌 Project Overview
**AI-NutriCare** is a full-stack application designed to generate personalized diet plans based on medical reports. [cite_start]Unlike generic diet apps, it uses Optical Character Recognition (OCR) and Generative AI to analyze a patient's specific health metrics (blood sugar, cholesterol, BMI) and doctor's notes to create a medically tailored meal plan[cite: 1, 7].

## ⚠️ Problem Statement
Patients often struggle to interpret complex medical reports and translate doctor's advice into daily meal choices. Generic diet plans fail to account for individual medical conditions like Diabetes or Hypertension. [cite_start]This project solves that gap by automating the interpretation of medical data[cite: 4, 5, 6].

## 🎯 Key Features
* [cite_start]**Medical Report Analysis:** Automatically extracts data from PDF or Image reports using OCR[cite: 9, 33].
* [cite_start]**Health Risk Detection:** Identifies abnormal values (e.g., High Glucose, Obesity) using rule-based logic[cite: 10, 36].
* [cite_start]**AI Diet Generation:** Uses Google's Gemini API to create a detailed, day-by-day meal plan based on the extracted health data[cite: 12, 43].
* [cite_start]**Doctor's Note Interpretation:** Translates complex medical jargon into simple, actionable diet advice[cite: 11, 40].

## 🏗️ Tech Stack
* [cite_start]**Frontend:** React.js, Tailwind CSS[cite: 24].
* [cite_start]**Backend:** Python, Django REST Framework[cite: 20].
* [cite_start]**AI & ML:** Google Gemini API (LLM), Tesseract OCR[cite: 22, 23].
* [cite_start]**Database:** SQLite[cite: 25].

## 🚀 How It Works
1.  [cite_start]**Upload:** User uploads a medical report (PDF/Image)[cite: 31].
2.  [cite_start]**Process:** The system reads the text and detects health conditions[cite: 33, 36].
3.  [cite_start]**Generate:** The AI creates a specific Breakfast, Lunch, and Dinner plan[cite: 43].
4.  [cite_start]**Download:** User gets a clean, easy-to-read diet chart[cite: 44].

---
*Created as part of the Infosys Springboard Internship.*
# 🩺 AI-NutriCare — Personalized Diet Plan Generator

AI-NutriCare is a full-stack web application that generates **personalized diet plans** from medical reports. It uses **Groq LLaMA Vision AI** to read uploaded blood-test PDFs or images, extract health metrics, detect abnormalities, and create a medically-tailored meal plan  all in seconds.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-4.2%2B-green?logo=django&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.30%2B-red?logo=streamlit&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-LLaMA_Vision-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Problem Statement

Patients often receive complex medical reports filled with lab values and medical jargon. Translating those numbers into practical, daily meal choices is difficult. Generic diet plans found online ignore individual conditions like diabetes, high cholesterol, or protein deficiency. **AI-NutriCare bridges that gap** by automating report interpretation and generating condition-aware nutrition plans.

---

## 🎯 Key Features

| Feature | Description |
|---|---|
| **AI-Powered OCR** | Extracts text from PDF / image medical reports using Groq LLaMA Vision models (no Tesseract needed) |
| **Health Metric Extraction** | Parses blood sugar, cholesterol, hemoglobin, BMI, total protein, albumin, and abnormal findings |
| **Personalized Diet Plans** | Generates Breakfast, Lunch & Dinner with calorie targets tailored to the patient's conditions |
| **Diet Type Support** | Supports Vegetarian and Non-Vegetarian preferences |
| **Smart Chatbot** | Ask follow-up questions about your diet plan powered by Groq LLaMA |
| **BMI Calculator** | Built-in calculator in the sidebar |
| **Dark / Light Mode** | Toggle between themes |
| **Model Fallback** | Automatically tries multiple AI models if one is unavailable |
| **Template Fallback** | Falls back to curated template diets if AI generation fails |

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Streamlit (Python) |
| **Backend API** | Django REST Framework |
| **AI / LLM** | Groq Cloud — LLaMA 3.3 70B (text), LLaMA 3.2 Vision (OCR) |
| **PDF Rendering** | pypdfium2 (renders PDF pages to images) |
| **Image Processing** | Pillow |
| **Database** | SQLite |
| **Chatbot** | Direct Groq API with context-aware prompting |

---

## 📁 Project Structure

```
AI-NutriCare/
├── backend/                        # Django backend
│   ├── api/                        # REST API app
│   │   ├── ai_utils.py             # Vision OCR — PDF/image → text via Groq
│   │   ├── services.py             # Data extraction + diet generation logic
│   │   ├── views.py                # Upload endpoint
│   │   ├── models.py               # MedicalReport model
│   │   ├── serializers.py          # DRF serializers
│   │   └── urls.py                 # API routes
│   ├── backend_config/             # Django project settings
│   │   ├── settings.py
│   │   └── urls.py
│   ├── media/reports/              # Uploaded report files (gitignored)
│   ├── .env                        # API keys (gitignored)
│   ├── manage.py
│   └── db.sqlite3                  # SQLite database (gitignored)
├── frontend_streamlit/             # Streamlit frontend
│   ├── app.py                      # Main UI application
│   ├── rag_engine.py               # AI chatbot engine (Groq-based)
│   └── .streamlit/config.toml      # Streamlit theme configuration
├── requirements.txt                # Python dependencies
├── .gitignore
└── README.md
```

---

## 🚀 How It Works

```
┌──────────────┐     ┌──────────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Upload PDF  │────▶│  Groq Vision AI  │────▶│  Extract Health │────▶│  Generate    │
│  or Image    │     │  (OCR to Text)   │     │  Metrics & Data │     │  Diet Plan   │
└──────────────┘     └──────────────────┘     └─────────────────┘     └──────┬───────┘
                                                                             │
                                                                             ▼
                                                                    ┌──────────────┐
                                                                    │  Display in  │
                                                                    │  Streamlit   │
                                                                    │  + AI Chat   │
                                                                    └──────────────┘
```

1. **Upload** — User uploads a medical report (PDF or image) via the Streamlit sidebar
2. **OCR** — Backend renders PDF pages as images and sends them to Groq LLaMA Vision for text extraction
3. **Extract** — AI parses the extracted text to identify patient info, lab values (blood sugar, cholesterol, hemoglobin, BMI, etc.), and abnormal findings
4. **Generate** — Based on the extracted data, diet type preference, and age, the AI generates a personalized Breakfast / Lunch / Dinner plan with calorie targets and a doctor's note
5. **Chat** — User can ask follow-up questions about their diet plan using the built-in AI chatbot

---

## ⚙️ Setup & Installation

### Prerequisites

- **Python 3.10+** (3.11 recommended)
- **Groq API Key** — Get one free at [console.groq.com](https://console.groq.com)
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/Prakriti308/AI-NutriCare.git
cd AI-NutriCare
```

### 2. Create a Virtual Environment

**Using conda (recommended):**
```bash
conda create -n nutricare python=3.11 -y
conda activate nutricare
```

**Using venv:**
```bash
# Linux / macOS
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

Create a `.env` file inside the `backend/` directory:

```bash
# Linux / macOS
echo 'GROQ_API_KEY=your_groq_api_key_here' > backend/.env

# Windows (PowerShell)
Set-Content backend\.env 'GROQ_API_KEY=your_groq_api_key_here'
```

Replace `your_groq_api_key_here` with your actual Groq API key.

### 5. Run Database Migrations

```bash
cd backend
python manage.py migrate
```

### 6. Start the Backend Server

```bash
python manage.py runserver
```

The Django API will be available at `http://127.0.0.1:8000`.

### 7. Start the Frontend (new terminal)

```bash
cd frontend_streamlit
streamlit run app.py
```

The Streamlit app will open at `http://localhost:8501`.

---

## 🖥️ Usage

1. Open `http://localhost:8501` in your browser
2. Upload a medical report (PDF or image) using the sidebar
3. Choose your **Diet Type** (Vegetarian / Non-Vegetarian) and enter your **Age**
4. Click **"🔬 Analyze & Generate Plan"**
5. View your personalized meal plan with calorie breakdowns, key vitals, and a doctor's note
6. Use the **Chat with AI** section to ask follow-up questions about your diet

---

## 🔧 Configuration

| Setting | Location | Description |
|---|---|---|
| `GROQ_API_KEY` | `backend/.env` | Your Groq API key (required) |
| Theme | `frontend_streamlit/.streamlit/config.toml` | Streamlit UI theme (dark/light base) |
| `ALLOWED_HOSTS` | `backend/backend_config/settings.py` | Defaults to `['*']` for development |
| `CORS_ALLOW_ALL_ORIGINS` | `backend/backend_config/settings.py` | Set to `True` for development |

---

## 🤖 AI Models Used

| Purpose | Models (in fallback order) |
|---|---|
| **Text Generation** | `llama-3.3-70b-versatile` → `llama3-70b-8192` → `llama-3.1-8b-instant` |
| **Vision OCR** | `llama-3.2-11b-vision-preview` → `llama-3.2-90b-vision-preview` |
| **Chatbot** | `llama-3.3-70b-versatile` → `llama-3.1-8b-instant` |

If a model is rate-limited or unavailable, the system automatically tries the next one in the chain.

---

## 📝 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/upload/` | Upload a medical report and receive a personalized diet plan |

**Request:** `multipart/form-data` with fields:
- `report_file` — PDF or image file
- `diet_type` — `"Vegetarian"` or `"Non-Vegetarian"`
- `age` — Patient age (integer)

**Response:** JSON with `patient_info`, `medical_data`, `diet_plan`, and `plan_source`.

---

## 🐛 Troubleshooting

| Issue | Solution |
|---|---|
| `Cannot connect to the backend` | Make sure Django is running: `cd backend && python manage.py runserver` |
| `GROQ_API_KEY not set` | Create `backend/.env` with your key |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| Template diet instead of AI | Groq API may be rate-limited — wait a moment and retry |
| Port 8000 in use | `python manage.py runserver 8001` (update `API_URL` in `app.py`) |
| Port 8501 in use | `streamlit run app.py --server.port 8502` |

---

## 📄 License

This project is open-source and available under the [MIT License](LICENSE).

---

*Created as part of the Infosys Springboard Internship.*